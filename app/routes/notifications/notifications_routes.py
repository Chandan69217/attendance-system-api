from fastapi import APIRouter, Depends, BackgroundTasks, WebSocket
from app.schemas.notifications_schema import NotificationSchema, UpdateNotificationSchema, NotificationTarget
from app.firebase.firebase_init import db
from app.core.security import verify_token
from app.schemas.user_schema import Role
from app.core.response import error_response, success_response
from google.cloud.firestore_v1 import FieldFilter, Query
from datetime import datetime, timezone
from app.web_sockets.notifications_socket import manager
from app.services.email_service import send_email_if_enabled
import asyncio
import uuid




router = APIRouter()





@router.post("/create")
async def create_notification(data: NotificationSchema, current_user: dict = Depends(verify_token)):

    user_role = current_user.get("role")

    if user_role == Role.student.value:
        return error_response(
            message="Only Admin and Faculty can send notifications"
        )

    notification_ref = db.collection("notifications")

    target = data.target.value

    query = db.collection("users")
    if target != NotificationTarget.ALLUSER.value:
        query = query.where(filter=FieldFilter("role", "==", target))

    users = query.stream()

    base_notification = data.model_dump()
    base_notification["created_at"] = datetime.now(timezone.utc).isoformat()
    base_notification["read"] = False

    batch_id = str(uuid.uuid4())
    
    for user in users:

        doc_ref = notification_ref.document()

        notification_data = base_notification.copy()
        notification_data["user_id"] = user.id
        notification_data["id"] = doc_ref.id
        notification_data["batch_id"] = batch_id

        doc_ref.set(notification_data)

        asyncio.create_task(
            manager.send_notification(
                user.id,
                notification_data
            )
        )

    return success_response(message="Notification sent successfully")




@router.get("/get-all")
def get_notifications(current_user: dict = Depends(verify_token)):

    user_id = current_user.get("id")
    user_role = current_user.get("role")

    print(f"DEBUG: user_id={user_id}, user_role={user_role}")

    if user_role == Role.admin.value:
        # Admin can see all notifications to manage them
        notifications = db.collection("notifications").stream()
    else:
        # Regular users only see their own notifications
        notifications = (
            db.collection("notifications")
            .where("user_id", "==", user_id)
            .stream()
        )

    results = []
    seen_batches = set()

    for notif in notifications:
        data = notif.to_dict()
        data["id"] = notif.id
        
        if user_role == Role.admin.value:
            batch_id = data.get("batch_id")
            if batch_id:
                if batch_id in seen_batches:
                    continue
                seen_batches.add(batch_id)
            # If no batch_id, it's an individual notification, so we include it
        
        results.append(data)

    # Sort notifications by created_at in descending order (newest first)
    # This avoids the "requires an index" error in Firestore
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return success_response(
        message="notifications fetched successfully",
        data=results
    )



@router.put("/read/{id}")
def mark_as_read(id: str, current_user: dict = Depends(verify_token)):

    user_id = current_user.get("id")
    notif_ref = db.collection("notifications").document(id)
    notification = notif_ref.get()

    if not notification.exists:
        return error_response(message="Notification not found")

    notif_data = notification.to_dict()
    role = current_user.get("role")
  
    if notif_data.get("user_id") != user_id and role != Role.admin.value:
        return error_response(message="Unauthorized to read this notification")

    batch_id = notif_data.get("batch_id")

    if role == Role.admin.value and batch_id:
        # Admin is marking a batch notification as read.
        # Mark all notifications in this batch as read so it persists across refreshes.
        batch_notifications = (
            db.collection("notifications")
            .where(filter=FieldFilter("batch_id", "==", batch_id))
            .stream()
        )
        batch = db.batch()
        for doc in batch_notifications:
            batch.update(doc.reference, {"read": True})
        batch.commit()
    else:
        notif_ref.update({"read": True})

    return success_response(message="Notification marked as read", data=notif_data)



@router.delete("/delete/{id}")
def deleteNotification(id: str, current_user: dict = Depends(verify_token)):

    role = current_user.get("role")

    if role != Role.admin.value:
        return error_response(message="Only admin can delete the notification")

    notif_ref = db.collection("notifications").document(id)
    notification = notif_ref.get()

    if not notification.exists:
        return error_response(message="Notification not found")

    notif_data = notification.to_dict()
    batch_id = notif_data.get("batch_id")

    if batch_id:
        
        notifications_to_delete = (
            db.collection("notifications")
            .where(filter=FieldFilter("batch_id", "==", batch_id))
            .stream()
        )
        
        batch = db.batch()
        count = 0
        for doc in notifications_to_delete:
            batch.delete(doc.reference)
            count += 1
        batch.commit()
        
        return success_response(
            message=f"Successfully deleted {count} notifications from batch",
            data=notif_data
        )
    else:
        # Fallback for legacy notifications without batch_id
        notif_ref.delete()
        return success_response(
            message="Notification deleted successfully",
            data=notif_data
        )






# This is for the email notifications

def send_email_notification(email: str, message: str):
    """Send a notification email — respects the email_notifications setting."""
    send_email_if_enabled(
        to_email=email,
        message=message,
        subject="Attendance System Notification"
    )


@router.post("/notify-email")
def notify(
    background_tasks: BackgroundTasks,
    email: str,
    message: str,
    current_user: dict = Depends(verify_token)
):
    user_role = current_user.get("role")
    if user_role != Role.admin.value:
        return error_response(message="Only admin can send email notifications")

    background_tasks.add_task(send_email_notification, email, message)

    return success_response(message="Email notification scheduled")


