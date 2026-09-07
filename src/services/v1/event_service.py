from src.services.v1 import *

# internal imports
from src.models import Event, EventParticipant
from src.repository.event import (EventRepository,
                                  EventParticipantReadRepository,
                                  EventParticipantWriteRepository)
from src.exception import (
    DatabaseConnectionException, 
    EventNotFoundException,
    UserNotFoundException,
    UserAlreadyExistsException,
    CustomBaseException,
    UnabletoRemovememberException
)
from src.models import (
    Event, 
    GroupPhoto, 
    EventParticipant, 
)
from src.utils import GenerateEventCode, MIN_CONFIDENCE, MATCH_THRESHOLD, find_best_match

from src.services.v1.face_service import crop_face
from src.services.v1.multiple_face_embed_service import dispatch_batch_photo_tasks

logger = logging.getLogger(__name__)

class EventService:

    def __init__(self, 
                 event_repo : EventRepository,
                 ep_read_repo : EventParticipantReadRepository, 
                 ep_write_repo : EventParticipantWriteRepository):

        self.event_repo = event_repo
        self.ep_read_repo = ep_read_repo
        self.ep_write_repo = ep_write_repo

        
    async def create_event(self, event_create_data, uploaded_group_photo, organizer_id: UUID) -> Event:

        self.upload_dir = "group_photo"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        try:

            # Retry loop: event_code is generated randomly, so retry a few times on collision
            for attempt in range(5):
                try:
                    async with self.event_repo.db.begin_nested():
                        event_code = GenerateEventCode.generate_event_code()

                        new_event = await self.event_repo.create_event(
                            create_event_data=event_create_data, 
                            event_code=event_code, 
                            organizer_id=organizer_id
                            )

                    break
                except IntegrityError:
                    # Unique constraint on event_code violated — try a new code
                    continue
            else:
                # Loop exhausted without breaking = all 5 attempts collided
                raise DatabaseConnectionException("Could not generate a unique event code")

            # Save the uploaded group photo to disk, named after the event's unique code
            _, ext = os.path.splitext(uploaded_group_photo.filename)
            unique_filename = f"{new_event.code}{ext}"
            file_path = os.path.join(self.upload_dir, unique_filename)

            with open(file_path, "wb") as buffer:
                await asyncio.to_thread(shutil.copyfileobj, uploaded_group_photo.file, buffer)      

            photo_url=f"/{self.upload_dir}/{os.path.basename(file_path)}"

            new_group_photo = await self.event_repo.add_group_photo(photo_url=photo_url, new_event=new_event)
            
            # Organizer is automatically added as the first participant of their own event
            await self.ep_write_repo.add_event_participant(user_id=new_event.organizer_id, event=new_event)
            
            logger.info(f"Group Photo {new_group_photo.group_photo_id} added")
            logger.info(f"Event {new_event.event_id} created with organizer as participant")
            return new_event

        except CustomBaseException:
            # Rollback DB changes and clean up any file already written to disk
            await self.event_repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise
        except Exception as e:
            # Same cleanup for unexpected errors, wrapped into a consistent exception type
            await self.event_repo.db.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Error in add_event service: {str(e)}", exc_info=True)
            raise DatabaseConnectionException(f"Database error: {str(e)}") from e
        
    async def get_all_events(self, skip : int = 0, limit : int = 100 ) -> list["Event"]:
        return await self.event_repo.get_all(skip=skip, limit=limit)

    async def get_event_by_id(self, event_id : UUID) -> "Event":
        event = await self.event_repo.get_event_by_id(event_id)
        return event
    
    async def get_event_by_name(self, event_name : str, user_id : UUID) -> "Event":
        return await self.event_repo.get_event_by_name(event_name, user_id)
    
    async def update_event_details(self, event_id : UUID, event_update) -> "Event":
        event = await self.event_repo.get_event_by_id(event_id)
        await self.event_repo.update_event(
            event=event,
            new_event_name=event_update.new_event_name, 
            new_description=event_update.new_description)
        
    async def delete_event(self, event_id : UUID) -> None:
        event = await self.event_repo.get_event_by_id(event_id=event_id)
        await self.event_repo.delete_event(event=event)

    # Shared authorization check: confirms the user is either the organizer or a co-organizer
    async def check_eligibility(self, event_id: UUID, user_id: UUID):

        event = await self.event_repo.get_event_by_id(event_id=event_id)
        co_org_id = await self.ep_read_repo.get_co_organizer_of_event_by_id(event_id=event_id)

        organizer_id = event.organizer_id
        co_organizer_ids = [ids for ids in co_org_id] if co_org_id else []

        if organizer_id != user_id and user_id not in co_organizer_ids:
                logger.warning(f"User {user_id} is not organizer/co-organizer of event {event_id}, cannot manage members")
                raise UnabletoRemovememberException("You are not able to remove users.")
        
        return event, co_organizer_ids

    # Removes a regular participant; organizer/co-organizer initiating this action is validated first
    async def remove_participant_by_organizer_and_co_org(self, user_id : UUID, event_id : UUID, participant_id : UUID):
        
        event, co_organizer_ids = await self.check_eligibility(event_id=event_id, user_id=user_id)

        event_participant = await self.ep_read_repo.get_event_participant_by_id(participant_id=participant_id, event_id=event_id)

        if not event_participant:
            logger.warning(f"Participant {participant_id} not found in event {event_id}")
            raise UserNotFoundException(f"Participant Not Found in Event")
            
        # Organizers/co-organizers can't be removed through this participant-removal path
        if participant_id == event.organizer_id or participant_id in co_organizer_ids:
            logger.warning(f"Participant {participant_id} is an organizer/co-organizer of event {event_id}, cannot be removed this way")
            raise UnabletoRemovememberException("Cannot remove an organizer or co-organizer")

        await self.ep_write_repo.remove_event_participant(event_participant=event_participant)
        logger.info(f"Successfully Removed the Participat")

    # Removes a co-organizer; caller must be the main organizer or another co-organizer
    async def remove_co_organizer(self, user_id : UUID, event_id : UUID, co_organizer_id : UUID):
        
        _, _ = await self.check_eligibility(event_id=event_id, user_id=user_id)

        await self.ep_write_repo.remove_co_organizer(event_id=event_id, user_id=co_organizer_id)
    
    # Lets the main organizer voluntarily step down and leave the event entirely
    async def remove_organizer_by_self(self, user_id : UUID, event_id : UUID):
        
        event_organizer = await self.ep_read_repo.get_organizer_of_event_by_id(event_id=event_id, user_id=user_id)

        event_participant = await self.ep_read_repo.get_event_participant_by_id(participant_id=user_id,
                                                                  event_id=event_id)
        
        if event_participant is None:
            logger.warning(f"User {user_id} is not a participant of event {event_id}")
            raise UserNotFoundException(f"There is no any participant in event, you entered wrong id please try again.")
        
        if event_participant and event_organizer is None:
            logger.warning(f"User {user_id} is not the organizer of event {event_id}, cannot self-remove as organizer")
            raise UserNotFoundException(f"You are not event Organizer, Unable to remove")
        
        # Removing organizer means removing both their participant record and organizer role
        await self.ep_write_repo.remove_event_participant(event_participant=event_participant)
        
        await self.ep_write_repo.remove_event_organizer(event_id=event_id)

        
    # Promotes an existing participant to co-organizer
    async def add_co_organizer(self, event_id: UUID, user_id: UUID):
        
        existing = await self.ep_read_repo.get_event_co_organizer(event_id=event_id, user_id=user_id)

        if existing:
            logger.warning(f"User {user_id} is already a co-organizer of event {event_id}")
            raise UserAlreadyExistsException("Already a co organizer")
                
        await self.ep_write_repo.add_co_organizer(user_id=user_id, event_id=event_id)

    # Joins an event using its unique event code; fails if user already joined
    async def join_event(self, user_id : UUID, code : str):

        event = await self.event_repo.get_event_by_code(code=code)
        await self.ep_read_repo.check_participant_exist(event_id=event.event_id, user_id=user_id)

        await self.ep_write_repo.add_event_participant(user_id=user_id, event=event)

    async def get_joined_events(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list["EventParticipant"]:
    
        return await self.ep_read_repo.get_joined_events(user_id=user_id)
    
    async def get_all_participants(self, event_id: UUID, skip: int = 0, limit: int = 100):
    
        return await self.ep_read_repo.get_all_participants(event_id=event_id, skip=skip, limit=limit)
        
    # Persists a single uploaded event photo record to the DB
    async def insert_event_photo(self, event_id, user_id, photo_url, photo_type):

        photo_record = await self.event_repo.insert_event_photo(
            event_id=event_id,
            user_id=user_id,
            photo_url=photo_url,
            photo_type=photo_type
        )

        return photo_record
    
    # Persists a face detected+matched in a photo, along with its embedding
    async def insert_detected_face(self, event_photo_id, embedding, matched_user_id):

        await self.event_repo.insert_detected_face(
            event_photo_id=event_photo_id,
            embedding=embedding,
            matched_user_id=matched_user_id
        )

    # Runs RetinaFace detection on an image and filters by confidence threshold
    async def _detect_all_faces(self, img, min_confidence: float = MIN_CONFIDENCE):

        # Offload CPU-bound detection to a threadpool so it doesn't block the event loop
        detections = await run_in_threadpool(RetinaFace.detect_faces, img)
        if not detections:
            return []

        faces = []
        for key, face_data in detections.items():
            if face_data["score"] >= min_confidence:
                faces.append({
                    "facial_area": face_data["facial_area"],  # [x1, y1, x2, y2]
                    "score": face_data["score"],
                })

        return faces
        
    
    async def _upload_single_photo(self, user_id: UUID, file_path: str, event_id: UUID):
        """
        Processes ONE photo: detect faces, generate embeddings, match, save to DB.
        Called once per photo by the Celery task.
        """
        # Pull all known face embeddings for this event to match against
        candidates = await self.event_repo.get_all_embeddings_for_event(event_id)

        photo_type = file_path.split(".")[-1].lower()

        photo_record = await self.insert_event_photo(
            event_id=event_id,
            user_id=user_id,
            photo_url=file_path,
            photo_type=photo_type
        )

        img = cv2.imread(file_path)

        faces = await self._detect_all_faces(img, MIN_CONFIDENCE)

        # Draw bounding boxes on the image for every detected face (debug/visual aid)
        if isinstance(faces, list):
            for face_data in faces:
                x1, y1, x2, y2 = face_data["facial_area"]
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # For each detected face: crop -> embed -> match against known participants -> save result
        for face in faces:
            cropped = crop_face(img, face["facial_area"])
            embedding = await embedding_service.generate_embedding(cropped)

            if embedding is None:
                # Embedding generation failed for this face — skip it, don't fail the whole photo
                continue

            matched_user_id = find_best_match(embedding, candidates, threshold=MATCH_THRESHOLD)

            await self.insert_detected_face(
                event_photo_id=photo_record.event_photo_id,
                embedding=embedding,
                matched_user_id=matched_user_id
            )

        logger.info(f"Photo processed with embedding: {file_path}")
        

    # Saves all uploaded photos to disk, then dispatches async processing (face detection/matching) via Celery
    async def upload_multi_event_photos(self, user_id, uploaded_event_photos, event_id):

        _, _ = await self.check_eligibility(event_id=event_id, user_id=user_id)

        saved_paths = []

        for idx, file in enumerate(uploaded_event_photos, 1):
            img_bytes = await file.read()
            unique_filename = f"{uuid6.uuid7()}_{file.filename}"

            upload_dir = "static/albums"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            photo_url = os.path.join(upload_dir, unique_filename)

            with open(photo_url, "wb") as f:
                f.write(img_bytes)

            saved_paths.append(photo_url)

        # Import here to avoid circular import
        # Heavy lifting (detection/embedding/matching) happens asynchronously in Celery workers
        dispatch_batch_photo_tasks(str(user_id), saved_paths, str(event_id))

        return {"message": "Successfully Uploaded the photos"}