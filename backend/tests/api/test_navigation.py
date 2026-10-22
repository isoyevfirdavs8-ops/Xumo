from django.urls import reverse
from rest_framework.test import APIClient


def test_navigation_public():
    client = APIClient()

    response = client.get(reverse("site-navigation"))

    assert response.status_code == 200
    assert response.data["brand"]["name"] == "FC BUKHARA"


def test_navigation_links():
    client = APIClient()

    response = client.get(reverse("site-navigation"))

    navigation = response.data["navigation"]
    paths = [item["path"] for item in navigation]

    assert "/" in paths
    assert "/services" in paths


def test_navigation_cart_and_profile():
    client = APIClient()

    response = client.get(reverse("site-navigation"))

    assert response.data["actions"]["cart"] == "/cart"
    assert response.data["actions"]["profile"] == "/profile"