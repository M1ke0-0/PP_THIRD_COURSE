from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from attempts.services import AttemptError, KioskRequiredError


def api_exception_handler(exc, context):
    """Ошибки бизнес-правил превращаются в ответ 400, а запрос не из киоска — в 403."""
    if isinstance(exc, AttemptError):
        code = status.HTTP_403_FORBIDDEN if isinstance(exc, KioskRequiredError) else status.HTTP_400_BAD_REQUEST
        return Response({'detail': str(exc)}, status=code)
    return exception_handler(exc, context)
