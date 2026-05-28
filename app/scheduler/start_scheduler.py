from apscheduler.schedulers.background import BackgroundScheduler
from .attendance_scheduler import generate_daily_attendance
from .lecture_scheduler import generate_daily_lecture_schedule
from .daily_report_scheduler import generate_daily_report
from .low_attendance_scheduler import check_low_attendance


def start_scheduler():
    print("Starting scheduler...")
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # ── 00:00 — Mark all faculty absent if no record exists for the day ────────
    scheduler.add_job(
        generate_daily_attendance,
        trigger="cron",
        id="daily_attendance",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=0,
        minute=0,
    )

    # ── 00:02 — Generate lecture slots from subjects ───────────────────────────
    scheduler.add_job(
        generate_daily_lecture_schedule,
        trigger="cron",
        id="daily_lecture_schedule",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=0,
        minute=2,
    )

    # ── 23:59 — Generate daily attendance summary report (if enabled) ──────────
    scheduler.add_job(
        generate_daily_report,
        trigger="cron",
        id="daily_report",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=23,
        minute=59,
    )

    # ── 20:00 — Send low-attendance alerts (if enabled in settings) ───────────
    # Runs at 8 PM IST every weekday so students get the warning before the next day.
    scheduler.add_job(
        check_low_attendance,
        trigger="cron",
        id="low_attendance_alerts",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=20,
        minute=0,
    )

    scheduler.start()