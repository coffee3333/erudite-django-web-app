from rest_framework import serializers
from django.utils.text import slugify
from django.db.models import Avg
from core.models.course_model import Course
from core.models.certificate_model import Certificate
from core.models.challenge_model import Challenge
from core.models.submission_model import Submission
from core.serializers.topic_serializer import TopicSerializer


def _get_completion_pct(user, course):
    total = Challenge.objects.filter(topic__course=course).count()
    if total == 0:
        return 0
    passed = (
        Submission.objects
        .filter(user=user, challenge__topic__course=course, status="passed")
        .values("challenge_id").distinct().count()
    )
    return round((passed / total) * 100, 1)


class CourseListSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    completion_pct = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "owner",
            "title",
            "description",
            "language",
            "level",
            "status",
            "featured_image",
            "created_at",
            "slug",
            "completion_pct",
            "certificate",
            "is_bookmarked",
        ]

    def get_completion_pct(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return _get_completion_pct(request.user, obj)

    def get_certificate(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        cert = Certificate.objects.filter(user=request.user, course=obj).first()
        if not cert:
            return None
        return {
            "certificate_id": str(cert.certificate_id),
            "issued_at": cert.issued_at,
            "score_pct": cert.score_pct,
            "pdf_download_url": request.build_absolute_uri(f"/api/platform/courses/{obj.slug}/certificate/download/"),
        }

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()

class CourseDetailSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    completion_pct = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "owner",
            "title",
            "description",
            "language",
            "level",
            "status",
            "featured_image",
            "created_at",
            "updated_at",
            "slug",
            "lti_token",
            "completion_pct",
            "certificate",
            "is_bookmarked",
            "avg_rating",
            "feedback_count",
        ]

    def get_completion_pct(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return _get_completion_pct(request.user, obj)

    def get_certificate(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        cert = Certificate.objects.filter(user=request.user, course=obj).first()
        if not cert:
            return None
        return {
            "certificate_id": str(cert.certificate_id),
            "issued_at": cert.issued_at,
            "score_pct": cert.score_pct,
            "pdf_download_url": request.build_absolute_uri(f"/api/platform/courses/{obj.slug}/certificate/download/"),
        }

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.bookmarks.filter(user=request.user).exists()

    def get_avg_rating(self, obj):
        result = obj.feedback.aggregate(avg=Avg("rating"))["avg"]
        return round(result, 1) if result is not None else None

    def get_feedback_count(self, obj):
        return obj.feedback.count()

class CourseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "title",
            "description",
            "language",
            "level",
            "status",
            "featured_image",
        )
        ref_name = "CourseUpdateSerializer"
        extra_kwargs = {
            "title": {"required": False},
            "description": {"required": False},
            "language": {"required": False},
            "level": {"required": False},
            "status": {"required": False},
            "featured_image": {"required": False},
        }

    # ---------- VALIDATIONS ----------

    def validate_featured_image(self, value):
        """Validate uploaded image size and format."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("Image size must not exceed 5MB.")
            if not value.name.lower().endswith((".png", ".jpg", ".jpeg")):
                raise serializers.ValidationError("Only PNG and JPEG images are allowed.")
        return value

    def validate_status(self, value):
        """Validate course status."""
        allowed_statuses = ["draft", "published", "archived", "private"]
        if not value:
            raise serializers.ValidationError("Status is required.")
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Status must be one of {', '.join(allowed_statuses)}."
            )
        return value

    def validate_level(self, value):
        """Validate course level."""
        allowed_levels = ["beginner", "intermediate", "advanced"]
        if value and value not in allowed_levels:
            raise serializers.ValidationError(
                f"Level must be one of {', '.join(allowed_levels)}."
            )
        return value

    # ---------- UPDATE LOGIC ----------

    def update(self, instance, validated_data):
        has_updates = False

        current_data = {
            "title": instance.title,
            "description": instance.description,
            "language": instance.language,
            "level": instance.level,
            "status": instance.status,
            "featured_image": instance.featured_image,
        }

        if "title" in validated_data and validated_data["title"] != instance.title:
            instance.title = validated_data["title"]
            has_updates = True

        if "description" in validated_data and validated_data["description"] != instance.description:
            instance.description = validated_data["description"]
            has_updates = True

        if "language" in validated_data and validated_data["language"] != instance.language:
            instance.language = validated_data["language"]
            has_updates = True

        if "level" in validated_data and validated_data["level"] != instance.level:
            instance.level = validated_data["level"]
            has_updates = True

        if "status" in validated_data and validated_data["status"] != instance.status:
            instance.status = validated_data["status"]
            has_updates = True

        if "featured_image" in validated_data:
            new_image = validated_data.get("featured_image")

            if new_image is None:
                if instance.featured_image:
                    instance.featured_image.delete(save=False)
                    instance.featured_image = None
                    has_updates = True

            elif new_image != instance.featured_image:
                instance.featured_image = new_image
                has_updates = True

        if has_updates:
            instance.save()

        serializer = self.__class__(instance)
        return serializer.data, has_updates

class CourseCreateSerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = (
            "title",
            "description",
            "language",
            "level",
            "status",
            "featured_image",
            "slug",
        )
        ref_name = "CourseCreateSerializer"

    # ---------- VALIDATIONS ----------

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Course title cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_featured_image(self, value):
        """Validate uploaded image size and format."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("Image size must not exceed 5MB.")
            if not value.name.lower().endswith((".png", ".jpg", ".jpeg")):
                raise serializers.ValidationError("Only PNG and JPEG images are allowed.")
        return value

    def validate_status(self, value):
        """Validate course status."""
        allowed_statuses = ["draft", "published", "archived", "private"]
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Status must be one of {', '.join(allowed_statuses)}."
            )
        return value

    def validate_level(self, value):
        """Validate difficulty level."""
        allowed_levels = ["beginner", "intermediate", "advanced"]
        if value not in allowed_levels:
            raise serializers.ValidationError(
                f"Level must be one of {', '.join(allowed_levels)}."
            )
        return value

    # ---------- CREATE LOGIC ----------

    def create(self, validated_data):
        """Create course and auto-generate slug if needed."""
        title = validated_data.get("title")
        base_slug = slugify(title)
        slug = base_slug or "course"
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        validated_data["slug"] = slug
        return super().create(validated_data)
