
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase

from .models import Category


User = get_user_model()


class CategoryAPITests(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Football",
            slug="football",
            description="Professional futbol maydoni",
            image="categories/football.jpg",
            is_active=True,
            sort_order=1,
        )

    def test_public_can_list_active_categories(self):
        response = self.client.get(
            reverse("public-category-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_inactive_category_is_hidden(self):
        Category.objects.create(
            name="Hidden",
            slug="hidden",
            image="categories/hidden.jpg",
            is_active=False,
        )

        response = self.client.get(
            reverse("public-category-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_cannot_create_category(self):
        response = self.client.post(
            reverse("dashboard-category-list"),
            {
                "name": "Tennis",
                "slug": "tennis",
            },
        )

        self.assertIn(response.status_code, [401, 403])

    def test_regular_user_cannot_access_dashboard(self):
        user = User.objects.create_user(
            phone_number="+998901112233",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse("dashboard-category-list")
        )

        self.assertEqual(response.status_code, 403)
