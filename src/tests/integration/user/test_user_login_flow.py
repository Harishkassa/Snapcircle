import pytest
from src.core import PasswordManager
from src.db.redis_connection import redisconnection
from src.exception import OTPVerificationException
from src.schemas.v1 import LoginRequest
from src.schemas.v1 import UserCreate
from unittest.mock import MagicMock

async def test_user_login_email_otp(
    fake_db_session, fake_redis, fake_user_repo, fake_user_service, mock_send_otp_email
):
    create_data = UserCreate(
        username="Harish451",
        email_id="harrykassa3@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="9999999999",
        temp_face_id="019f9a1a-0699-7f9f-aa57-f34f86b9da99",
    )
    
    real_hashed_password = PasswordManager.hash("Hh@123!!!!")

    new_user = await fake_user_repo.add_register_user(
        create_user_data=create_data,
        hashed_password=real_hashed_password
    )

    login_user = LoginRequest(
        identifier="harrykassa3@gmail.com",
        password="Hh@123!!!!"
    )    

    await fake_user_service.login_user_email_otp(login_user.identifier, login_user.password)

    mock_send_otp_email.assert_called_once()


async def test_user_login_mobile_otp(
    fake_db_session, fake_redis, fake_user_repo, fake_user_service, mock_send_sms_task
):
    create_data = UserCreate(
        username="Harish451",
        email_id="harrykassa3@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="9999999999",
        temp_face_id="019f9a1a-0699-7f9f-aa57-f34f86b9da99",
    )
    
    real_hashed_password = PasswordManager.hash("Hh@123!!!!")

    new_user = await fake_user_repo.add_register_user(
        create_user_data=create_data,
        hashed_password=real_hashed_password
    )

    login_user = LoginRequest(
        identifier="harrykassa3@gmail.com",
        password="Hh@123!!!!"
    )    

    await fake_user_service.login_user_mobile_otp(login_user.identifier, login_user.password)

    mock_send_sms_task.assert_called_once()


async def test_vefrify_top_and_access_key_token_generation(
    fake_db_session, fake_redis, fake_user_repo, fake_user_service      
):
    fake_response = MagicMock()
    otp = "123456"

    create_user_data = UserCreate(
        username="Harish451",
        email_id="harrykassa3@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="9999999999",
        temp_face_id="019f9a1a-0699-7f9f-aa57-f34f86b9da99",
    )
    
    real_hashed_password = PasswordManager.hash("Hh@123!!!!")

    new_user = await fake_user_repo.add_register_user(
        create_user_data=create_user_data,
        hashed_password=real_hashed_password
    )

    await redisconnection.store_otp(new_user.email_id, otp)

    access_token, _ = await fake_user_service.verify_otp_at_login(fake_response, new_user.email_id, otp)
    print(access_token)
    assert access_token is not None
    assert isinstance(access_token, str)

async def test_verify_otp_fails_for_wrong_otp(
    fake_db_session, fake_redis, fake_user_repo, fake_user_service, mocker
):
    fake_response = MagicMock()
    otp = "123456"

    create_user_data = UserCreate(
        username="Harish451",
        email_id="harrykassa3@gmail.com",
        password="Hh@123!!!!",
        gender="Male",
        mobile_number="9999999999",
        temp_face_id="019f9a1a-0699-7f9f-aa57-f34f86b9da99",
    )
    
    real_hashed_password = PasswordManager.hash("Hh@123!!!!")

    new_user = await fake_user_repo.add_register_user(
        create_user_data=create_user_data,
        hashed_password=real_hashed_password
    )

    await redisconnection.store_otp(new_user.email_id, "123456")

    with pytest.raises(OTPVerificationException):   # apni actual exception class daalo (jaise OTPInvalidException)
        await fake_user_service.verify_otp_at_login(fake_response, new_user.email_id, "000000")

