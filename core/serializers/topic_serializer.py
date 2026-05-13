from rest_framework import serializers
from core.models.topic_model import Topic


class TopicSerializer(serializers.ModelSerializer):
    challenge_count = serializers.SerializerMethodField()
    completion_pct = serializers.SerializerMethodField()

    def get_challenge_count(self, topic):
        return topic.challenges.count()

    def get_completion_pct(self, topic):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        total = topic.challenges.count()
        if total == 0:
            return None
        passed = topic.challenges.filter(
            submissions__user=request.user,
            submissions__status="passed",
        ).distinct().count()
        return round((passed / total) * 100)

    class Meta:
        model = Topic
        fields = ["id", "slug", "title", "description", "sort_order", "challenge_count", "completion_pct"]
        read_only_fields = ["id", "slug"]
        extra_kwargs = {
            "description": {"required": False},
            "sort_order": {"required": False},
        }


class TopicDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    owner = serializers.CharField(source="owner.username", read_only=True)

    def _user_status(self, challenge, request):
        """
        Returns the authenticated user's best submission status for a challenge.
        Priority: passed > failed > pending > null (never attempted).
        """
        if not request or not request.user.is_authenticated:
            return None
        submissions = challenge.submissions.filter(user=request.user)
        if submissions.filter(status="passed").exists():
            return "passed"
        if submissions.filter(status="failed").exists():
            return "failed"
        if submissions.filter(status="pending").exists():
            return "pending"
        return None

    def get_items(self, topic):
        request = self.context.get("request")

        lessons = [
            {
                "type":               "lesson",
                "slug":               l.slug,
                "title":              l.title,
                "sort_order":         l.sort_order,
                "content_type":       l.content_type,
                "content":            l.content,
                "video_url":          l.video_url,
                "photo":              request.build_absolute_uri(l.photo.url) if (request and l.photo) else None,
                "estimated_minutes":  l.estimated_minutes,
                # challenge-only — always null on lessons
                "challenge_type":     None,
                "points":             None,
                "difficulty":         None,
                "user_status":        None,
                "code_language":      None,
            }
            for l in topic.lessons.all()
        ]

        challenges = [
            {
                "type":               "challenge",
                "slug":               c.slug,
                "title":              c.title,
                "sort_order":         c.sort_order,
                "challenge_type":     c.challenge_type,
                "points":             c.points,
                "difficulty":         c.difficulty,
                "user_status":        self._user_status(c, request),
                "code_language":      (
                    c.code_config.language
                    if c.challenge_type == "code" and hasattr(c, "code_config")
                    else None
                ),
                # lesson-only — always null on challenges
                "content_type":       None,
                "content":            None,
                "video_url":          None,
                "estimated_minutes":  None,
            }
            for c in topic.challenges.all()
        ]

        return sorted(lessons + challenges, key=lambda x: x["sort_order"])

    class Meta:
        model = Topic
        fields = ["id", "slug", "title", "description", "owner", "items"]
