# from pydantic import BaseModel
# from typing import Optional
# from enum import Enum
# from datetime import date, datetime


# class AttendanceStatusSchema(str, Enum):
#     present = "present"
#     absent = "absent"
#     late = "late"
#     on_leave = "on_leave"


# class AttendanceVerificationSchema(str, Enum):
#     pending = "pending"
#     approved = "approved"
#     rejected = "rejected"


# class AttendanceMethodSchema(str,Enum):
#     face_recognition = "face_recognition"
#     manual = "manual"
#     self_marked = "self_marked"
    

# class FacultyAttendanceSchema(BaseModel):
#     id: str
#     faculty_id: str
#     faculty_name: str
#     date: date
#     check_in: Optional[datetime] = None
#     check_out: Optional[datetime] = None
#     status: AttendanceStatusSchema
#     verified_by_id:str
#     verified_by_name: Optional[str] = None
#     verification_status: AttendanceVerificationSchema
#     remarks: Optional[str] = None


# class StudentAttendanceSchema(BaseModel):
#     id:str
#     student_id:str
#     student_name:str
#     date:date
#     subject_id:str
#     subject_name:str
#     status:AttendanceStatusSchema
#     marked_by_id:str
#     marked_by_name:str
#     methon: AttendanceMethodSchema


# class FacultyAttendanceResponseSchema(BaseModel):
#     check_in:Optional[str] = None
#     check_out:Optional[str] = None
#     remarks:Optional[str] = None


# class StudentAttendanceResponseSchema(BaseModel):
#     subject_id:str
#     marked_by_id:Optional[str] = None


from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import date, datetime


class AttendanceStatusSchema(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"
    on_leave = "on_leave"



class AttendanceVerificationSchema(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AttendanceMethodSchema(str, Enum):
    face_recognition = "face_recognition"
    manual = "manual"
    self_marked = "self_marked"



class AttendanceVerificationRequest(BaseModel):
    status: AttendanceVerificationSchema
    
class FacultyAttendanceSchema(BaseModel):
    id: str
    faculty_id: str
    faculty_name: str
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: AttendanceStatusSchema
    verification_status: AttendanceVerificationSchema
    verify_by_id:Optional[str] = None
    verify_by_name:Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StudentAttendanceSchema(BaseModel):
    id: str
    student_id: str
    student_name: str
    date: date
    subject_id: str
    subject_name: str
    status: AttendanceStatusSchema
    marked_by_id: str
    marked_by_name: str
    method: AttendanceMethodSchema
    created_at: Optional[datetime] = None



class FacultyAttendanceRequestSchema(BaseModel):
    image: str
    latitude: float
    longitude: float
    remarks: Optional[str] = None


class StudentAttendanceRequestSchema(BaseModel):
    image: str
    latitude: float
    longitude: float
    subject_id: str
    subject_name: str
    marked_by_id: str
    marked_by_name: str
