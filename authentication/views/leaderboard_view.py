from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from authentication.models import User
from authentication.utils import safe_photo_url
from core.models.submission_model import Submission


def _user_total_points(user_id):
    """
    Mirrors DashboardView: sum of best scores across distinct passed challenges,
    excluding hint/solution-reveal sentinel submissions.
    """
    return (
        Submission.objects
        .filter(user_id=user_id, status="passed")
        .exclude(answer_text__in=["__hint_used__", "__solution_revealed__"])
        .values("challenge_id").distinct()
        .aggregate(pts=Sum("score"))["pts"] or 0
    )


def _all_users_points():
    """
    Returns a queryset of {user_id, pts} for all STUDENTS with at least one passed
    submission, using the same deduplication as DashboardView.
    Teachers are excluded from the leaderboard.
    """
    student_ids = User.objects.filter(role="student").values_list("id", flat=True)
    return (
        Submission.objects
        .filter(status="passed", user_id__in=student_ids)
        .exclude(answer_text__in=["__hint_used__", "__solution_revealed__"])
        .values("user_id", "challenge_id")
        .distinct()
        .values("user_id")
        .annotate(pts=Sum("score"))
        .order_by("-pts")
    )


class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ranked_qs = list(_all_users_points())

        user_ids = [r["user_id"] for r in ranked_qs]
        users_by_id = {
            u.id: u
            for u in User.objects.filter(id__in=user_ids).only("id", "username", "photo", "role")
        }

        me = request.user if request.user.is_authenticated else None

        # Build ranked list (top 10), flag current user inline
        leaderboard = []
        me_in_top10 = False
        for i, row in enumerate(ranked_qs[:10]):
            user = users_by_id.get(row["user_id"])
            if not user:
                continue
            is_me = me is not None and user.id == me.id
            if is_me:
                me_in_top10 = True
            entry = {
                "rank": i + 1,
                "username": user.username,
                "photo": safe_photo_url(user),
                "total_points": round(row["pts"]),
            }
            if is_me:
                entry["is_current_user"] = True
            leaderboard.append(entry)

        # Current user's position if outside top 10 (students only)
        my_entry = None
        if me is not None and not me_in_top10 and me.role == "student":
            my_points = _user_total_points(me.id)
            users_ahead = sum(1 for r in ranked_qs if r["pts"] > my_points)
            my_entry = {
                "rank": users_ahead + 1,
                "username": me.username,
                "photo": safe_photo_url(me),
                "total_points": round(my_points),
                "is_current_user": True,
            }

        return Response({"leaderboard": leaderboard, "current_user": my_entry})
