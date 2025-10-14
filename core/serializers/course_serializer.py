from rest_framework import serializers
from django.utils.text import slugify
from core.models.course_model import Course

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
        allowed_statuses = ["draft", "published", "archived"]
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

        if "featured_image" in validated_data and validated_data["featured_image"] != instance.featured_image:
            instance.featured_image = validated_data["featured_image"]
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
        allowed_statuses = ["draft", "published", "archived"]
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
        request = self.context.get("request")

        title = validated_data.get("title")
        base_slug = slugify(title)
        slug = base_slug or "course"
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        course = Course.objects.create(
            slug=slug,
            **validated_data
        )

        return course
