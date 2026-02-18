"""
Serializers for Announcements models.
"""

from rest_framework import serializers

from apps.users.models import User

from .models import Announcement, AnnouncementAttachment, AnnouncementReaction


class AuthorSerializer(serializers.ModelSerializer):
    """Minimal serializer for announcement authors."""

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "profile_picture"]


class AnnouncementAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for AnnouncementAttachment model."""

    uploaded_by = AuthorSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = AnnouncementAttachment
        fields = [
            "id",
            "name",
            "file",
            "file_url",
            "uploaded_by",
            "uploaded_at",
        ]

    def get_file_url(self, obj: AnnouncementAttachment) -> str:
        if obj.file:
            return obj.file.url
        return ""


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model."""

    author = AuthorSerializer(read_only=True)
    is_own = serializers.SerializerMethodField()
    attachments = AnnouncementAttachmentSerializer(many=True, read_only=True)
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "content",
            "author",
            "is_active",
            "priority",
            "is_own",
            "attachments",
            "reactions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_is_own(self, obj: Announcement) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False

    def get_reactions(self, obj: Announcement) -> list[dict]:
        """Get reaction summary with counts and user's own reactions."""
        request = self.context.get("request")
        user_id = request.user.id if request and request.user.is_authenticated else None

        reaction_counts: dict[str, dict] = {}
        emoji_map = dict(AnnouncementReaction.REACTION_CHOICES)

        for reaction in obj.reactions.all():
            r_type = reaction.reaction_type
            if r_type not in reaction_counts:
                reaction_counts[r_type] = {
                    "reaction_type": r_type,
                    "emoji": emoji_map.get(r_type, ""),
                    "count": 0,
                    "has_reacted": False,
                    "users": [],
                }
            reaction_counts[r_type]["count"] += 1
            reaction_counts[r_type]["users"].append(
                f"{reaction.user.first_name} {reaction.user.last_name}".strip()
            )
            if user_id and reaction.user_id == user_id:
                reaction_counts[r_type]["has_reacted"] = True

        return list(reaction_counts.values())


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating announcements."""

    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Announcement
        fields = ["title", "content", "is_active", "priority", "attachments"]

    def validate_attachments(self, value: list) -> list:
        from apps.forum.utils import validate_file_size

        for file in value:
            validate_file_size(file)
        return value

    def create(self, validated_data: dict) -> Announcement:
        attachments = validated_data.pop("attachments", [])
        validated_data["author"] = self.context["request"].user
        announcement = super().create(validated_data)

        # Create attachments
        for attachment_file in attachments:
            AnnouncementAttachment.objects.create(
                announcement=announcement,
                uploaded_by=announcement.author,
                file=attachment_file,
                name=attachment_file.name,
            )

        # Send notifications to all users (except author) if announcement is active
        if announcement.is_active:
            from apps.notifications.tasks import notify_new_announcement_task

            notify_new_announcement_task(
                author_id=announcement.author.id,
                announcement_title=announcement.title,
                announcement_id=announcement.id,
                announcement_content=announcement.content or "",
            )

        return announcement
