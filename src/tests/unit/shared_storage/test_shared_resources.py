import io
import pytest

from PIL import Image
from unittest.mock import patch
from fastapi import HTTPException, UploadFile


from src.exception import OTPVerificationException
from src.tests.conftest import fake_db_session, fake_redis
from src.db import redisconnection
from src.core import OtpManager
from src.services.v1 import email_service
from src.utils.file_validator import photos_file_validator
from src.tests.conftest import make_real_jpeg_bytes

async def test_db_session_works(fake_db_session):
    assert fake_db_session is not None

async def test_fake_redis_conn(fake_redis):
    await redisconnection.set_expiration("test123", "hello", 60)
    value = await redisconnection.get_value("temp_face:test123")
    assert value == "hello"
    
async def test_save_otp_with_rate_limit(fake_redis):
    await redisconnection.save_otp_with_rate_limit(email_id="test@gmail.com", new_otp="124587", channel = "email")
    value = await redisconnection.get_value("otp_lock:"+"email:"+"test@gmail.com")
    assert value is not None

async def test_otp_verification_by_email(fake_redis):
    await redisconnection.save_otp_with_rate_limit(email_id="test@gmail.com", new_otp="124587")
    value = await redisconnection.otp_verification_by_email(email="test@gmail.com", otp="124587")
    assert value == True

async def test_otp_verification_by_email(fake_redis):
    await redisconnection.save_otp_with_rate_limit(email_id="test@gmail.com", new_otp="124587")

    with pytest.raises(OTPVerificationException):
        await redisconnection.otp_verification_by_email(email="test@gmail.com", otp="124877")


async def test_valid_jpeg_passes_validation():
    file_bytes = make_real_jpeg_bytes()
    upload_file = UploadFile(filename="test.jpg", file=io.BytesIO(file_bytes))
    upload_file.headers = {"content-type": "image/jpeg"}  

    result = await photos_file_validator._validation_photos_files(upload_file)

    assert result is not None


async def test_invalid_content_type_rejected():
    upload_file = UploadFile(filename="test.txt", file=io.BytesIO(b"not an image"))
    upload_file.headers = {"content-type": "text/plain"}

    with pytest.raises(HTTPException) as exc_info:
        await photos_file_validator._validation_photos_files(upload_file)

    assert exc_info.value.status_code == 400
    assert "Invalid file type" in exc_info.value.detail


async def test_empty_file_rejected():
    upload_file = UploadFile(filename="empty.jpg", file=io.BytesIO(b""))
    upload_file.headers = {"content-type": "image/jpeg"}

    with pytest.raises(HTTPException) as exc_info:
        await photos_file_validator._validation_photos_files(upload_file)

    assert exc_info.value.status_code == 400


async def test_fake_content_type_but_wrong_magic_bytes_rejected():
    """Content-Type header lies (says jpeg), but actual bytes are not a real image."""
    fake_bytes = b"this is not an image, just random text"
    upload_file = UploadFile(filename="fake.jpg", file=io.BytesIO(fake_bytes))
    upload_file.headers = {"content-type": "image/jpeg"}

    with pytest.raises(HTTPException) as exc_info:
        await photos_file_validator._validation_photos_files(upload_file)

    assert "does not match an allowed image type" in exc_info.value.detail


async def test_file_exceeds_max_size_rejected():
    # 6MB ka fake file (MAX_SIZE 5MB hai)
    large_bytes = b"\xff\xd8\xff" + (b"a" * (6 * 1024 * 1024))
    upload_file = UploadFile(filename="large.jpg", file=io.BytesIO(large_bytes))
    upload_file.headers = {"content-type": "image/jpeg"}

    with pytest.raises(HTTPException) as exc_info:
        await photos_file_validator._validation_photos_files(upload_file)

    assert "exceeds 5MB limit" in exc_info.value.detail