# tests/conftest.py
from contextlib import asynccontextmanager
import io
import fakeredis.aioredis as fkredis
import pytest
import pytest_asyncio
import io as io_module

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient 
from PIL import Image

from src.main import app
from src.db import redisconnection
from src.core.config import settings
from src.repository.user import UserRepository
from src.repository.event import EventRepository, EventParticipantReadRepository, EventParticipantWriteRepository
from src.schemas.v1 import UserCreate, EventCreate
from src.services.v1 import UserService, EventService
from src.db import Base  # tumhara SQLAlchemy declarative Base


def make_real_jpeg_bytes(width=50, height=50, color=(255, 0, 0)):
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest_asyncio.fixture
async def fake_db_session():
    # In-memory SQLite, async driver (aiosqlite) ke saath
    engine = create_async_engine(
        str(settings.SQLALCHEMY_TEST_DATABASE_URI),   
        echo=False,
    )

    # Tables create karo isi engine pe (fresh DB har test ke liye)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    # # Cleanup — tables drop karo taaki next test fresh mile
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Cleanup — engine dispose karo
    await engine.dispose()


@pytest_asyncio.fixture
async def fake_user_repo(fake_db_session):
    return UserRepository(fake_db_session)

@pytest_asyncio.fixture
async def fake_event_repo(fake_db_session):
    return EventRepository(fake_db_session)
    
@pytest_asyncio.fixture
async def fake_event_read_repo(fake_db_session):
    return EventParticipantReadRepository(fake_db_session)

@pytest_asyncio.fixture
async def fake_event_write_repo(fake_db_session, fake_event_read_repo, fake_event_repo):
    return EventParticipantWriteRepository(fake_db_session, 
                                           ep_read_repo=fake_event_read_repo, 
                                           event_repo=fake_event_repo)
        
@pytest_asyncio.fixture
async def fake_user_service(fake_user_repo):
    return UserService(user_repo=fake_user_repo, email_service=MagicMock())

@pytest_asyncio.fixture
async def fake_event_service(
    fake_event_repo,
    fake_event_read_repo,
    fake_event_write_repo
):
    return EventService(
        event_repo=fake_event_repo,
        ep_read_repo=fake_event_read_repo,
        ep_write_repo=fake_event_write_repo
    )

@pytest_asyncio.fixture
async def fake_redis():
    fake_client = fkredis.FakeRedis(decode_responses=True)

    redisconnection.redis_client = fake_client

    yield fake_client

    await fake_client.aclose()
    
    redisconnection.redis_client = None 

@pytest_asyncio.fixture
async def mock_retinaface_detect():
    fake_result = {
        "face1" : {
            "score" : 0.99,
            "facial_area" : [50, 50, 300, 300]
        }
    }

    with patch(
        "src.api.v1.endpoints.user.face_capture.RetinaFace.detect_faces",
        return_value = fake_result
    ) as mock_detect:
        yield mock_detect

@pytest.fixture
def test_client():
    return TestClient(app=app)

@pytest_asyncio.fixture
async def mock_generate_embedding():
    with patch(
        "src.services.v1.user_service.embedding_service.generate_embedding",
        new=AsyncMock(return_value=[0.1,0.2,0.3])        
    ) as mock:
        yield mock

@pytest.fixture
def mock_send_otp_email():
    with patch(
        "src.services.v1.user_service.send_email_task.delay"
    ) as mock_delay:
        yield mock_delay


@pytest.fixture
def mock_send_sms_task():
    with patch(
        "src.services.v1.user_service.send_sms_task.delay"
    ) as mock_delay:
        yield mock_delay

@pytest.fixture
def mock_dispatch_celery():
    with patch(
        "src.services.v1.event_service.dispatch_batch_photo_tasks"
    ) as mock:
        yield mock

@pytest.fixture
def mock_single_photo_task():
    with patch(
        "src.services.v1.multiple_face_embed_service.single_photo_embedding_task.delay"
    ) as mock:
        yield mock

@pytest.fixture
def fake_async_session_factory(fake_db_session):
    @asynccontextmanager
    async def _factory():
        yield fake_db_session

    with patch(
        "src.services.v1.multiple_face_embed_service.db_module.AsyncSessionLocal",
        side_effect=_factory
    ) as mock:
        yield mock

@pytest_asyncio.fixture
async def create_test_user(fake_user_repo, fake_db_session):

    create_data = UserCreate(
        username="Harish451",
        email_id="haribhaikassa3@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="9999999999",
        temp_face_id="019f9a1a-0699-7f9f-aa57-f34f86b9da99",
    )

    new_user = await fake_user_repo.add_register_user(
        create_user_data=create_data,
        hashed_password="hashed_dummy_value"
    )
    
    real_img_bytes = make_real_jpeg_bytes()
    
    await fake_user_repo.add_profile_photo(
        new_user,
        filename="test_profile.jpg",
        upload_dir="static",
        img_bytes=real_img_bytes, 
        embedding=[0.1, 0.2, 0.3]
    )

    return new_user

@pytest_asyncio.fixture
async def create_test_user_2(fake_user_repo):
    create_data = UserCreate(
        username="SecondUser999",
        email_id="second_user@gmail.com",
        password="Hh@123!!!!",
        gender="Female",
        mobile_number="8888888888",
        temp_face_id="029f9a1a-0699-7f9f-aa57-f34f86b9da98",
    )
    return await fake_user_repo.add_register_user(
        create_user_data=create_data,
        hashed_password="hashed_dummy_value"
    )

@pytest_asyncio.fixture
async def create_test_user_3(fake_user_repo):
    create_data = UserCreate(
        username="ThirdUser777",
        email_id="third_user@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="7777777777",
        temp_face_id="039f9a1a-0699-7f9f-aa57-f34f86b9da97",
    )
    return await fake_user_repo.add_register_user(
        create_user_data=create_data,
        hashed_password="hashed_dummy_value"
    )

@pytest_asyncio.fixture
async def create_test_event(fake_event_service, create_test_user):

    new_user = create_test_user
    
    create_data = EventCreate(
        event_name="Marriage",
        location="Delhi",
        date="2025-12-12",
        description="Hi hfuhsdfsfhfsdbfsf"
    )

    uploaded_group_photo = MagicMock()
    uploaded_group_photo.filename = "photo.jpg"
    uploaded_group_photo.file = io.BytesIO(b"fake image bytes")
    
    new_event = await fake_event_service.create_event(
        event_create_data=create_data,
        uploaded_group_photo=uploaded_group_photo,
        organizer_id=new_user.user_id
    )

    return new_event


