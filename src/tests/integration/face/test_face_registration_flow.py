import base64
import cv2
import numpy as np

async def test_face_capture_ws_locks_and_saves_to_redis(
        test_client, fake_redis, mock_retinaface_detect
):
    dummy_frame = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy_frame)
    b64 = base64.b64encode(buffer).decode("utf-8")

    with test_client.websocket_connect("/api/v1/face_capture/ws/face-capture") as websocket:
        for _ in range(5):   # LOCK_FRAMES_REQUIRED jitni baar
            websocket.send_json({"frame": f"data:image/jpeg;base64,{b64}"})
            response = websocket.receive_json()
            print("response", response)

            if response.get("status") == "success":
                break

    # Sirf FINAL response check karo — ye hi last message hai
    assert response["status"] == "success"
    temp_face_id = response["temp_face_id"]
    assert "temp_face_id" in response
    

    mock_retinaface_detect.assert_called()

    saved_data = await fake_redis.get(f"temp_face:{temp_face_id}")
    print("temp_face_id", temp_face_id)
    assert saved_data is not None
        