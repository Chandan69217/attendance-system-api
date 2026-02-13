def success_response(data=None, message="Success"):
    return {
        "status": True,
        "message": message,
        "data": data
    }

def error_response(message="Error"):
    return {
        "status": False,
        "message": message,
    }
