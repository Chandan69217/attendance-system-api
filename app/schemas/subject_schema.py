from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import date



class CreateSubjectSchema(BaseModel):
    name:str
    dept_id:str
    


class UpdateSubjectSchema(BaseModel):
    name: Optional[str] = None
    dept_id:Optional[str] = None
   
