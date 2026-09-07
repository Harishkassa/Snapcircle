from unittest.mock import patch, MagicMock
import numpy as np
import pytest
from src.services.v1.embedding_service import generate_embedding
# ^ apna actual import path daalo


@pytest.mark.asyncio
async def test_generate_embedding_returns_list_for_valid_face():
    dummy_face_crop = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

    # Fake face object banayo jaisa insightface deta hai
    fake_face = MagicMock()
    fake_face.embedding = np.array([0.1, 0.2, 0.3])

    with patch(
        "src.services.v1.embedding_service._face_app.get",
        return_value=[fake_face]
    ):
        result = await generate_embedding(dummy_face_crop)

    assert isinstance(result, list)
    print("result", result)
    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_when_no_face_found():
    dummy_face_crop = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

    with patch(
        "src.services.v1.embedding_service._face_app.get",
        return_value=[]   # koi face nahi mila
    ):
        result = await generate_embedding(dummy_face_crop)

    assert result is None