from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/site/", include("apps.core.urls")),
    path("api/v1/", include("apps.banners.urls")),
    path("api/v1/", include("apps.categories.urls")),
    path("api/v1/", include("apps.coaches.urls")),
    path("api/v1/", include("apps.competitions.urls")),
    path("api/v1/", include("apps.foods.urls")),
    path("api/v1/",include("apps.restaurant_orders.urls")),
    path("api/v1/", include("apps.footer.urls")),
    path("api/v1/football/",include("apps.football.urls")),
    path("api/v1/tennis/",include("apps.tennis.urls")),
    path("api/v1/boxing/",include("apps.boxing.urls")),
    path("api/v1/finance/",include("apps.finance.urls")),
    path("api/v1/payments/",include("apps.payments.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/site/about/",include("apps.about.urls")),
    path("api/v1/telegram/",include("apps.telegram_bot.urls")),
    path("api/v1/attendance/",include("apps.attendance.urls")),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

