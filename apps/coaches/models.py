
from django.db import models
from django.core.validators import MinValueValidator
from apps.categories.models import Category
from django.conf import settings


class Coach(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="coaches",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coach_profile",
    )

    boxing_academies = models.ManyToManyField(
        "boxing.BoxingAcademy",
        blank=True,
        related_name="assigned_coaches",
    )

    tennis_courts = models.ManyToManyField(
        "tennis.TennisCourt",
        blank=True,
        related_name="assigned_coaches",
    )

    full_name = models.CharField(max_length=160)
    specialization = models.CharField(max_length=160)
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to="coaches/")

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.full_name
