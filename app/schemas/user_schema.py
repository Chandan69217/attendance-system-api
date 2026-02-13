from pydantic import BaseModel, EmailStr
from typing import Optional
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
    status: Optional[UserStatus] = UserStatus.active



class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    role: Optional[Role] = Role.student
    department: Optional[str] = None
    class_name: Optional[str] = None  
    avatar: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[UserStatus] = UserStatus.active


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