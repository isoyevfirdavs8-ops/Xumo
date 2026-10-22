
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="categories/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ],
    )

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name







class SubCategory(models.Model):
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="subcategories",
    )

    name = models.CharField(max_length=150)

    slug = models.SlugField(
        max_length=180,
        blank=True,
        null=True,
    )

    description = models.TextField(
        blank=True,
    )

    image = models.ImageField(
        upload_to="subcategories/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "slug"],
                name="unique_subcategory_slug_per_category",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.name or not self.name.strip():
            raise ValidationError({
                "name": "Subkategoriya nomini kiriting."
            })

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                self.name,
                allow_unicode=True,
            )

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} / {self.name}"
