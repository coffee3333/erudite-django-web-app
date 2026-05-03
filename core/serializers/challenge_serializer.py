from rest_framework import serializers
from core.models.challenge_model import Challenge
from core.models.code_challenge import CodeTestCase, CodeChallengeConfig
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
            "hint", "solution_explanation",
        ]
        read_only_fields = ["id", "slug"]

    def validate(self, attrs):
        raw_answers = attrs.get("answers", "") or ""
        answers_list = [x.strip() for x in raw_answers.split(",") if x.strip()]
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
    code_language = serializers.SerializerMethodField()
    code_template = serializers.SerializerMethodField()
    user_status = serializers.SerializerMethodField()
    hint_available = serializers.SerializerMethodField()
    solution_available = serializers.SerializerMethodField()
    user_hint_used = serializers.SerializerMethodField()
    user_solution_revealed = serializers.SerializerMethodField()
    hint = serializers.SerializerMethodField()
    solution_explanation = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id", "title", "body",
            "points", "difficulty",
            "challenge_type", "sort_order",
            "photo", "slug",
            "options",
            "code_language", "code_template",
            "user_status",
            "hint_available", "solution_available",
            "user_hint_used", "user_solution_revealed",
            "hint", "solution_explanation",
        ]

    def get_options(self, obj):
        return list(obj.options.values("id", "text").order_by("id"))

    def get_code_language(self, obj):
        if obj.challenge_type == "code" and hasattr(obj, "code_config"):
            return obj.code_config.language
        return None

    def get_code_template(self, obj):
        if obj.challenge_type == "code" and hasattr(obj, "code_config"):
            return obj.code_config.solution_template
        return None

    def get_user_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        sentinel_texts = ("__hint_used__", "__solution_revealed__")
        submissions = obj.submissions.filter(user=request.user).exclude(answer_text__in=sentinel_texts)
        if submissions.filter(status="passed").exists():
            return "passed"
        if submissions.filter(status="failed").exists():
            return "failed"
        if submissions.filter(status="pending").exists():
            return "pending"
        return None

    def get_hint_available(self, obj):
        return bool(obj.hint)

    def get_solution_available(self, obj):
        return bool(obj.solution_explanation)

    def _get_user_submission(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return obj.submissions.filter(user=request.user).first()

    def get_user_hint_used(self, obj):
        sub = self._get_user_submission(obj)
        return sub.hint_used if sub else False

    def get_user_solution_revealed(self, obj):
        sub = self._get_user_submission(obj)
        return sub.solution_revealed if sub else False

    def _is_owner(self, obj):
        request = self.context.get("request")
        return request and request.user.is_authenticated and obj.topic.course.owner == request.user

    def get_hint(self, obj):
        return obj.hint if self._is_owner(obj) else None

    def get_solution_explanation(self, obj):
        return obj.solution_explanation if self._is_owner(obj) else None

class CodeTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CodeTestCase
        fields = ["stdin", "expected_stdout", "is_public", "weight", "description"]

class CodeConfigSerializer(serializers.ModelSerializer):
    test_cases = CodeTestCaseSerializer(many=True, write_only=True)

    class Meta:
        model  = CodeChallengeConfig
        fields = ["language", "solution_template", "solution_hidden",
                  "time_limit_seconds", "memory_limit_mb", "test_cases"]

class ChallengeCreateSerializer(serializers.ModelSerializer):
    code_config = CodeConfigSerializer(required=False)

    class Meta:
        model  = Challenge
        fields = ["topic", "title", "body", "difficulty", "points",
                  "challenge_type", "hint", "solution_explanation", "code_config"]

    def validate(self, data):
        if data.get("challenge_type") == "code" and not data.get("code_config"):
            raise serializers.ValidationError(
                {"code_config": "Required when challenge_type is 'code'."}
            )
        return data

    def create(self, validated_data):
        config_data = validated_data.pop("code_config", None)
        test_cases  = config_data.pop("test_cases", []) if config_data else []
        challenge   = Challenge.objects.create(**validated_data)

        if config_data:
            config = CodeChallengeConfig.objects.create(challenge=challenge, **config_data)
            for tc in test_cases:
                CodeTestCase.objects.create(config=config, **tc)

        return challenge