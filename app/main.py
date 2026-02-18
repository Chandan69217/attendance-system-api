from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException,FastAPI,WebSocket
from fastapi.exceptions import RequestValidationError
from app.routes.authentication import auth_routes
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes.department import department_routes
from app.routes.user import user_routes
from app.routes.classes import classes_routes
from app.routes.settings import settings_routes
from app.routes.calendar import accedmic_calendar_routes
from app.routes.session import session_routes
from app.web_sockets.attendance_socket import router as attendance_router
from app.web_sockets.face_recognitation_socket import router as face_recognition

app = FastAPI(title="Attendance System API")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = []

    for error in exc.errors():
        field = error["loc"][-1]
        message = error["msg"]

        # Custom friendly messages
        if field == "email":
            errors.append("Please enter a valid email address.")
        elif field == "phone":
            errors.append("Please enter a valid phone number.")
        else:
            errors.append(f"{field.capitalize()} is invalid.")

    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "message": errors[0]  # return first error only
        },
    )

app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(department_routes.router,prefix="/dept",tags=["Department"])
app.include_router(user_routes.router,prefix="/user",tags=["User"])
app.include_router(classes_routes.router,prefix="/class",tags=["Classes"])
app.include_router(settings_routes.router,prefix="/settings",tags=["Settings"])
app.include_router(accedmic_calendar_routes.router,prefix="/academic-calendar",tags=["Academy Calandar"])
app.include_router(session_routes.router,prefix="/sessions", tags=["Sessions"])
app.include_router(attendance_router,prefix="/ws/attendance", tags=["Sockets"])
app.include_router(face_recognition,prefix="/ws/users",tags=["Face Recognition"])



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )





