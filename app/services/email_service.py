# import smtplib
# from email.message import EmailMessage
# import os


    
# def send_email(to_email: str, message:str):
#     EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
#     EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

#     msg = EmailMessage()
#     msg["Subject"] = "Your Attendance System Login Credentials"
#     msg["From"] = EMAIL_ADDRESS
#     msg["To"] = to_email

#     msg.set_content(message)

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
#         smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#         smtp.send_message(msg)


import resend
import os


def get_email_notifications_enabled() -> bool:
    """Read the email_notifications flag from the global settings document.
    Defaults to True if the document or field is missing."""
    try:
        from app.firebase.firebase_init import db
        settings_doc = db.collection("settings").document("global").get()
        if settings_doc.exists:
            return settings_doc.to_dict().get("email_notifications", True)
    except Exception as e:
        print(f"[email_service] Could not read settings: {e}")
    return True


def send_email(to_email: str, message: str, subject: str = "Your Attendance System Login Credentials"):
    """Send an email unconditionally (use for security-critical emails like OTP)."""
    resend.api_key = os.getenv("RESEND_API_KEY")

    response = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": to_email,
        "subject": subject,
        "text": message,
    })

    print(response)


def send_email_if_enabled(to_email: str, message: str, subject: str = "Your Attendance System Login Credentials"):
    """Send an email only if the email_notifications setting is enabled."""
    if not get_email_notifications_enabled():
        print(f"[email_service] Email notifications disabled — skipping email to {to_email}")
        return
    send_email(to_email, message, subject)

def get_account_create_confirmation(email:str,password:str,user_name: str) -> str:
    return f"""
            Hello {user_name},

                Your account has been created.

                Email: {email}
                Password: {password}

                Please change your password after login.

                Regards,
                Attendance System
            """


def get_password_change_confirmation(user_name: str) -> str:
    return f"""
            Hello {user_name},

                Your password has been successfully changed.

                If you did not perform this action, please reset your password immediately or contact support.

                Regards,
                Attendance System
                """
