"""
Custom exception handler for Student Analytics Platform REST API.
Returns consistent JSON error responses across all endpoints.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF's default handler
    and returns a consistent error format:
    {
        "error": true,
        "status_code": 403,
        "detail": "You do not have permission to perform this action."
    }
    """
    # Call DRF's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap in a consistent structure
        response.data = {
            'error': True,
            'status_code': response.status_code,
            'detail': response.data.get('detail', response.data)
            if isinstance(response.data, dict) else response.data,
        }

    return response
