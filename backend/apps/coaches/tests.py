
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase

from apps.categories.models import Category
from .models import Coach


User = get_user_model()


class CoachAPITests(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Futbol",
            slug="football",
            image="categories/football.jpg",
            is_active=True,
        )

        self.coach = Coach.objects.create(
            category=self.category,
            full_name="Test Murabbiy",
            specialization="Futbol",
            experience_years=8,
            image="coaches/test.jpg",
            is_active=True,
        )

    def test_public_coach_list(self):
        response = self.client.get(
            reverse("public-coach-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["category_name"],
            "Futbol",
        )

    def test_inactive_coach_is_hidden(self):
        self.coach.is_active = False
        self.coach.save()

        response = self.client.get(
            reverse("public-coach-list")
        )

        self.assertEqual(len(response.data), 0)

    def test_category_filter(self):
        response = self.client.get(
            reverse("public-coach-list"),
            {"category": "football"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_cannot_create_coach(self):
        response = self.client.post(
            reverse("dashboard-coach-list"),
            {
                "full_name": "Yangi Murabbiy",
                "category": self.category.id,
            },
        )

        self.assertIn(response.status_code, [401, 403])

    def test_regular_user_cannot_access_dashboard(self):
        user = User.objects.create_user(
            phone_number="+998901112244",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse("dashboard-coach-list")
        )

        self.assertEqual(response.status_code, 403)
