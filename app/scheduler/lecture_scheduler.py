from datetime import datetime
import pytz
from google.cloud.firestore_v1 import FieldFilter
from app.firebase.firebase_init import db
from app.lib.utils import generate_lecture_id


def generate_daily_lecture_schedule():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    today = now.date().isoformat()

    print(f"Generating lecture schedule for {today}")

    subjects = db.collection("subjects").stream()
    users_ref = db.collection("users").select(['id','name',"dept_id","subject_id"])\
        .where(filter=FieldFilter("role","==","faculty"))\
        .stream()
    
    users=[]
    for user in users_ref:
        u = user.to_dict()
        if(u):
            users.append(u)


    map_user = {u["subject_id"] : u for u in users}

    for subject in subjects:
        subject_data = subject.to_dict()

        lecture_id = f"{generate_lecture_id()}_{today}"

        ref = db.collection("lectures").document(lecture_id)

        if not ref.get().exists:
            faculty = map_user.get(subject.id)
            if(not faculty):
                return
            
            ref.set({
                "id": lecture_id,
                "subject_id": subject.id,
                "subject_name": subject_data.get("name"),
                "faculty_id": faculty["id"],
                "faculty_name": faculty['name'],
                "class_id": subject_data.get("class_id"),
                "class_name": subject_data.get("class_name"),
                "date": today,
                "start_time": subject_data.get("start_time"),
                "end_time": subject_data.get("end_time"),
                "status": "scheduled",
                "created_at": now
            })

    print("Lecture schedule generated")

