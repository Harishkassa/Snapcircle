from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from fastapi import HTTPException
import pytest
import logging
from uuid6 import uuid7
from unittest.mock import MagicMock
from src.core.security import JWTManager
from src.exception import (
    UserAlreadyExistsException, 
    UserNotFoundException, 
    MissingRefreshToken, 
    InvalidRefreshToken,
    ExpiredRefreshToken)

from src.models import UserRegister
from src.schemas.v1 import UserCreate
from src.db import redisconnection
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy import text

async def test_create_user(fake_user_repo, create_test_user):

    new_user = create_test_user
    
    assert new_user.user_id is not None          # DB ne auto ID diya
    assert new_user.email_id == "haribhaikassa3@gmail.com"
    assert new_user.username == "Harish451"
    assert new_user.password == "hashed_dummy_value"   

async def test_update_pwd(fake_user_repo, create_test_user, create_test_user_2):

    new_user = create_test_user

    await fake_user_repo.password_update(new_user, "Harry@123!!!!")
    
    # for wrong user_id fetch
    # with pytest.raises(UserNotFoundException):
    #     user = await fake_user_repo.get_by_id(uuid7())
    
    user = await fake_user_repo.get_by_id(new_user.user_id)

    assert user.password is not None

# async def test_logout_blacklists_token(fake_redis, fake_user_service):
    
#     fake_response = MagicMock()
#     token = "dummy.jwt.token"
#     refresh_token = "some.raw.refresh.token"
    
#     await fake_user_service.log_out(fake_response, token, refresh_token)

#     # Verify token blacklist mein save hua
#     is_blacklisted = await redisconnection.is_token_blacklisted(token)

#     assert is_blacklisted is True

async def test_logout_blacklists_token(
    fake_redis, fake_user_service, fake_user_repo, create_test_user
):
    new_user = create_test_user
    
    fake_response = MagicMock()
    token = "dummy.jwt.token"

    # 1. Issue a real refresh token first (this is what login would normally do)
    raw_refresh_token = await fake_user_repo.issue_refresh_token(new_user.user_id)

    # 2. Now log out using that same raw refresh token
    await fake_user_service.log_out(
        fake_response,
        token,
        refresh_token=raw_refresh_token
    )

    # 3. Assert access token got blacklisted
    is_blacklisted = await redisconnection.is_token_blacklisted(token)
    assert is_blacklisted is True

    # 4. Assert refresh token family got revoked
    token_hash = JWTManager.hash_token(raw_refresh_token)
    record = await fake_user_repo.get_refresh_token_by_hash(token_hash=token_hash)
    assert record.revoked is True

async def test_update_username_duplicate(fake_db_session, fake_user_repo, create_test_user, create_test_user_2, mocker):
    new_user = create_test_user
    random_user = create_test_user_2

    rollback_spy = mocker.spy(fake_db_session, "rollback")  # patch nahi, spy — real rollback bhi chalega

    with pytest.raises(UserAlreadyExistsException):
        await fake_user_repo.update_username(new_user, random_user.username)

    rollback_spy.assert_called_once()

async def test_session_active_after_error(fake_db_session, fake_user_repo, create_test_user, create_test_user_2, mocker):
    new_user = create_test_user
    random_user = create_test_user_2

    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(UserAlreadyExistsException):
        await fake_user_repo.update_username(new_user, random_user.username)

    # Check 1: is_active flag
    print("Session active:", fake_db_session.is_active)  # False agar failed-transaction state mein hai

    # Check 2: dummy query — real proof

    try:
        await fake_db_session.execute(text("SELECT 1"))
        print("Session usable — no pending rollback")
    except PendingRollbackError:
        print("PendingRollbackError — session is dirty, needs rollback")

    rollback_spy.assert_called_once()


async def test_logs_warning_on_duplicate(fake_db_session, fake_user_repo, create_test_user, create_test_user_2, caplog):
    new_user = create_test_user
    random_user = create_test_user_2

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserAlreadyExistsException):
            await fake_user_repo.update_username(new_user, random_user.username)

    print("logger warning", caplog.text)
    assert "username" in caplog.text.lower()


async def test_refresh_missing_token_raises_401(fake_user_service):
    fake_response = MagicMock()

    with pytest.raises(MissingRefreshToken):
        await fake_user_service.refresh(fake_response, refresh_token=None)

async def test_refresh_invalid_token_raises_401(fake_user_service):
    fake_response = MagicMock()

    with pytest.raises(InvalidRefreshToken):
        await fake_user_service.refresh(fake_response, refresh_token="not-a-real-token")


async def test_refresh_reused_token_revokes_family_and_raises(
    fake_user_service, fake_user_repo, create_test_user
):
    
    new_user = create_test_user
    fake_response = MagicMock()

    # Issue a real token, then simulate it already being used/rotated
    raw_refresh_token = await fake_user_repo.issue_refresh_token(new_user.user_id)
    token_hash = JWTManager.hash_token(raw_refresh_token)
    record = await fake_user_repo.get_refresh_token_by_hash(token_hash=token_hash)
    record.revoked = True   # simulate prior rotation

    with pytest.raises(HTTPException):
        await fake_user_service.refresh(fake_response, refresh_token=raw_refresh_token)

    # Assert entire family got revoked
    family_tokens = await fake_user_repo.get_all_by_family(family_id=record.family_id)  # add helper if needed
    assert all(t.revoked for t in family_tokens)

async def test_refresh_expired_token_raises_401(
    fake_user_service, fake_user_repo, create_test_user
):
    
    new_user = create_test_user
    fake_response = MagicMock()

    raw_refresh_token = await fake_user_repo.issue_refresh_token(new_user.user_id)
    token_hash = JWTManager.hash_token(raw_refresh_token)
    record = await fake_user_repo.get_refresh_token_by_hash(token_hash=token_hash)
    record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # force expiry

    with pytest.raises(ExpiredRefreshToken):
        await fake_user_service.refresh(fake_response, refresh_token=raw_refresh_token)


async def test_refresh_success_rotates_token_and_returns_access_token(
    fake_user_service, fake_user_repo, create_test_user
):
    
    new_user = create_test_user
    fake_response = MagicMock()

    raw_refresh_token = await fake_user_repo.issue_refresh_token(new_user.user_id)
    old_hash = JWTManager.hash_token(raw_refresh_token)
    old_record = await fake_user_repo.get_refresh_token_by_hash(token_hash=old_hash)
    old_family_id = old_record.family_id

    new_access_token, user = await fake_user_service.refresh(
        fake_response, refresh_token=raw_refresh_token
    )

    # Access token returned correctly
    assert new_access_token is not None
    assert isinstance(new_access_token, str)
    assert user.user_id == new_user.user_id

    # Old token marked revoked
    old_record_after = await fake_user_repo.get_refresh_token_by_hash(token_hash=old_hash)
    assert old_record_after.revoked is True

    # New cookie was set
    fake_response.set_cookie.assert_called_once()  # or match set_refresh_cookie's exact call