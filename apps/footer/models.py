from django.db import models


class FooterSettings(models.Model):
    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
    )

    brand_name = models.CharField(
        max_length=100,
        default="FC BUKHARA",
    )
    description = models.TextField(
        blank=True,
        default=(
            "Sport, sog‘lom turmush va mazmunli hordiq "
            "uchun zamonaviy imkoniyatlar."
        ),
    )

    phone = models.CharField(max_length=30, blank=True)
    phone_2 = models.CharField(max_length=30, blank=True)
    phone_3 = models.CharField(max_length=30, blank=True)
    phone_4 = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    working_hours = models.CharField(max_length=150, blank=True)

    telegram_url = models.URLField(max_length=500, blank=True)
    facebook_url = models.URLField(max_length=500, blank=True)
    instagram_url = models.URLField(max_length=500, blank=True)

    copyright_text = models.CharField(
        max_length=255,
        blank=True,
        default="Barcha huquqlar himoyalangan.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "FC BUKHARA — Footer sozlamalari"

    class Meta:
        verbose_name = "Footer sozlamasi"
        verbose_name_plural = "Footer sozlamalari"