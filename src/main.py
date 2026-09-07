from src import *

from slowapi import _rate_limit_exceeded_handler

# internal imports
from src.api.v1.router import router as v1_router
from src.exception import register_exception_handlers
from src.db import db, Base, redisconnection
from src.core.logger import setup_logging
from src.utils import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    await db.check_connection()

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await redisconnection.connect()

    yield  # app runs while paused here

    # ---- shutdown ----
    await redisconnection.disconnect()
    await db.engine.dispose()

# Initialize FastAPI app
app = FastAPI(title="SnapCircle", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

setup_logging()

register_exception_handlers(app=app)

app.include_router(v1_router, prefix="/api/v1")

# --- Health Check ---

@app.get("/health")
def health_check():
    return {"status": "ok"}
