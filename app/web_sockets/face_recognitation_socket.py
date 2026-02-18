from fastapi import APIRouter, WebSocket,WebSocketDisconnect
import face_recognition
import numpy as np
import cv2
import base64
from app.firebase.firebase_init import db
from app.core.response import success_response,error_response
router = APIRouter()





@router.websocket("/face-recognition")
async def face_recognition_socket(websocket: WebSocket):

    await websocket.accept()

    settings_doc = db.collection("settings").document("global").get()

    if not settings_doc.exists:
        await websocket.send_json(error_response("Settings not found"))
        return

    settings = settings_doc.to_dict()
    confi_threshold = settings.get("confidence_threshold", 0.6)
    confidence_threshold = round(1 - confi_threshold / 100, 2)
    pending_match = None
    pending_encoding = None

    try:
        while True:
            data = await websocket.receive_json()

                # handle confirmation 
            if "confirm" in data:

                if not pending_match:
                    await websocket.send_json(
                        error_response("No pending face to confirm")
                    )
                    continue

                if data.get("confirm"):

                    db.collection("users") \
                        .document(pending_match["id"]) \
                        .update({
                            "face": pending_encoding.tolist()
                        })

                    await websocket.send_json(
                        success_response(message="Face updated successfully")
                    )
                else:
                    await websocket.send_json(
                        error_response("Update cancelled")
                    )

                pending_match = None
                pending_encoding = None
                continue

           
            # HANDLE IMAGE MESSAGE
          
            image_data = data.get("image")
            user_id = data.get("user_id")

            if not image_data:
                await websocket.send_json(
                    error_response("Image is required")
                )
                continue

            img_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            face_locations = face_recognition.face_locations(frame)

            if not face_locations:
                await websocket.send_json(
                    error_response("No face detected")
                )
                continue

            if len(face_locations) > 1:
                await websocket.send_json(
                    error_response("Multiple faces detected")
                )
                continue

            encodings = face_recognition.face_encodings(frame, face_locations)

            if not encodings:
                await websocket.send_json(
                    error_response("Face encoding failed")
                )
                continue

            face_encoding = encodings[0]

        
            # REGISTER MODE (when user selected)
       
            if user_id:

                user_ref = db.collection("users").document(user_id)
                user_doc = user_ref.get()

                if not user_doc.exists:
                    await websocket.send_json(
                        error_response("User not found")
                    )
                    continue

                user_ref.update({
                    "face": face_encoding.tolist()
                })

                await websocket.send_json(
                    success_response(message="Face registered / updated successfully")
                )
                continue

          
            # MATCH MODE
       
            users = db.collection("users").stream()
            matched_user = None

            for doc in users:
                user = doc.to_dict()

                if not user.get("face"):
                    continue

                stored_encoding = np.array(user["face"])

                distance = face_recognition.face_distance(
                    [stored_encoding],
                    face_encoding
                )[0]

                if distance < confidence_threshold:
                    matched_user = user
                    break

            if not matched_user:
                await websocket.send_json(
                    error_response("No matching face found")
                )
                continue

            safe_user = {
                    "user_id": matched_user.get("user_id"),
                    "id": matched_user.get("id"),
                    "name": matched_user.get("name"),
                    "email": matched_user.get("email"),
                    "role": matched_user.get("role"),
                    "status": matched_user.get("status"),
                    "phone": matched_user.get("phone"),
                    "join_date": matched_user.get("join_date").isoformat() if matched_user.get("join_date") else None,
                    "updated_at": matched_user.get("updated_at").isoformat() if matched_user.get("updated_at") else None,
            }

            # Store temporarily for confirm step
            pending_match = matched_user
            pending_encoding = face_encoding

            await websocket.send_json(
                success_response(
                    message="Face matched. Confirm update?",
                    data=safe_user
                )
            )

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("Socket Error:", e)
