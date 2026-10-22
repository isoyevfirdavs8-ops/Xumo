from rest_framework import generics, permissions
from apps.dashboard.permissions import IsDashboardAdmin
from .models import AboutItem
from .serializers import AboutItemSerializer


class AboutPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and IsDashboardAdmin().has_permission(request, view))


class AboutListCreateView(generics.ListCreateAPIView):
    queryset = AboutItem.objects.all()
    serializer_class = AboutItemSerializer
    permission_classes = [AboutPermission]
    pagination_class = None


class AboutDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AboutItem.objects.all()
    serializer_class = AboutItemSerializer
    permission_classes = [AboutPermission]
    http_method_names = ('get', 'patch', 'delete', 'head', 'options')
