import hmac

from django.conf import settings

KIOSK_HEADER = 'X-Exam-Client-Key'


def is_kiosk_request(request):
    """Запрос пришёл из клиента-киоска: в заголовке передан ключ клиента."""
    key = request.headers.get(KIOSK_HEADER, '')
    return bool(settings.EXAM_CLIENT_KEY) and hmac.compare_digest(key, settings.EXAM_CLIENT_KEY)
