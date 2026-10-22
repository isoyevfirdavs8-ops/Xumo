
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Food(models.Model):
    subcategory = models.ForeignKey(
        "categories.SubCategory",
        on_delete=models.PROTECT,
        related_name="foods",
    )

    name = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="foods/",
        blank=True,
        null=True,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(
                fields=["subcategory", "is_active"],
            ),
        ]

    def clean(self):
        super().clean()

        if not self.name or not self.name.strip():
            raise ValidationError({
                "name": "Taom nomini kiriting."
            })

    def __str__(self):
        return self.name
