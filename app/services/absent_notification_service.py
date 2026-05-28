"""
Absent notification helper.

Called right after a lecture is ended. It:
  1. Reads settings — skips if send_absent_notifications is disabled.
  2. Finds all students in the lecture's class.
  3. Checks which ones do NOT have a present/late attendance record for this lecture's subject today.
  4. For each absent student:
     - Creates an in-app notification in Firestore.
     - Sends an email (respects email_notifications toggle).
"""

from datetime import datetime, timezone
import pytz
import uuid
from app.firebase.firebase_init import db
from app.services.email_service import send_email_if_enabled


def notify_absent_students(lecture_id: str):
    """
    Should be called in a BackgroundTask immediately after a lecture is ended.
    """
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    today = now.date().isoformat()

    print(f"[AbsentNotify] Processing lecture {lecture_id} for absent students...")

    # ── 1. Check settings ─────────────────────────────────────────────────────
    settings_doc = db.collection("settings").document("global").get()
    if not settings_doc.exists:
        print("[AbsentNotify] No settings document — skipping.")
        return

    settings = settings_doc.to_dict()
    if not settings.get("send_absent_notifications", True):
        print("[AbsentNotify] send_absent_notifications is disabled — skipping.")
        return

    # ── 2. Load lecture details ───────────────────────────────────────────────
    lecture_doc = db.collection("lectures").document(lecture_id).get()
    if not lecture_doc.exists:
        print(f"[AbsentNotify] Lecture {lecture_id} not found — skipping.")
        return

    lecture = lecture_doc.to_dict()
    subject_id = lecture.get("subject_id")
    subject_name = lecture.get("subject_name", "Unknown Subject")
    class_id = lecture.get("class_id")
    lecture_date = lecture.get("date", today)

    if not class_id or not subject_id:
        print("[AbsentNotify] Lecture has no class_id or subject_id — skipping.")
        return

    # ── 3. Get all students in the class ─────────────────────────────────────
    students_ref = db.collection("users") \
        .where("role", "==", "student") \
        .where("class_id", "==", class_id) \
        .stream()

    students = []
    for doc in students_ref:
        u = doc.to_dict()
        if u.get("id"):
            students.append(u)

    if not students:
        print(f"[AbsentNotify] No students found in class {class_id}.")
        return

    # ── 4. Find students who have a present/late record for this subject today ─
    present_student_ids = set()
    attendance_docs = db.collection("student_attendances") \
        .where("subject_id", "==", subject_id) \
        .where("date", "==", lecture_date) \
        .stream()

    for doc in attendance_docs:
        rec = doc.to_dict()
        if rec.get("status") in ("present", "late"):
            present_student_ids.add(rec.get("student_id"))

    # ── 5. Notify absent students ─────────────────────────────────────────────
    batch_id = str(uuid.uuid4())
    alerted = 0

    for student in students:
        student_id = student.get("id")
        if student_id in present_student_ids:
            continue  # already marked present/late — skip

        student_name = student.get("name", "Student")
        student_email = student.get("email", "")

        notification_title = "📋 Absent from Lecture"
        notification_message = (
            f"You were marked absent for {subject_name} on {lecture_date}. "
            f"If this is incorrect, please contact your faculty immediately."
        )

        # 5a. In-app notification
        notif_ref = db.collection("notifications").document()
        notif_ref.set({
            "id": notif_ref.id,
            "batch_id": batch_id,
            "user_id": student_id,
            "title": notification_title,
            "message": notification_message,
            "category": "attendance",
            "target": "student",
            "read": False,
            "created_at": now.isoformat(),
        })

        # 5b. Email notification (respects email_notifications toggle)
        if student_email:
            email_body = (
                f"Hello {student_name},\n\n"
                f"You have been marked absent for the following lecture:\n\n"
                f"  Subject : {subject_name}\n"
                f"  Date    : {lecture_date}\n\n"
                f"If you believe this is a mistake, please contact your faculty.\n\n"
                f"Regards,\nAttendance System"
            )
            send_email_if_enabled(
                to_email=student_email,
                message=email_body,
                subject=f"Absent Notice — {subject_name} ({lecture_date})",
            )

        alerted += 1
        print(f"[AbsentNotify] Notified {student_name} ({student_id}) — absent from {subject_name}.")

    print(f"[AbsentNotify] Done. {alerted}/{len(students)} student(s) notified as absent.")
