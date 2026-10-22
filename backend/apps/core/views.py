
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class SiteNavigationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "brand": {
                "name": "FC BUKHARA",
                "subtitle": "SPORT & LIFESTYLE",
            },
            "navigation": [
                {
                    "label": "Bosh sahifa",
                    "path": "/",
                },
                {
                    "label": "Xizmatlar",
                    "path": "/services",
                },
                {
                    "label": "Musobaqalar",
                    "path": "/competitions",
                },
                {
                    "label": "Biz haqimizda",
                    "path": "/about",
                },
                {
                    "label": "Aloqa",
                    "path": "/#contact",
                },
            ],
            "actions": {
                "cart": "/cart",
                "profile": "/profile",
            },
        })
