from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Prefetch
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from authentication.utils import safe_photo_url
from core.models.submission_model import Submission
from core.models.course_model import Course
from core.models.challenge_model import Challenge
from authentication.models import User
from core.permissions import IsTeacherUser


class TeacherDashboardView(APIView):
    """
    Returns per-course student performance for the authenticated teacher.

    For each course the teacher owns, returns:
    - course meta (title, slug, level, total_challenges)
    - list of students who have at least one submission in the course, with:
        - username, email, photo
        - challenges_passed, challenges_attempted, total_points (in this course)
        - completion_pct
        - per_challenge status list (id, title, status: passed|failed|not_attempted)
    """
    permission_classes = [IsAuthenticated, IsTeacherUser]

    @swagger_auto_schema(
        tags=["Profile"],
        operation_summary="Get teacher's per-course student performance",
        operation_description=(
            "Returns performance data for every course owned by the authenticated teacher.\n\n"
            "For each course:\n"
            "- Course meta: `title`, `slug`, `level`, `status`, `featured_image`, `total_challenges`\n"
            "- `student_count` — number of students who have at least one real submission\n"
            "- `students` — list sorted by completion (highest first), each entry contains:\n"
            "  - `username`, `email`, `photo`, `moodle_platform`\n"
            "  - `challenges_passed`, `challenges_attempted`, `total_points`, `completion_pct`\n"
            "  - `per_challenge` — one entry per challenge with `id`, `title`, `points`, `difficulty`, "
            "`status` (`passed` / `failed` / `not_attempted`), `score`\n\n"
            "Only the **best result per challenge** per student is counted. "
            "Hint-use and solution-reveal events are excluded from all counts."
        ),
        responses={
            200: openapi.Response(
                description="Per-course student performance",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "courses": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "title":            openapi.Schema(type=openapi.TYPE_STRING),
                                    "slug":             openapi.Schema(type=openapi.TYPE_STRING),
                                    "level":            openapi.Schema(type=openapi.TYPE_STRING),
                                    "status":           openapi.Schema(type=openapi.TYPE_STRING),
                                    "total_challenges": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "student_count":    openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "students": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "username":            openapi.Schema(type=openapi.TYPE_STRING),
                                                "email":               openapi.Schema(type=openapi.TYPE_STRING),
                                                "challenges_passed":   openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "challenges_attempted":openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "total_points":        openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "completion_pct":      openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "per_challenge": openapi.Schema(
                                                    type=openapi.TYPE_ARRAY,
                                                    items=openapi.Schema(
                                                        type=openapi.TYPE_OBJECT,
                                                        properties={
                                                            "id":         openapi.Schema(type=openapi.TYPE_INTEGER),
                                                            "title":      openapi.Schema(type=openapi.TYPE_STRING),
                                                            "points":     openapi.Schema(type=openapi.TYPE_INTEGER),
                                                            "difficulty": openapi.Schema(type=openapi.TYPE_STRING),
                                                            "status":     openapi.Schema(type=openapi.TYPE_STRING, enum=["passed", "failed", "not_attempted"]),
                                                            "score":      openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        },
                                                    ),
                                                ),
                                            },
                                        ),
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            ),
            401: openapi.Response(description="Not authenticated"),
            403: openapi.Response(description="Not a teacher"),
        },
    )
    def get(self, request):
        teacher = request.user

        courses = (
            Course.objects
            .filter(owner=teacher)
            .prefetch_related(
                Prefetch(
                    "topics__challenges",
                    queryset=Challenge.objects.order_by("sort_order", "id"),
                )
            )
            .order_by("-created_at")
        )

        result = []

        for course in courses:
            # Collect all challenges flat
            challenges = []
            for topic in course.topics.all():
                for ch in topic.challenges.all():
                    challenges.append(ch)

            total_challenges = len(challenges)
            challenge_ids = [ch.id for ch in challenges]

            # Find all students who submitted at least once in this course
            student_ids = (
                Submission.objects
                .filter(challenge_id__in=challenge_ids)
                .exclude(user=teacher)
                .exclude(answer_text__in=["__hint_used__", "__solution_revealed__"])
                .values_list("user_id", flat=True)
                .distinct()
            )

            students_data = []

            for student in User.objects.filter(id__in=student_ids).order_by("username"):
                subs = (
                    Submission.objects
                    .filter(user=student, challenge_id__in=challenge_ids)
                    .exclude(answer_text__in=["__hint_used__", "__solution_revealed__"])
                    .values("challenge_id", "status", "score")
                    .order_by("challenge_id", "-score")  # best score first
                )

                # Best result per challenge
                best_per_challenge = {}
                for s in subs:
                    cid = s["challenge_id"]
                    if cid not in best_per_challenge:
                        best_per_challenge[cid] = s
                    else:
                        # Prefer passed over failed; higher score wins
                        existing = best_per_challenge[cid]
                        if s["status"] == "passed" and existing["status"] != "passed":
                            best_per_challenge[cid] = s
                        elif s["status"] == existing["status"] and s["score"] > existing["score"]:
                            best_per_challenge[cid] = s

                passed_ids = {cid for cid, s in best_per_challenge.items() if s["status"] == "passed"}
                attempted_ids = set(best_per_challenge.keys())

                total_points = sum(
                    s["score"] for s in best_per_challenge.values() if s["status"] == "passed"
                )

                completion_pct = round((len(passed_ids) / total_challenges) * 100) if total_challenges else 0

                per_challenge = []
                for ch in challenges:
                    if ch.id in passed_ids:
                        status = "passed"
                    elif ch.id in attempted_ids:
                        status = "failed"
                    else:
                        status = "not_attempted"
                    per_challenge.append({
                        "id": ch.id,
                        "title": ch.title,
                        "points": ch.points,
                        "difficulty": ch.difficulty,
                        "status": status,
                        "score": round(best_per_challenge[ch.id]["score"]) if ch.id in best_per_challenge else 0,
                    })

                students_data.append({
                    "username": student.username,
                    "email": student.email,
                    "photo": safe_photo_url(student),
                    "moodle_platform": student.moodle_platform or None,
                    "challenges_passed": len(passed_ids),
                    "challenges_attempted": len(attempted_ids),
                    "total_points": round(total_points),
                    "completion_pct": completion_pct,
                    "per_challenge": per_challenge,
                })

            # Sort students: highest completion first
            students_data.sort(key=lambda s: (-s["completion_pct"], -s["total_points"]))

            result.append({
                "title": course.title,
                "slug": course.slug,
                "level": course.level,
                "status": course.status,
                "featured_image": course.featured_image.url if course.featured_image else None,
                "total_challenges": total_challenges,
                "student_count": len(students_data),
                "students": students_data,
            })

        return Response({"courses": result})
