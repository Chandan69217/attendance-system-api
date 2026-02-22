from datetime import datetime
import pytz
from google.cloud.firestore_v1 import FieldFilter
from app.firebase.firebase_init import db


def generate_daily_attendance():
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.now(ist).date().isoformat()

    print(f"Generating absent attendance for {today}")

    faculties = db.collection("users") \
        .where(filter=FieldFilter("role", "==", "faculty"))\
        .stream()

    for faculty in faculties:
        user = faculty.to_dict()
        user_id = user.get("id")

        doc_id = f"{user_id}_{today}"
        ref = db.collection("faculty_attendances").document(doc_id)

        if not ref.get().exists:
            ref.set({
                "id": doc_id,
                "faculty_id": user_id,
                "faculty_name": user.get("name"),
                "date": today,
                "check_in": None,
                "check_out": None,
                "status": "absent",
                "verification_status": "pending",
                "created_at": datetime.now(ist),
                "updated_at": datetime.now(ist),
            })

    print("Absent attendance generated successfully")



