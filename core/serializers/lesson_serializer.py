from rest_framework import serializers
from core.models.lesson import Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id", "slug", "title", "content", "video_url",
            "content_type", "photo", "sort_order", "estimated_minutes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
        extra_kwargs = {
            "content": {"required": False},
            "video_url": {"required": False},
            "content_type": {"required": False},
            "sort_order": {"required": False},
            "estimated_minutes": {"required": False},
        }
