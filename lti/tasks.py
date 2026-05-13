from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_grade_to_platform(self, lti_session_id: str, score: float):
    """
    Send a grade (0.0–1.0) back to the LMS via AGS (Assignment and Grade Services).
    Retries up to 3 times on failure.
    """
    from .models import LTISession
    from .utils import get_platform_access_token
    import time

    try:
        session = LTISession.objects.select_related("registration", "resource_mapping").get(id=lti_session_id)
    except LTISession.DoesNotExist:
        logger.error(f"LTISession {lti_session_id} not found, skipping grade passback")
        return

    from urllib.parse import urlparse, urlunparse

    def _build_score_url(lineitem_url):
        parsed = urlparse(lineitem_url)
        return urlunparse(parsed._replace(path=parsed.path.rstrip("/") + "/scores"))

    if session.resource_mapping.lineitem_url:
        # Always rebuild from lineitem_url to guard against malformed stored score_url
        score_url = _build_score_url(session.resource_mapping.lineitem_url)
    elif session.score_url:
        score_url = session.score_url
    else:
        score_url = None
    if not score_url:
        logger.warning(f"No score URL for LTISession {lti_session_id}, skipping")
        return

    try:
        from django.conf import settings

        internal_score_url = score_url
        for public, internal in getattr(settings, 'LTI_HOST_REWRITES', {}).items():
            internal_score_url = internal_score_url.replace(public, internal)
        score_host = urlparse(score_url).netloc

        access_token = get_platform_access_token(session.registration)

        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scoreGiven": score,
            "scoreMaximum": 1.0,
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
            "userId": session.lti_user_id,
        }

        resp = requests.post(
            internal_score_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.ims.lis.v1.score+json",
                "Host": score_host,
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info(f"Grade {score} sent for session {lti_session_id}")

    except Exception as exc:
        logger.error(f"Grade passback failed for {lti_session_id}: {exc}")
        raise self.retry(exc=exc)
