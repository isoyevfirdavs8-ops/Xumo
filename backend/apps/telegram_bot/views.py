import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .callbacks import process_order_callback


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    )

    if not settings.TELEGRAM_WEBHOOK_SECRET:
        return JsonResponse({"detail": "Not configured"}, status=503)

    if secret != settings.TELEGRAM_WEBHOOK_SECRET:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    import json

    try:
        update = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    callback = update.get("callback_query")

    if callback:
        try:
            process_order_callback(callback)
        except Exception:
            logger.exception("Telegram callback failed")
            return JsonResponse({"ok": False}, status=500)

    return JsonResponse({"ok": True})