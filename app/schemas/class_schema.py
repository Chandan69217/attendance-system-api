from pydantic import BaseModel,EmailStr
from typing import Optional


class ClassSchema(BaseModel):
    name: str
    dept_id: str
    class_teacher_id: Optional[str] = None
    student_count: int = 0



class ClassUpdateSchema(BaseModel):
    name:Optional[str] = None
    dept_id:Optional[str] = None
    class_teacher_id:Optional[str] = None
    stu:Optional[str] = None