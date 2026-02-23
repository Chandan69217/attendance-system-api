from apscheduler.schedulers.background import BackgroundScheduler
from .attendance_scheduler import generate_daily_attendance
from .lecture_scheduler import generate_daily_lecture_schedule

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        generate_daily_attendance,
        trigger="cron",
        id="daily_attendance",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=0,
        minute=0,
    )

    scheduler.add_job(
        generate_daily_lecture_schedule,
        trigger="cron",
        id="daily_lecture_schedule",
        replace_existing=True,
        day_of_week="mon-sat",
        hour=0,
        minute=2,   
    )
    scheduler.start()