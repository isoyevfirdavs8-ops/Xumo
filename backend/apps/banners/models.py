
from django.db import models
from django.core.validators import FileExtensionValidator


class Banner(models.Model):
    title = models.CharField(max_length=200)

    subtitle = models.TextField(
        blank=True
    )

    image = models.ImageField(
        upload_to="banners/desktop/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ],
    )

    mobile_image = models.ImageField(
        upload_to="banners/mobile/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ],
    )

    button_text = models.CharField(
        max_length=100,
        blank=True
    )

    button_url = models.CharField(
        max_length=255,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    sort_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title
