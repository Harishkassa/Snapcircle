import io
import os
import cv2
from fastapi import UploadFile
import numpy as np

from unittest.mock import MagicMock, AsyncMock
from PIL import Image

from src.services.v1.multiple_face_embed_service import _run_single

def make_fake_image_bytes(width=100, height=100, color=(255, 0, 0)):
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()

async def test_upload_multi_event_photos_dispatches_celery_task(
    fake_event_service, create_test_event, create_test_user, mock_dispatch_celery
):
    event = create_test_event
    user = create_test_user

    uploaded_photos = [
        UploadFile(filename=f"image_{i}.jpg", file=io.BytesIO(make_fake_image_bytes()))
        for i in range(3)
    ]

    result = await fake_event_service.upload_multi_event_photos(
        user.user_id, uploaded_photos, event.event_id
    )

    assert result == {"message": "Successfully Uploaded the photos"}
    mock_dispatch_celery.assert_called_once()

    call_args = mock_dispatch_celery.call_args[0]
    assert call_args[0] == str(user.user_id)
    assert len(call_args[1]) == 3
    assert call_args[2] == str(event.event_id)


async def test_run_single_processes_photo(
    fake_event_repo, fake_user_repo, create_test_event, create_test_user,
    mock_generate_embedding, mock_retinaface_detect, fake_async_session_factory
):
    user = create_test_user
    event = create_test_event

    photo_bytes = make_fake_image_bytes()
    test_photo_path = "static/albums/test_photo.jpg"
    os.makedirs("static/albums", exist_ok=True)
    with open(test_photo_path, "wb") as f:
        f.write(photo_bytes)

    result = await _run_single(str(user.user_id), test_photo_path, str(event.event_id))

    assert result["status"] == "success"
    mock_retinaface_detect.assert_called()
    mock_generate_embedding.assert_called()

    photos = await fake_event_repo.get_event_photos_by_event_id(event.event_id)
    assert len(photos) == 1