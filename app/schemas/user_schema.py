from pydantic import BaseModel, EmailStr
from typing import Optional,List
from enum import Enum
from datetime import datetime



class Role(str, Enum):
    admin = "admin"
    faculty = "faculty"
    student = "student"


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"



class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    department: Optional[str] = None
    class_name: Optional[str] = None  
    avatar: Optional[str] = None
    phone: Optional[str] = None
    password: str
    join_date: Optional[datetime] = None
    face_id: Optional[List[float]] = None
    status: Optional[UserStatus] = UserStatus.active



class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    role: Optional[Role] = Role.student
    dept_id: Optional[str] = None
    class_id: Optional[str] = None  
    avatar: Optional[str] = None
    phone:str
    session_id:Optional[str]
    status: Optional[UserStatus] = UserStatus.active

class UserUpdateSchema(BaseModel):
    name: Optional[str] = None,
    email: Optional[str] = None,
    role : Optional[Role] = None,
    dept_id:Optional[str] = None,
    class_id: Optional[str] = None,
    avater: Optional[str] = None,
    phone : Optional[str] = None,
    face_id: Optional[List[float]] = None
    status: Optional[UserStatus] = None


class LoginSchema(BaseModel):
    email:EmailStr
    password:str
    role:str

class ChangePasswordSchema(BaseModel):
    email:EmailStr
    new_password: str

class VerifyOTPSchema(BaseModel):
    email:EmailStr
    otp:str