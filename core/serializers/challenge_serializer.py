from rest_framework import serializers
from core.models.challenge_model import Challenge
from core.models.topic_model import Topic
from core.models.challenge_correct_answer import ChallengeCorrectAnswer
from core.models.challenge_option import ChallengeOption
from django.shortcuts import get_object_or_404
import json
import re

class ChallengeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ["id", "title", "slug"]


class ChallengeCorrectAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeCorrectAnswer
        fields = ["correct_answer", "case_sensitive"]


class ChallengeSerializer(serializers.ModelSerializer):
    topic_slug = serializers.SlugField(write_only=True)
    answers = serializers.CharField(write_only=True, required=False, allow_blank=True)
    correct_answer = serializers.CharField(write_only=True)
    case_sensitive = serializers.BooleanField(write_only=True, required=False, default=False)

    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Challenge
        fields = [
            "id", "title", "body", "points", "difficulty", "photo",
            "slug", "topic_slug", "answers", "correct_answer", "case_sensitive",
        ]
        read_only_fields = ["id", "slug"]

    def validate(self, attrs):
        answers_list = [x.strip() for x in attrs.get("answers").split(",")]
        attrs["_answers_list"] = answers_list

        correct_answer = str(attrs.get("correct_answer", "")).strip()
        if not correct_answer:
            raise serializers.ValidationError({"correct_answer": "This field is required."})

        case_sensitive = bool(attrs.get("case_sensitive", False))

        if answers_list:
            if case_sensitive:
                ok = correct_answer in answers_list
            else:
                ok = correct_answer.lower() in [a.lower() for a in answers_list]
            if not ok:
                raise serializers.ValidationError({
                    "correct_answer": f"'{correct_answer}' is not in answers list."
                })

        topic_slug = attrs.get("topic_slug")
        if not topic_slug:
            raise serializers.ValidationError({"topic_slug": "This field is required."})
        if not Topic.objects.filter(slug=topic_slug).exists():
            raise serializers.ValidationError({"topic_slug": f"Topic with slug '{topic_slug}' does not exist."})

        attrs["_correct_answer"] = correct_answer
        attrs["_case_sensitive"] = case_sensitive
        return attrs

    def create(self, validated_data):
        topic = get_object_or_404(Topic, slug=validated_data.pop("topic_slug"))

        answers_list = validated_data.pop("_answers_list", [])
        correct_answer = validated_data.pop("_correct_answer")
        case_sensitive = validated_data.pop("_case_sensitive", False)

        for junk in ["answers", "correct_answer", "case_sensitive",
                     "_answers_list", "_correct_answer", "_case_sensitive"]:
            validated_data.pop(junk, None)

        challenge = Challenge.objects.create(topic=topic, **validated_data)

        if answers_list:
            ChallengeOption.objects.bulk_create([
                ChallengeOption(challenge=challenge, text=a) for a in answers_list
            ])

        ChallengeCorrectAnswer.objects.create(
            challenge=challenge,
            correct_answer=correct_answer,
            case_sensitive=case_sensitive,
        )
        return challenge


class ChallengeListSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id", "title", "body",
            "points", "difficulty", "photo",
            "slug",
            "options",
        ]

    def get_options(self, obj):
        return list(obj.options.values_list("text", flat=True).order_by("id"))