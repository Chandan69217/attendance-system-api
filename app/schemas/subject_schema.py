from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import date



class CreateSubjectSchema(BaseModel):
    name:str
    dept_id:str
    start_time:str
    end_time:str
    class_id:str
    


class UpdateSubjectSchema(BaseModel):
    name: Optional[str] = None
    dept_id:Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    class_id: Optional[str] = None
   
