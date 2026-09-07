from src.services.v1 import *
from src.repository.event import (EventRepository, 
                                  EventParticipantReadRepository, 
                                  EventParticipantWriteRepository)


from src.exception import DatabaseConnectionException
from src.utils import MIN_CONFIDENCE
from src.services.v1 import celery_app
from src.db.database_connection import db as db_module

logger = logging.getLogger(__name__)

# Builds a fresh DB session + repos + service instance for each photo, since this
# runs inside a Celery worker process (separate from the FastAPI request lifecycle)
async def _run_single(user_id, photo_path, event_id):
    async with db_module.AsyncSessionLocal() as session:
        try:
            # Imported here to avoid circular import between event_service and this module
            from src.services.v1.event_service import EventService

            event_repo = EventRepository(db=session)
            ep_read_repo = EventParticipantReadRepository(session)
            ep_write_repo = EventParticipantWriteRepository(db=session, ep_read_repo=ep_read_repo, event_repo=event_repo)

            service = EventService(
                event_repo=event_repo,
                ep_read_repo=ep_read_repo,
                ep_write_repo=ep_write_repo)

            result = await service._upload_single_photo(user_id, photo_path, event_id)

            # Explicit commit needed since this session isn't tied to a request lifecycle
            await session.commit()

            return {
                "status": "success",
                "event_id": str(event_id)
            }
        
        except SQLAlchemyError as e:
            # DB-specific failures get rolled back and wrapped in a domain exception
            await session.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            raise DatabaseConnectionException()
        except Exception:
            # Any other unexpected error still needs a rollback before re-raising
            await session.rollback()
            raise

        
# Celery task wrapper: retries automatically on failure (max 3x, exponential backoff),
# rate-limited to 15/min to avoid overwhelming the face-detection model
@celery_app.task(
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=10,
    rate_limit="15/m"
)
def single_photo_embedding_task(user_id, photo_path, event_id):
    # Runs the async service method inside Celery's synchronous worker environment
    return async_to_sync(_run_single)(user_id, photo_path, event_id)

def dispatch_batch_photo_tasks(user_id, saved_paths: list[str], event_id):
    """
    Fans out one Celery task per photo, runs them in parallel via group().
    """
    # group() lets all photos for this batch be processed concurrently by workers,
    # instead of one-by-one sequentially
    job = group(
        single_photo_embedding_task.s(str(user_id), path, str(event_id))
        for path in saved_paths
    )
    result = job.apply_async()
    return result