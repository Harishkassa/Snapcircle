import io
from unittest.mock import MagicMock

import pytest
import logging
from sqlalchemy.exc import IntegrityError
from uuid6 import uuid7
from src.exception import (
    EventNotFoundException, 
    UserAlreadyExistsException, 
    UserNotFoundException, 
    UserNotFoundException, 
    UnabletoRemovememberException
)
from src.schemas.v1 import EventCreate, UserCreate
from src.schemas.v1.event.update import EventUpdate

async def test_create_event(fake_event_service, fake_user_repo, fake_db_session, create_test_user, create_test_event):
    
    new_event = create_test_event

    assert new_event is not None
    assert new_event.location == "Delhi"
    assert new_event.event_name == "Marriage"
    assert new_event.date.strftime("%Y-%m-%d") == "2025-12-12"

async def test_event_update(fake_event_service, fake_event_repo, fake_db_session, create_test_user, create_test_event):

    new_event = create_test_event

    update_data = EventUpdate(
        new_event_name="Mehandi"
    )
    
    await fake_event_service.update_event_details(new_event.event_id, update_data)
    await fake_db_session.commit()

    event = await fake_event_repo.get_event_by_id(new_event.event_id)

    assert event is not None
    assert event.event_name == "Mehandi"


async def test_delete_event(fake_event_service, fake_event_repo, create_test_event, fake_db_session, mocker, caplog):
    event = create_test_event

    await fake_event_service.delete_event(event_id=event.event_id)
    await fake_db_session.commit()

    # get_event_by_id is @handle_db_errors decorated -> raising EventNotFoundException
    # goes through the decorator's `except CustomBaseException` branch, which rolls back.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(EventNotFoundException):
            await fake_event_repo.get_event_by_id(event_id=event.event_id)
    
    rollback_spy.assert_called_once()
    assert "not found" in caplog.text.lower()

async def test_join_event_success(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session
):
    event = create_test_event
    new_participant = create_test_user_2 

    await fake_event_service.join_event(user_id=new_participant.user_id, code=event.code)
    await fake_db_session.commit()

    participants = await fake_event_service.get_all_participants(event.event_id)

    assert participants is not None
    participant_ids = [p.user_id for p in participants]
    assert new_participant.user_id in participant_ids 


async def test_join_event_fails_for_invalid_code(fake_db_session, fake_event_service, create_test_user_2, mocker):
    # EventNotFoundException originates in event_repo.get_event_by_code (@handle_db_errors) -> rollback fires
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(EventNotFoundException): 
        await fake_event_service.join_event(user_id=create_test_user_2.user_id, code="INVALID_CODE")

    rollback_spy.assert_called_once()


async def test_join_event_fails_if_already_member(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session, mocker, caplog
):
    event = create_test_event
    new_participant = create_test_user_2

    await fake_event_service.join_event(user_id=new_participant.user_id, code=event.code)
    await fake_db_session.commit()

    # UserAlreadyExistsException originates in ep_read_repo.check_participant_exist (@handle_db_errors) -> rollback fires
    rollback_spy = mocker.spy(fake_db_session, "rollback") 

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserAlreadyExistsException):
            await fake_event_service.join_event(user_id=new_participant.user_id, code=event.code)

    rollback_spy.assert_called_once()
    assert "already a participant" in caplog.text.lower()


# ---------- REPO FUNCTION TESTS (simple version) ----------

async def test_repo_add_co_organizer_fails_if_already_an_organizer(
    fake_event_write_repo, create_test_event, fake_db_session, mocker, caplog
):
    event = create_test_event

    # add_co_organizer (repo, @handle_db_errors) raises UserAlreadyExistsException directly -> rollback fires
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserAlreadyExistsException):
            await fake_event_write_repo.add_co_organizer(user_id=event.organizer_id, event_id=event.event_id)

    rollback_spy.assert_called_once()
    assert "already the organizer" in caplog.text.lower()

# ---------- SERVICE FUNCTION TESTS (detailed version) ----------

async def test_service_add_co_organizer_fails_if_not_member(
    fake_db_session, fake_event_service, create_test_event, create_test_user_2, mocker
):
    event = create_test_event
    user = create_test_user_2   # Haven't joined the event yet

    # UserNotFoundException raised inside ep_write_repo.add_co_organizer (@handle_db_errors) -> rollback fires
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(UserNotFoundException):
        await fake_event_service.add_co_organizer(event_id=event.event_id, user_id=user.user_id)

    rollback_spy.assert_called_once()

async def test_service_add_co_organizer_success_for_member(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session
):
    event = create_test_event
    user = create_test_user_2

    # Pehle participant banao
    await fake_event_service.join_event(user_id=user.user_id, code=event.code)
    await fake_db_session.commit()

    # Ab co-organizer banao
    await fake_event_service.add_co_organizer(event_id=event.event_id, user_id=user.user_id)
    await fake_db_session.commit()

    # Verify — organizer check se confirm karo
    organizer = await fake_event_service.ep_read_repo.get_co_organizer_of_event_by_id(
        event_id=event.event_id
    )
    co_organizers = [org for org in organizer]
    assert co_organizers is not None


async def test_service_add_co_organizer_if_co_org_already_exist(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session, mocker,caplog
):
    
    event = create_test_event
    user = create_test_user_2

    await fake_event_service.join_event(user_id=user.user_id, code=event.code)
    await fake_db_session.commit()

    await fake_event_service.add_co_organizer(event_id=event.event_id, user_id=user.user_id)
    await fake_db_session.commit()

    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserAlreadyExistsException):
            await fake_event_service.add_co_organizer(event_id=event.event_id, user_id=user.user_id)

    rollback_spy.assert_not_called()
    assert "already a co-organizer" in caplog.text.lower()


async def test_remove_member_success(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session
):
    event = create_test_event
    participant = create_test_user_2

    # Member ko pehle event join karwao
    await fake_event_service.join_event(user_id=participant.user_id, code=event.code)
    await fake_db_session.commit()

    # Organizer (event ka creator) member ko remove kare
    await fake_event_service.remove_participant_by_organizer_and_co_org(
        user_id=event.organizer_id,
        event_id=event.event_id,
        participant_id=participant.user_id
    )
    await fake_db_session.commit()

    # Verify member hat gaya
    removed = await fake_event_service.ep_read_repo.get_event_participant_by_id(
        participant_id=participant.user_id, event_id=event.event_id
    )
    assert removed is None


async def test_remove_member_fails_if_caller_not_organizer_or_co_organizer(
    fake_event_service, create_test_event, create_test_user_2, create_test_user_3, fake_db_session, mocker, caplog
):
    event = create_test_event
    participant = create_test_user_2
    random_user = create_test_user_3   # na organizer, na co-organizer

    await fake_event_service.join_event(user_id=participant.user_id, code=event.code)
    await fake_db_session.commit()

    # UnabletoRemovememberException raised in service's check_eligibility (service layer,
    # not @handle_db_errors, no prior db.add()) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UnabletoRemovememberException):
            await fake_event_service.remove_participant_by_organizer_and_co_org(
                user_id=random_user.user_id,
                event_id=event.event_id,
                participant_id=participant.user_id
            )

    rollback_spy.assert_not_called()
    assert "not organizer/co-organizer" in caplog.text.lower()

async def test_remove_member_fails_if_member_not_found(
    fake_db_session, fake_event_service, create_test_event, create_test_user_2, mocker
):
    event = create_test_event
    non_participant = create_test_user_2   # kabhi join hi nahi kiya

    # Raised directly in event_service.remove_participant_by_organizer_and_co_org (service layer) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(UserNotFoundException):
        await fake_event_service.remove_participant_by_organizer_and_co_org(
            user_id=event.organizer_id,
            event_id=event.event_id,
            participant_id=non_participant.user_id
        )

    rollback_spy.assert_not_called()

async def test_remove_member_fails_if_target_is_organizer(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session, mocker
):
    event = create_test_event
    co_organizer = create_test_user_2

    # co_organizer ko member banaake co-organizer bana do
    await fake_event_service.join_event(user_id=co_organizer.user_id, code=event.code)
    await fake_db_session.commit()

    await fake_event_service.add_co_organizer(user_id=co_organizer.user_id, event_id=event.event_id)
    await fake_db_session.commit()

    # Raised directly in event_service.remove_participant_by_organizer_and_co_org (service layer) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    # Ab organizer khud is co-organizer ko remove karne ki koshish kare — fail hona chahiye
    with pytest.raises(UnabletoRemovememberException):
        await fake_event_service.remove_participant_by_organizer_and_co_org(
            user_id=event.organizer_id,
            event_id=event.event_id,
            participant_id=co_organizer.user_id
        )

    rollback_spy.assert_not_called()

async def test_remove_co_organizer_success(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session
):
    event = create_test_event
    co_organizer = create_test_user_2

    # Member banao, phir co-organizer banao
    await fake_event_service.join_event(user_id=co_organizer.user_id, code=event.code)
    await fake_db_session.commit()

    await fake_event_service.add_co_organizer(user_id=co_organizer.user_id, event_id=event.event_id)
    await fake_db_session.commit()

    # Organizer, co-organizer ko remove kare
    await fake_event_service.remove_co_organizer(
        user_id=event.organizer_id,
        event_id=event.event_id,
        co_organizer_id=co_organizer.user_id
    )
    await fake_db_session.commit()

    # Verify co-organizer hat gaya
    removed = await fake_event_service.ep_read_repo.get_event_co_organizer(
        event_id=event.event_id, user_id=co_organizer.user_id
    )
    assert removed is None


async def test_remove_co_organizer_fails_if_caller_not_authorized(
    fake_event_service, create_test_event, create_test_user_2, create_test_user_3, fake_db_session, mocker, caplog
):
    event = create_test_event
    co_organizer = create_test_user_2
    random_user = create_test_user_3

    await fake_event_service.join_event(user_id=co_organizer.user_id, code=event.code)
    await fake_db_session.commit()
    await fake_event_service.add_co_organizer(user_id=co_organizer.user_id, event_id=event.event_id)
    await fake_db_session.commit()

    # Raised in service's check_eligibility (service layer, not @handle_db_errors) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UnabletoRemovememberException):
            await fake_event_service.remove_co_organizer(
                user_id=random_user.user_id,   # na organizer, na co-organizer
                event_id=event.event_id,
                co_organizer_id=co_organizer.user_id
            )

    rollback_spy.assert_not_called()
    assert "not organizer/co-organizer" in caplog.text.lower()


async def test_remove_co_organizer_fails_if_target_not_a_co_organizer(
    fake_db_session, fake_event_service, create_test_event, create_test_user_2, mocker, caplog
):
    
    event = create_test_event
    not_co_organizer = create_test_user_2   # kabhi co-organizer bana hi nahi

    # UserNotFoundException raised inside ep_write_repo.remove_co_organizer (@handle_db_errors) -> rollback fires
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UserNotFoundException):
            await fake_event_service.remove_co_organizer(
                user_id=event.organizer_id,
                event_id=event.event_id,
                co_organizer_id=not_co_organizer.user_id
            )

    rollback_spy.assert_called_once()
    assert "no co-organizer" in caplog.text.lower()


async def test_remove_organizer_by_self_success(
    fake_event_service, create_test_event, fake_db_session
):
    
    event = create_test_event

    await fake_event_service.remove_organizer_by_self(
        user_id=event.organizer_id,
        event_id=event.event_id
    )
    await fake_db_session.commit()

    # Verify organizer_id NULL ho gaya
    updated_event = await fake_event_service.event_repo.get_event_by_id(event_id=event.event_id)
    assert updated_event.organizer_id is None


async def test_remove_organizer_fails_if_user_not_event_member(
    fake_db_session, fake_event_service, create_test_event, create_test_user_2, mocker
):
    event = create_test_event
    random_user = create_test_user_2   # kabhi member/organizer nahi tha

    # Raised directly in event_service.remove_organizer_by_self (service layer) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(UserNotFoundException):
        await fake_event_service.remove_organizer_by_self(
            user_id=random_user.user_id,
            event_id=event.event_id
        )

    rollback_spy.assert_not_called()


async def test_remove_organizer_fails_if_member_but_not_organizer(
    fake_event_service, create_test_event, create_test_user_2, fake_db_session, mocker
):
    event = create_test_event
    participant = create_test_user_2

    # Member hai, but organizer nahi
    await fake_event_service.join_event(user_id=participant.user_id, code=event.code)
    await fake_db_session.commit()

    # Raised directly in event_service.remove_organizer_by_self (service layer) -> no rollback expected.
    rollback_spy = mocker.spy(fake_db_session, "rollback")

    with pytest.raises(UserNotFoundException):
        await fake_event_service.remove_organizer_by_self(
            user_id=participant.user_id,
            event_id=event.event_id
        )
    
    rollback_spy.assert_not_called()

