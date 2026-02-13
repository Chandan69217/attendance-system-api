from fastapi import APIRouter,status,BackgroundTasks
from app.schemas.user_schema import RegisterSchema, LoginSchema,User,ChangePasswordSchema,VerifyOTPSchema
from app.core.security import hash_password, verify_password, create_access_token
from app.firebase.firebase_init import db
from app.core.response import success_response, error_response
from app.lib.utils import generate_user_id,generate_random_password
from datetime import datetime,timedelta,timezone
from app.services.email_service import send_email,get_password_change_confirmation,get_account_create_confirmation
from app.core.custom_exception import HttpsException
from app.lib.field_validation import phone_validate
from app.schemas.user_schema import Role,UserStatus
import random
import time
from google.cloud.firestore_v1 import FieldFilter
from pydantic import EmailStr


router = APIRouter()



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user_data: RegisterSchema,
    background_tasks: BackgroundTasks
):

    collection = db.collection("users")

   
    if user_data.role in [Role.faculty, Role.student] and not user_data.department:
        return error_response(message="Department is required")

    if user_data.role == Role.student and not user_data.class_name:
        return error_response(message="Class is required")

    if not phone_validate(user_data.phone):
        return error_response(message="Please enter a valid 10-digit mobile number.")

    if user_data.role.name not in Role.__members__:
        return error_response(message="Invalid user role")

    if user_data.status.name not in UserStatus.__members__:
        return error_response(message="Invalid status")

    email = user_data.email.lower().strip()
    phone = user_data.phone.strip()

   
    email_exists = collection \
        .where(filter=FieldFilter("email", "==", email)) \
        .limit(1) \
        .get()

    if email_exists:
        return error_response(message="Email already exists")

    phone_exists = collection \
        .where(filter=FieldFilter("phone", "==", phone)) \
        .limit(1) \
        .get()

    if phone_exists:
        return error_response(message="Phone already exists")


    user_id = generate_user_id(user_data.role.value)
    plain_password = generate_random_password()
    hashed_password = hash_password(plain_password)

  
    user_dict = {
        "id": user_id,
        "name": user_data.name.strip(),
        "email": email,
        "role": user_data.role.value,
        "department": user_data.department,
        "class_name": user_data.class_name,
        "avatar": user_data.avatar,
        "phone": phone,
        "password": hashed_password,
        "join_date": datetime.now(),
        "status": user_data.status.value
    }

    collection.document(user_id).set(user_dict)

   
    message = get_account_create_confirmation(
        email=email,
        password=plain_password,
        user_name=user_data.name
    )

    background_tasks.add_task(send_email, email, message)

   
    response_data = user_dict.copy()
    response_data.pop("password", None)

    return success_response(
        message="User registered successfully",
        data=response_data
    )






@router.post("/login")
def login(login_data: LoginSchema):

    email = login_data.email.lower().strip()


    query = db.collection("users") \
        .where(filter=FieldFilter("email", "==", email)) \
        .limit(1) \
        .get()

    if not query:
        return error_response(message="User not found")

    user_doc = query[0]
    user_dict = user_doc.to_dict()


    if login_data.role != user_dict.get("role"):
        return error_response(
            message="Selected role does not match the registered account role."
        )

 
    if not verify_password(login_data.password, user_dict.get("password")):
        return error_response(message="Incorrect password")

  
    token = create_access_token({
        "sub": user_dict["email"],
        "role": user_dict["role"],
        "id": user_dict["id"]
    })


    user_dict.pop("password", None)

    return {
        "status":True,
        "message":"Login successful",
        "token": token,
        "data": user_dict
    }

    



@router.post("/send-otp")
def send_otp(
    email: EmailStr,
    background_tasks: BackgroundTasks
):

    email = email.lower().strip()

 
    user_query = db.collection("users") \
        .where(filter=FieldFilter("email", "==", email)) \
        .limit(1) \
        .get()


    if not user_query:
        return error_response(message="User not found")

  
    otp = str(random.randint(100000, 999999))

   
    expires_at = datetime.now() + timedelta(minutes=5)

    otp_ref = db.collection("otp_verifications").document(email)

  
    existing_otp = otp_ref.get()
    if existing_otp.exists:
        data = existing_otp.to_dict()
        if data.get("expires_at") and data["expires_at"] > datetime.utcnow():
            return error_response(message="Please wait before requesting another OTP")


    otp_ref.set({
        "otp": otp,
        "verified": False,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })


    message = f"""
    Hello,

    Your OTP for password reset is: {otp}

    This OTP will expire in 5 minutes.

    Regards,
    Attendance System
    """

    background_tasks.add_task(send_email, email, message)

    return success_response(
        message="OTP has been sent"
    )





@router.post("/verify-otp")
def verify_otp(data: VerifyOTPSchema):

    email = data.email.lower().strip()

    otp_ref = db.collection("otp_verifications").document(email)
    otp_doc = otp_ref.get()

    if not otp_doc.exists:
        return error_response(message="Invalid or expired OTP")

    otp_data = otp_doc.to_dict()

   
    if otp_data.get("verified"):
        return error_response(message="OTP already verified")

   
    if otp_data.get("expires_at") < datetime.now(timezone.utc):
        otp_ref.delete()
        return error_response(message="OTP expired")

  
    attempts = otp_data.get("attempts", 0)

    if attempts >= 3:
        otp_ref.delete()
        return error_response(message="Too many invalid attempts")

    
    if data.otp != otp_data.get("otp"):
        otp_ref.update({
            "attempts": attempts + 1
        })
        return error_response(message="Invalid OTP")


    otp_ref.update({
        "verified": True,
        "verified_at": datetime.utcnow()
    })

    return success_response(
        message="OTP verified successfully"
    )





@router.post("/change-password")
def change_password(
    data: ChangePasswordSchema,
    background_tasks: BackgroundTasks
):

    email = data.email.lower().strip()


    otp_ref = db.collection("otp_verifications").document(email)
    otp_doc = otp_ref.get()

    if not otp_doc.exists:
        return error_response(message="Invalid or expired OTP")

    otp_data = otp_doc.to_dict()


    if otp_data.get("expires_at") < datetime.now(timezone.utc):
        otp_ref.delete()
        return error_response(message="OTP expired. Please request again.")


    if not otp_data.get("verified"):
        return error_response(message="OTP not verified")


    user_query = db.collection("users") \
        .where(filter=FieldFilter("email", "==", email)) \
        .limit(1) \
        .get()

    if not user_query:
        return error_response(message="User not found")

    user_doc = user_query[0]
    user_dict = user_doc.to_dict()

    if verify_password(data.new_password, user_dict.get("password")):
        return error_response(message="New password cannot be same as old password")

    if len(data.new_password) < 6:
        return error_response(message="Password must be at least 6 characters")

    hashed_password = hash_password(data.new_password)

  
    user_doc.reference.update({
        "password": hashed_password,
        "updated_at": datetime.utcnow()
    })


    otp_ref.delete()


    background_tasks.add_task(
        send_email,
        email,
        get_password_change_confirmation(
            user_name=user_dict.get("name")
        )
    )

    return success_response(
        message="Password changed successfully"
    )



