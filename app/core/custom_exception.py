from fastapi import HTTPException, status
from app.core.response import error_response

class HttpsException(HTTPException):
    def __init__(self, message: str = "Resource already exists",status_code:int=200):
        super().__init__(
            status_code=status_code,
            detail= message
        )
