import base64
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
import pytest

from src.db.redis_connection import redisconnection 
from src.models.user.register import UserRegister
from src.schemas.v1 import UserCreate
from src.schemas.v1 import UpdateProfilePhoto


async def test_register_user_creates_user_and_profile_photo(
    fake_user_repo, fake_db_session, fake_redis, fake_user_service, mock_generate_embedding
):
    # Redis mein pehle se face daal do (jaisa WebSocket flow real mein karta hai)
    dummy_frame = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy_frame)
    face_b64 = base64.b64encode(buffer).decode("utf-8")

    temp_face_id = "019f9a1a-0699-7f9f-aa57-f34f86b9da99"
    await redisconnection.set_expiration(temp_face_id, face_b64, 300)

    create_data = UserCreate(
        username="Harry12345",
        email_id="test12345@gmail.com",
        password="Hh@123!!!!!",
        gender="Male",
        mobile_number="9999999998",
        temp_face_id=temp_face_id,
    )

    new_user = await fake_user_service.register_user(create_data)

    await fake_db_session.commit()

    assert new_user.user_id is not None
    assert new_user.username == "Harry12345"


async def test_update_profile_photo(
    fake_user_repo, fake_db_session, fake_redis, fake_user_service, mock_generate_embedding
):
    # ---- Step 1: Register a user first ----
    dummy_frame = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy_frame)
    face_b64 = base64.b64encode(buffer).decode("utf-8")

    register_temp_face_id = "019f9a1a-0699-7f9f-aa57-f34f86b9da99"
    await redisconnection.set_expiration(register_temp_face_id, face_b64, 300)

    create_user_data = UserCreate(
        username="Harry12345",
        email_id="test12345@gmail.com",
        password="Hh@123!!!!!",
        gender="Male",
        mobile_number="9999999998",
        temp_face_id=register_temp_face_id,
    )

    new_user = await fake_user_service.register_user(create_user_data)
    await fake_db_session.commit()

    assert new_user.user_id is not None

    # ---- Step 2: Prepare a FRESH temp_face_id for the profile photo update ----
    dummy_frame_2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    _, buffer_2 = cv2.imencode(".jpg", dummy_frame_2)
    face_b64_2 = base64.b64encode(buffer_2).decode("utf-8")

    update_temp_face_id = "029f9a1a-0699-7f9f-aa57-f34f86b9da98"
    await redisconnection.set_expiration(update_temp_face_id, face_b64_2, 300)

    update_user_data = UpdateProfilePhoto(
        temp_face_id=update_temp_face_id
    )

    # ---- Step 3: Use the ACTUAL registered user, not a fake/hardcoded one ----
    current_user = new_user

    await fake_user_service.update_user_profile_photo(update_user_data, current_user=current_user)

    await fake_db_session.commit()

    # ---- Step 4: Verify ----
    photo = await fake_user_repo.get_profile_photo_by_user_id(user_id=current_user.user_id)

    assert photo is not None
    assert photo.user_id == current_user.user_id