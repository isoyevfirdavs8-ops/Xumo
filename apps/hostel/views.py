
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HostelRoom, HostelRoomImage
from .permissions import IsHostelStaff
from .serializers import (
    HostelRoomSerializer,
    HostelRoomImageSerializer,
    HostelRoomImageUploadSerializer,
)


class HostelRoomDashboardListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsHostelStaff]
    serializer_class = HostelRoomSerializer

    def get_queryset(self):
        return HostelRoom.objects.prefetch_related("images").all()


class HostelRoomDashboardDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsHostelStaff]
    serializer_class = HostelRoomSerializer

    def get_queryset(self):
        return HostelRoom.objects.prefetch_related("images").all()


class HostelRoomImageUploadView(APIView):
    permission_classes = [IsHostelStaff]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, pk):
        room = get_object_or_404(HostelRoom, pk=pk)

        serializer = HostelRoomImageUploadSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        is_primary = serializer.validated_data.get(
            "is_primary", False
        )

        if is_primary:
            HostelRoomImage.objects.filter(
                room=room,
                is_primary=True,
            ).update(is_primary=False)

        image = serializer.save(room=room)

        return Response(
            HostelRoomImageSerializer(
                image,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class HostelRoomImageDeleteView(APIView):
    permission_classes = [IsHostelStaff]

    def delete(self, request, pk, image_id):
        image = get_object_or_404(
            HostelRoomImage,
            pk=image_id,
            room_id=pk,
        )
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HostelRoomImagePrimaryView(APIView):
    permission_classes = [IsHostelStaff]

    @transaction.atomic
    def post(self, request, pk, image_id):
        room = get_object_or_404(HostelRoom, pk=pk)

        image = get_object_or_404(
            HostelRoomImage,
            pk=image_id,
            room=room,
        )

        HostelRoomImage.objects.filter(
            room=room,
            is_primary=True,
        ).update(is_primary=False)

        image.is_primary = True
        image.save(update_fields=["is_primary"])

        return Response(
            HostelRoomImageSerializer(
                image,
                context={"request": request},
            ).data
        )

