from celery import shared_task

from apps.telegram_bot.services import send_paid_order_to_managers


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def notify_restaurant_managers(self, order_id):
    send_paid_order_to_managers(order_id)