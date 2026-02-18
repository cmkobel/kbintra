"""
Views for Announcements app.
"""

from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Announcement, AnnouncementReaction
from .serializers import AnnouncementCreateSerializer, AnnouncementSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit/delete."""

    def has_object_permission(self, request: Any, view: Any, obj: Announcement) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class AnnouncementListCreateView(generics.ListCreateAPIView):
    """List all announcements or create a new one."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self) -> type:
        if self.request.method == "POST":
            return AnnouncementCreateSerializer
        return AnnouncementSerializer

    def get_queryset(self) -> Any:
        # By default only show active announcements
        queryset = Announcement.objects.select_related("author").prefetch_related(
            "attachments__uploaded_by", "reactions"
        )
        # Allow filtering by is_active
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        else:
            queryset = queryset.filter(is_active=True)
        return queryset


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an announcement."""

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Announcement.objects.select_related("author").prefetch_related(
        "attachments__uploaded_by", "reactions"
    )

    def get_serializer_class(self) -> type:
        if self.request.method in ["PUT", "PATCH"]:
            return AnnouncementCreateSerializer
        return AnnouncementSerializer


class AnnouncementReactionToggleView(APIView):
    """Toggle a reaction on an announcement."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, announcement_id: int) -> Response:
        """Add or remove a reaction from an announcement."""
        announcement = get_object_or_404(Announcement, pk=announcement_id)
        reaction_type = request.data.get("reaction_type")

        valid_types = [choice[0] for choice in AnnouncementReaction.REACTION_CHOICES]
        if reaction_type not in valid_types:
            return Response(
                {"detail": f"Invalid reaction type. Must be one of: {valid_types}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = AnnouncementReaction.objects.filter(
            announcement=announcement, user=request.user, reaction_type=reaction_type
        ).first()

        if existing:
            existing.delete()
            return Response(
                {"detail": "Reaction removed.", "action": "removed"},
                status=status.HTTP_200_OK,
            )
        else:
            AnnouncementReaction.objects.create(
                announcement=announcement, user=request.user, reaction_type=reaction_type
            )
            return Response(
                {"detail": "Reaction added.", "action": "added"},
                status=status.HTTP_201_CREATED,
            )
