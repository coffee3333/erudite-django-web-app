from rest_framework import serializers
from core.models.topic_model import Topic
from core.serializers.challenge_serializer import ChallengeShortSerializer


class TopicSerializer(serializers.ModelSerializer):
    # challenges = ChallengeShortSerializer(many=True, read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Topic
        fields = ["title", "slug"]