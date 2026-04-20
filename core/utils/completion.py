from core.models.challenge_model import Challenge
from core.models.submission_model import Submission
from core.models.certificate_model import Certificate


def check_and_issue_certificate(user, course):
    """
    Issue or update a certificate for user/course.

    Returns (cert, score_changed) where:
      cert         — Certificate instance if threshold met, else None
      score_changed — True if the cert was newly issued or score_pct changed
    """
    total = Challenge.objects.filter(topic__course=course).count()
    if total == 0:
        return None, False

    passed_count = (
        Submission.objects
        .filter(user=user, challenge__topic__course=course, status="passed")
        .values("challenge_id").distinct().count()
    )
    score_pct = round((passed_count / total) * 100, 2)

    existing = Certificate.objects.filter(user=user, course=course).first()
    if existing:
        if score_pct > existing.score_pct:
            existing.score_pct = score_pct
            existing.save(update_fields=["score_pct"])
            return existing, True
        return existing, False

    if score_pct < course.completion_threshold:
        return None, False

    cert, created = Certificate.objects.get_or_create(
        user=user, course=course, defaults={"score_pct": score_pct}
    )
    return cert, created
