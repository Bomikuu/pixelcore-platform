from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    if isinstance(exc, ValidationError):
        code = "VALIDATION_ERROR"
        message = "The submitted data is invalid."
    elif response.status_code == 401:
        code = "AUTHENTICATION_REQUIRED"
        message = "Authentication is required."
    elif response.status_code == 403:
        code = "FORBIDDEN"
        message = "You do not have permission to perform this action."
    elif response.status_code == 404:
        code = "NOT_FOUND"
        message = "The requested resource was not found."
    elif response.status_code == 405:
        code = "METHOD_NOT_ALLOWED"
        message = "This operation is not supported."
    elif response.status_code == 429:
        code = "RATE_LIMITED"
        message = "Too many requests. Please try again later."
    else:
        code = "REQUEST_ERROR"
        message = "The request could not be completed."

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    return response
