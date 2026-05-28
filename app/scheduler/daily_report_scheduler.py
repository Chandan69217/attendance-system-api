from datetime import datetime
import pytz
from google.cloud.firestore_v1 import FieldFilter
from app.firebase.firebase_init import db


def generate_daily_report():
    """
    Generates a daily attendance summary report and saves it to Firestore
    under the 'daily_reports' collection.

    This job runs every day at 11:59 PM IST (after all attendance is finalised).
    It ONLY executes if the admin has enabled 'daily_reports' in system settings.
    """
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    today = now.date().isoformat()      # "YYYY-MM-DD"

    print(f"[DailyReport] Checking if daily reports are enabled...")

    # ── 1. Read the setting flag ──────────────────────────────────────────────
    settings_doc = db.collection("settings").document("global").get()
    if settings_doc.exists:
        settings = settings_doc.to_dict()
        if not settings.get("daily_reports", False):
            print("[DailyReport] 'daily_reports' is disabled — skipping.")
            return
    else:
        print("[DailyReport] No settings document found — skipping.")
        return

    print(f"[DailyReport] Generating report for {today}...")

    # ── 2. Skip if a report for today already exists ──────────────────────────
    report_ref = db.collection("daily_reports").document(today)
    if report_ref.get().exists:
        print(f"[DailyReport] Report for {today} already exists — skipping.")
        return

    # ── 3. Aggregate STUDENT attendance for today ─────────────────────────────
    student_stats = {"present": 0, "absent": 0, "late": 0, "on_leave": 0, "total": 0}

    student_records = (
        db.collection("student_attendance")
        .where(filter=FieldFilter("date", "==", today))
        .stream()
    )

    for doc in student_records:
        rec = doc.to_dict()
        status = rec.get("status", "absent")
        student_stats["total"] += 1
        if status in student_stats:
            student_stats[status] += 1

    student_present_rate = (
        round((student_stats["present"] + student_stats["late"]) * 100 / student_stats["total"], 2)
        if student_stats["total"] > 0
        else 0.0
    )

    # ── 4. Aggregate FACULTY attendance for today ─────────────────────────────
    faculty_stats = {"present": 0, "absent": 0, "late": 0, "on_leave": 0, "total": 0}

    faculty_records = (
        db.collection("faculty_attendance")
        .where(filter=FieldFilter("date", "==", today))
        .stream()
    )

    for doc in faculty_records:
        rec = doc.to_dict()
        status = rec.get("status", "absent")
        faculty_stats["total"] += 1
        if status in faculty_stats:
            faculty_stats[status] += 1

    faculty_present_rate = (
        round((faculty_stats["present"] + faculty_stats["late"]) * 100 / faculty_stats["total"], 2)
        if faculty_stats["total"] > 0
        else 0.0
    )

    # ── 5. Count pending faculty verifications ────────────────────────────────
    pending_verification_query = (
        db.collection("faculty_attendance")
        .where(filter=FieldFilter("date", "==", today))
        .where(filter=FieldFilter("verification_status", "==", "pending"))
        .count()
        .get()
    )
    pending_verifications = (
        pending_verification_query[0][0].value if pending_verification_query else 0
    )

    # ── 6. Count lectures scheduled vs completed today ────────────────────────
    lectures_scheduled = 0
    lectures_completed = 0

    lecture_records = (
        db.collection("lectures")
        .where(filter=FieldFilter("date", "==", today))
        .stream()
    )

    for doc in lecture_records:
        rec = doc.to_dict()
        lectures_scheduled += 1
        if rec.get("status") == "closed":
            lectures_completed += 1

    # ── 7. Build and save the report document ────────────────────────────────
    report = {
        "id": today,
        "date": today,
        "generated_at": now.isoformat(),

        # Student summary
        "student_total": student_stats["total"],
        "student_present": student_stats["present"],
        "student_absent": student_stats["absent"],
        "student_late": student_stats["late"],
        "student_on_leave": student_stats["on_leave"],
        "student_present_rate": student_present_rate,

        # Faculty summary
        "faculty_total": faculty_stats["total"],
        "faculty_present": faculty_stats["present"],
        "faculty_absent": faculty_stats["absent"],
        "faculty_late": faculty_stats["late"],
        "faculty_on_leave": faculty_stats["on_leave"],
        "faculty_present_rate": faculty_present_rate,

        # Verification & lectures
        "pending_verifications": pending_verifications,
        "lectures_scheduled": lectures_scheduled,
        "lectures_completed": lectures_completed,

        # Overall combined rate
        "overall_present_rate": round(
            (student_present_rate + faculty_present_rate) / 2, 2
        ),
    }

    report_ref.set(report)
    print(f"[DailyReport] Report saved for {today}: "
          f"students={student_present_rate}%, faculty={faculty_present_rate}%")
