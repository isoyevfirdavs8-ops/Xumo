from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.restaurant_orders.models import RestaurantOrder
from apps.restaurant_orders.services import expire_restaurant_order


class Command(BaseCommand):
    help = "Muddati tugagan restoran buyurtmalarini yopish"

    def handle(self, *args, **options):
        ids = (
            RestaurantOrder.objects.filter(
                status=RestaurantOrder.Status.PENDING,
                expires_at__lte=timezone.now(),
            )
            .values_list("pk", flat=True)
            .iterator(chunk_size=200)
        )

        count = 0

        for order_id in ids:
            if expire_restaurant_order(order_id):
                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} ta buyurtma yopildi."
            )
        )