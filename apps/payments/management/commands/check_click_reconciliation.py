
import json

from django.core.management.base import BaseCommand

from apps.payments.click_reconciliation import (
    get_click_reconciliation_summary,
)


class Command(BaseCommand):
    help = (
        "Report stale Click PREPARED transactions "
        "without changing payment state."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=15,
        )

    def handle(self, *args, **options):
        try:
            summary = get_click_reconciliation_summary(
                older_than_minutes=options["minutes"]
            )
        except ValueError as exc:
            from django.core.management.base import CommandError
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            json.dumps(summary, ensure_ascii=False)
        )
