from pydantic import BaseModel
from typing import Optional



class Department(BaseModel):
    name: str
    head_id: Optional[str] = None


class UpdateDepartmentSchema(BaseModel):
    name: Optional[str] = None
    head_id: Optional[str] = None