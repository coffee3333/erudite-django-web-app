from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from drf_yasg.utils import swagger_auto_schema

from authentication.utils import safe_photo_url
from core.models.submission_model import Submission
from core.models.certificate_model import Certificate
from core.models.course_model import Course
from core.models.challenge_model import Challenge
from authentication.models import User


def _get_course_completion(user, course):
    total = Challenge.objects.filter(topic__course=course).count()
    if total == 0:
        return 0
    passed = (
        Submission.objects
        .filter(user=user, challenge__topic__course=course, status="passed")
        .values("challenge_id").distinct().count()
    )
    return round((passed / total) * 100, 1)


class DashboardView(APIView):
    """
    Returns a complete dashboard snapshot for the authenticated student:
    profile info, aggregated stats (points, rank, challenges), courses in progress,
    earned certificates, and the last 8 submission events.
    Hint and solution-reveal sentinel submissions are excluded from all stats.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Profile"], operation_summary="Get authenticated user's dashboard stats",
        operation_description=(
            "Returns a complete dashboard snapshot for the authenticated student.\n\n"
            "**Sections:**\n\n"
            "- **`profile`** — username, email, photo, role, bio, email_verified, date_joined, moodle_platform\n"
            "- **`stats`** — aggregated performance metrics:\n"
            "  - `total_points` — sum of best scores across all passed challenges\n"
            "  - `challenges_passed` — distinct challenges the student has passed\n"
            "  - `challenges_attempted` — distinct challenges attempted (passed or failed)\n"
            "  - `total_attempts` — total submission count (includes retries)\n"
            "  - `certificates_earned` — number of course certificates\n"
            "  - `rank` — position among all users by total points (1 = highest)\n"
            "- **`courses`** — courses the student has submitted in, sorted: in-progress first, "
            "then completed, then not started. Each entry includes `completion_pct` and `certificate_earned`.\n"
            "- **`certificates`** — list of earned certificates with `course_title`, `issued_at`, `score_pct`\n"
            "- **`recent_activity`** — last 8 submissions with challenge/course info and score\n\n"
            "Hint and solution-reveal events are excluded from all stats."
        )
    )
    def get(self, request):
        user = request.user

        # ── Points & challenge stats ──────────────────────────────────────────
        # Exclude sentinel submissions created by hint/solution-reveal events
        submissions_qs = Submission.objects.filter(user=user).exclude(
            answer_text__in=["__hint_used__", "__solution_revealed__"]
        )

        total_points = (
            submissions_qs
            .filter(status="passed")
            .values("challenge_id").distinct()  # best per challenge
            .aggregate(pts=Sum("score"))["pts"] or 0
        )

        challenges_passed = (
            submissions_qs.filter(status="passed")
            .values("challenge_id").distinct().count()
        )
        challenges_attempted = (
            submissions_qs.values("challenge_id").distinct().count()
        )
        total_attempts = submissions_qs.count()

        # ── Certificates ──────────────────────────────────────────────────────
        certs = Certificate.objects.filter(user=user).select_related("course").order_by("-issued_at")
        certificates = [
            {
                "course_title": c.course.title,
                "course_slug": c.course.slug,
                "issued_at": c.issued_at,
                "score_pct": c.score_pct,
            }
            for c in certs
        ]

        # ── Courses in progress ───────────────────────────────────────────────
        # Courses the user has at least one submission in
        touched_course_ids = (
            submissions_qs
            .values_list("challenge__topic__course_id", flat=True)
            .distinct()
        )
        courses_qs = (
            Course.objects
            .filter(id__in=touched_course_ids, status__in=["published", "private"])
            .select_related("owner")
        )
        courses_progress = []
        for course in courses_qs:
            pct = _get_course_completion(user, course)
            has_cert = certs.filter(course=course).exists()
            courses_progress.append({
                "title": course.title,
                "slug": course.slug,
                "owner": course.owner.username,
                "featured_image": course.featured_image.url if course.featured_image else None,
                "completion_pct": pct,
                "certificate_earned": has_cert,
            })
        # Sort: in-progress first (not 0, not 100), then completed, then not started
        courses_progress.sort(key=lambda c: (
            0 if 0 < c["completion_pct"] < 100 else
            1 if c["completion_pct"] == 100 else 2
        ))

        # ── Rank (by total points among all users) ────────────────────────────
        users_ahead = (
            Submission.objects
            .filter(status="passed")
            .values("user_id", "challenge_id")
            .distinct()
            .values("user_id")
            .annotate(pts=Sum("score"))
            .filter(pts__gt=total_points)
            .count()
        )
        rank = users_ahead + 1

        # ── Recent activity (last 8 submissions) ──────────────────────────────
        recent = (
            submissions_qs
            .select_related("challenge", "challenge__topic__course")
            .order_by("-created_at")[:8]
        )
        recent_activity = [
            {
                "challenge_title": s.challenge.title,
                "challenge_slug": s.challenge.slug,
                "course_title": s.challenge.topic.course.title,
                "topic_slug": s.challenge.topic.slug,
                "status": s.status,
                "score": s.score,
                "created_at": s.created_at,
            }
            for s in recent
        ]

        return Response({
            "profile": {
                "username": user.username,
                "email": user.email,
                "photo": safe_photo_url(user),
                "role": user.role,
                "user_bio": user.user_bio,
                "email_verified": user.email_verified,
                "date_joined": user.date_joined,
                "moodle_platform": user.moodle_platform or None,
            },
            "stats": {
                "total_points": round(total_points),
                "challenges_passed": challenges_passed,
                "challenges_attempted": challenges_attempted,
                "total_attempts": total_attempts,
                "certificates_earned": len(certificates),
                "rank": rank,
            },
            "courses": courses_progress,
            "certificates": certificates,
            "recent_activity": recent_activity,
        })
