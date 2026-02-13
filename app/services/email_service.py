import smtplib
from email.message import EmailMessage
import os

def send_email(to_email: str, message:str):
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = "Your Attendance System Login Credentials"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.set_content(message)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)




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
