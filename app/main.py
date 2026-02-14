from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException,FastAPI
from fastapi.exceptions import RequestValidationError
from app.routes.authentication import auth_routes
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.routes.department import department_routes
from app.routes.user import user_routes
from app.routes.classes import classes_routes

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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
