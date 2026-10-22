from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Telefon raqami majburiy")

        extra_fields.pop("username", None)

        user = self.model(
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.ADMIN)

        if extra_fields["is_staff"] is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak")

        if extra_fields["is_superuser"] is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak")

        return self.create_user(phone_number, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        COACH = "coach", "Coach"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Admin"

    username = None

    phone_number = models.CharField(
        max_length=13,
        unique=True,
        db_index=True,
    )

    full_name = models.CharField(max_length=200)

    email = models.EmailField(blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    is_phone_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number