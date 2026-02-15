from fastapi import APIRouter,Depends,status
from app.core.security import verify_token
from app.core.response import error_response,success_response
from app.firebase.firebase_init import db
from app.schemas.setting_schema import SettingKey
from datetime import datetime,timezone

router = APIRouter()

from fastapi import APIRouter, status, Depends
from datetime import datetime, date
from app.core.security import verify_token
from app.core.response import success_response, error_response
from app.firebase.firebase_init import db
from app.schemas.setting_schema import SettingKey

router = APIRouter()



@router.get("/", status_code=status.HTTP_200_OK)
def academic_calendar(current_user: dict = Depends(verify_token)):

    settings_ref = db.collection("settings").document("global")
    settings_doc = settings_ref.get()

    if not settings_doc.exists:
        return error_response(message="Settings not found")

    settings = settings_doc.to_dict()


    semester_start = settings.get(SettingKey.semester_start.value)
    semester_end = settings.get(SettingKey.semester_end.value)
    holidays = settings.get(SettingKey.holidays.value, [])

  
    if not semester_start or not semester_end:
        return error_response(message="Semester dates not configured")

    try:
        start_date = datetime.strptime(f"{semester_start.strip()}", "%Y-%m-%d").date()
      
        end_date = datetime.strptime(f"{semester_end.strip()}", "%Y-%m-%d").date()

        holiday_list = []   
        for h in holidays:
            try:
                holiday_list.append(datetime.strptime(f"{h.strip()}", "%d-%m-%Y").date())
            except Exception:
                continue

    except Exception:
        return error_response(message="Invalid date format in settings")

    return success_response(
        message="Academic calendar fetched successfully",
        data={
            "academic_year": start_date.year,
            "semester_start": start_date,
            "semester_end": end_date,
           "holidays": holiday_list
    
        }
    )


        