import re


phone_pattern  = r"^[6-9]\d{9}$"
password_pattern  = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
email_pattern =  r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

def phone_validate(phone:str):
    return re.match(phone_pattern,phone)


def password_validate(password:str):
    return re.match(password_pattern,password)

def email_validate(email:str):
    return re.match(email_validate,email)


# raise HttpsException(message="Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.")