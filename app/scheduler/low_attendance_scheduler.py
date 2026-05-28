from datetime import datetime, timezone
import pytz
from collections import defaultdict
from app.firebase.firebase_init import db
from app.services.email_service import send_email_if_enabled
import uuid


def check_low_attendance():
    """
    Runs daily to detect students/faculty below the minimum attendance threshold.

    Steps:
      1. Read settings — bail out if 'low_attendance_alerts' is disabled.
      2. For every student, calculate per-subject attendance %.
      3. Any subject below min_attendance_percent fires:
         - An in-app notification (Firestore 'notifications' collection).
         - An email alert (respects email_notifications toggle).
    """
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    print("[LowAttendance] Checking low_attendance_alerts setting...")

    # ── 1. Read settings ──────────────────────────────────────────────────────
    settings_doc = db.collection("settings").document("global").get()
    if not settings_doc.exists:
        print("[LowAttendance] No settings document found — skipping.")
        return

    settings = settings_doc.to_dict()
    if not settings.get("low_attendance_alerts", False):
        print("[LowAttendance] 'low_attendance_alerts' is disabled — skipping.")
        return

    threshold = settings.get("min_attendance_percent", 75)
    print(f"[LowAttendance] Running with threshold={threshold}%")

    # ── 2. Load all students ──────────────────────────────────────────────────
    students = db.collection("users") \
        .where("role", "==", "student") \
        .stream()

    student_map = {}   # student_id → { id, name, email }
    for doc in students:
        u = doc.to_dict()
        sid = u.get("id")
        if sid:
            student_map[sid] = {
                "id": sid,
                "name": u.get("name", "Student"),
                "email": u.get("email", ""),
            }

    if not student_map:
        print("[LowAttendance] No students found — skipping.")
        return

    # ── 3. Aggregate student attendance per subject ───────────────────────────
    # Structure: { student_id: { subject_id: { name, total, present } } }
    stats: dict = defaultdict(lambda: defaultdict(lambda: {
        "subject_name": "",
        "total": 0,
        "present": 0,
    }))

    attendance_docs = db.collection("student_attendances").stream()
    for doc in attendance_docs:
        rec = doc.to_dict()
        student_id = rec.get("student_id")
        subject_id = rec.get("subject_id")
        if not student_id or not subject_id:
            continue

        entry = stats[student_id][subject_id]
        entry["subject_name"] = rec.get("subject_name", subject_id)
        entry["total"] += 1
        if rec.get("status") in ("present", "late"):
            entry["present"] += 1

    # ── 4. Find students below threshold & notify ─────────────────────────────
    alerted_count = 0
    batch_id = str(uuid.uuid4())

    for student_id, subjects in stats.items():
        student = student_map.get(student_id)
        if not student:
            continue

        low_subjects = []
        for subject_id, data in subjects.items():
            total = data["total"]
            present = data["present"]
            pct = round((present / total) * 100, 1) if total > 0 else 0.0
            if pct < threshold:
                low_subjects.append({
                    "name": data["subject_name"],
                    "percentage": pct,
                })

        if not low_subjects:
            continue

        # Build the alert message
        subject_lines = "\n".join(
            f"  • {s['name']}: {s['percentage']}%"
            for s in low_subjects
        )
        notification_title = "⚠️ Low Attendance Alert"
        notification_message = (
            f"Your attendance is below {threshold}% in the following subject(s):\n"
            f"{subject_lines}\n\n"
            "Please contact your faculty or attend more classes to avoid academic consequences."
        )

        # 4a. Save in-app notification to Firestore
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

        # 4b. Send email alert (respects email_notifications setting)
        email = student.get("email", "")
        if email:
            email_body = (
                f"Hello {student['name']},\n\n"
                f"This is an automated low-attendance alert.\n\n"
                f"Your attendance is below the required {threshold}% in:\n"
                f"{subject_lines}\n\n"
                f"Please take immediate action to improve your attendance.\n\n"
                f"Regards,\nAttendance System"
            )
            send_email_if_enabled(
                to_email=email,
                message=email_body,
                subject=f"⚠️ Low Attendance Warning — below {threshold}%",
            )

        alerted_count += 1
        print(
            f"[LowAttendance] Alerted {student['name']} ({student_id}) "
            f"— {len(low_subjects)} subject(s) below threshold."
        )

    print(f"[LowAttendance] Done. {alerted_count} student(s) alerted.")
