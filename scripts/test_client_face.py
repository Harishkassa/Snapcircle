"""
test_client.py

Simple standalone Python WebSocket client to test the face-capture
pipeline WITHOUT a frontend/browser. Opens your webcam, sends frames
to the FastAPI websocket route, prints server responses.

Install:
    pip install websockets opencv-python

Run (after starting uvicorn separately):
    python test_client.py
"""
import asyncio
import cv2
import json
import base64
import websockets

from scripts import *

WS_URL = "ws://localhost:8000/api/v1/face_capture/ws/face-capture"


async def face_client_test():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam")
        return

    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            _, buffer = cv2.imencode(".jpg", frame)
            b64 = base64.b64encode(buffer).decode("utf-8")

            await ws.send(json.dumps({"frame": f"data:image/jpeg;base64,{b64}"}))

            response = await ws.recv()
            data = json.loads(response)
            print(data)

            # show local preview window (optional)
            cv2.imshow("Sending to server", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if data.get("status") == "success":
                temp_face_id = data.get("temp_face_id")
                print(f"SAVE THIS ID: {temp_face_id}")
                break

    cap.release()
    cv2.destroyAllWindows()
    return temp_face_id

if __name__ == "__main__":
    result_id = asyncio.run(face_client_test())
    print("Returned ID:", result_id)