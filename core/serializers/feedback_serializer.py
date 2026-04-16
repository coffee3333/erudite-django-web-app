from rest_framework import serializers
from core.models.feedback_model import CourseFeedback


class CourseFeedbackSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    photo = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()

    class Meta:
        model = CourseFeedback
        fields = ["id", "username", "photo", "rating", "comment", "created_at", "updated_at", "is_own"]
        read_only_fields = ["id", "username", "photo", "created_at", "updated_at", "is_own"]

    def get_photo(self, obj):
        try:
            return obj.user.photo.url if obj.user.photo else None
        except Exception:
            return None

    def get_is_own(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user
