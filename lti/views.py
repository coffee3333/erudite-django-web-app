import uuid
import logging
import urllib.parse

from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache

from rest_framework_simplejwt.tokens import RefreshToken

from .models import LTIRegistration, LTIResourceMapping, LTISession
from .utils import public_key_to_jwk, verify_lti_jwt

User = get_user_model()
logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

# LTI 1.3 claim constants
CLAIM_MESSAGE_TYPE = "https://purl.imsglobal.org/spec/lti/claim/message_type"
CLAIM_VERSION = "https://purl.imsglobal.org/spec/lti/claim/version"
CLAIM_RESOURCE_LINK = "https://purl.imsglobal.org/spec/lti/claim/resource_link"
CLAIM_ROLES = "https://purl.imsglobal.org/spec/lti/claim/roles"
CLAIM_DEPLOYMENT_ID = "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
CLAIM_AGS = "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint"


class JWKSView(View):
    """
    GET /lti/jwks/
    Serves the tool's RS256 public keys so the platform can verify our JWTs.
    """
    def get(self, request):
        keys = []
        for reg in LTIRegistration.objects.all():
            if reg.tool_public_key:
                jwk = public_key_to_jwk(reg.tool_public_key, reg.tool_key_id)
                keys.append(jwk)
        return JsonResponse({"keys": keys})


@method_decorator(csrf_exempt, name="dispatch")
class OIDCInitView(View):
    """
    GET/POST /lti/oidc-init/
    Step 1 of LTI 1.3 launch: Platform sends login hint, we redirect back with nonce.
    """
    def get(self, request):
        return self._handle(request)

    def post(self, request):
        return self._handle(request)

    def _handle(self, request):
        params = request.POST if request.method == "POST" else request.GET

        issuer = params.get("iss")
        login_hint = params.get("login_hint")
        target_link_uri = params.get("target_link_uri")
        lti_message_hint = params.get("lti_message_hint", "")
        client_id = params.get("client_id")

        logger.info(f"OIDC init — iss={issuer} client_id={client_id} login_hint={login_hint} target={target_link_uri}")

        if not login_hint or not target_link_uri:
            logger.error(f"OIDC init missing params: iss={issuer} login_hint={login_hint} target={target_link_uri}")
            return HttpResponseBadRequest("Missing required OIDC parameters (login_hint, target_link_uri)")

        # Try to find registration by client_id first (most reliable), then issuer
        reg = None
        if client_id:
            reg = LTIRegistration.objects.filter(client_id=client_id).first()
        if not reg and issuer:
            reg = LTIRegistration.objects.filter(issuer=issuer).first()
        if not reg:
            logger.error(f"OIDC init — no registration found for iss={issuer} client_id={client_id}")
            return HttpResponseBadRequest(f"Unknown platform (iss={issuer}, client_id={client_id})")

        # Generate state and nonce, store in cache for 10 minutes
        state = str(uuid.uuid4())
        nonce = str(uuid.uuid4())
        cache.set(f"lti_state_{state}", {"nonce": nonce, "registration_id": reg.id}, timeout=600)
        # Build redirect back to platform's auth request URL
        redirect_params = {
            "scope": "openid",
            "response_type": "id_token",
            "client_id": reg.client_id,
            "redirect_uri": target_link_uri,
            "login_hint": login_hint,
            "state": state,
            "response_mode": "form_post",
            "nonce": nonce,
            "prompt": "none",
        }
        if lti_message_hint:
            redirect_params["lti_message_hint"] = lti_message_hint

        auth_url = reg.auth_request_url + "?" + urllib.parse.urlencode(redirect_params)
        return HttpResponseRedirect(auth_url)


@method_decorator(csrf_exempt, name="dispatch")
class LTILaunchView(View):
    """
    POST /lti/launch/
    Step 2: Platform posts the signed LTI JWT here. We verify it, create/find the
    Erudite user, create an LTISession, and redirect the student into the course.
    """
    def post(self, request):
        id_token = request.POST.get("id_token")
        state = request.POST.get("state")

        if not id_token or not state:
            return HttpResponseBadRequest("Missing id_token or state")

        # Retrieve state from cache
        state_data = cache.get(f"lti_state_{state}")
        if not state_data:
            return HttpResponseBadRequest("Invalid or expired state")
        cache.delete(f"lti_state_{state}")

        try:
            reg = LTIRegistration.objects.get(id=state_data["registration_id"])
        except LTIRegistration.DoesNotExist:
            return HttpResponseBadRequest("Registration not found")

        # Verify the JWT
        try:
            claims = verify_lti_jwt(
                token=id_token,
                jwks_url=reg.platform_jwks_url,
                client_id=reg.client_id,
                issuer=reg.issuer,
            )
        except Exception as e:
            logger.error(f"LTI JWT verification failed: {e}")
            return HttpResponseBadRequest(f"JWT verification failed: {e}")

        # Validate nonce
        if claims.get("nonce") != state_data["nonce"]:
            return HttpResponseBadRequest("Nonce mismatch")

        # Validate message type
        if claims.get(CLAIM_MESSAGE_TYPE) != "LtiResourceLinkRequest":
            return HttpResponseBadRequest("Unsupported message type")

        # Extract user info
        lti_user_id = claims.get("sub")
        email = claims.get("email", "")
        name = claims.get("name", "") or claims.get("given_name", "")

        if not email:
            return HttpResponseBadRequest("Platform did not share user email")

        # Find or create Erudite user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": self._unique_username(name or email.split("@")[0]),
                "email_verified": True,
                "role": "student",
            },
        )
        if created:
            user.set_unusable_password()
            user.moodle_platform = reg.name
            user.save()
        elif user.moodle_platform != reg.name:
            user.moodle_platform = reg.name
            user.save(update_fields=["moodle_platform"])

        # Find or create resource mapping
        resource_link = claims.get(CLAIM_RESOURCE_LINK, {})
        resource_link_id = resource_link.get("id", "")

        # Resolve course by lti_token (custom param) — only token-based lookup is supported
        # Teacher sets "course=<lti_token>" in Moodle custom parameters
        custom_params = claims.get("https://purl.imsglobal.org/spec/lti/claim/custom", {})
        course_token = custom_params.get("course")
        logger.info(f"LTI launch — custom_params={custom_params} course_token={course_token}")
        course = None
        if course_token:
            from core.models.course_model import Course
            try:
                course = Course.objects.get(lti_token=course_token)
                logger.info(f"LTI launch — resolved course: {course.slug}")
            except (Course.DoesNotExist, Exception) as e:
                logger.warning(f"LTI launch — course token lookup failed: {e}")
                course = None

        # If no valid course token, just log the user in and send to courses list
        if course is None:
            logger.warning(f"LTI launch — no valid course token, redirecting to /courses")
            refresh = RefreshToken.for_user(user)
            redirect_url = (
                f"{FRONTEND_URL}/lti-landing"
                f"?access={str(refresh.access_token)}"
                f"&refresh={str(refresh)}"
                f"&next={urllib.parse.quote('/courses')}"
            )
            return HttpResponseRedirect(redirect_url)

        mapping, created = LTIResourceMapping.objects.get_or_create(
            registration=reg,
            resource_link_id=resource_link_id,
            defaults={"course": course},
        )
        # Always update course from token if token was provided — allows re-pointing
        if not created and course is not None and mapping.course != course:
            mapping.course = course
            mapping.save(update_fields=["course"])
        logger.info(f"LTI launch — mapping course_id={mapping.course_id} created={created}")

        # Extract AGS endpoint if present
        ags = claims.get(CLAIM_AGS, {})
        lineitem_url = ags.get("lineitem") or ags.get("lineitems")
        if lineitem_url and not mapping.lineitem_url:
            mapping.lineitem_url = lineitem_url
            mapping.save()

        score_url = None
        if lineitem_url:
            # Insert /scores before the query string, not after it
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(lineitem_url)
            score_url = urlunparse(parsed._replace(path=parsed.path.rstrip("/") + "/scores"))

        # Create LTI session
        lti_session = LTISession.objects.create(
            user=user,
            registration=reg,
            resource_mapping=mapping,
            lti_user_id=lti_user_id,
            score_url=score_url,
        )

        # Auto-enroll the student in the mapped course (for private courses)
        if mapping.course_id and not user == mapping.course.owner:
            from core.models.enrollment_model import CourseEnrollment
            CourseEnrollment.objects.get_or_create(course=mapping.course, student=user)

        # Issue JWT tokens for the user so frontend can authenticate
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Redirect to frontend with tokens + session id
        # If a course is mapped, go straight to it; otherwise go to courses list
        if mapping.course_id:
            frontend_path = f"/course/{mapping.course.slug}"
        else:
            frontend_path = "/courses"

        redirect_url = (
            f"{FRONTEND_URL}/lti-landing"
            f"?access={access_token}"
            f"&refresh={refresh_token}"
            f"&session={lti_session.id}"
            f"&next={urllib.parse.quote(frontend_path)}"
        )
        return HttpResponseRedirect(redirect_url)

    def _unique_username(self, base: str) -> str:
        from django.utils.text import slugify
        base = slugify(base)[:40] or "user"
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        return username


class LTIConfigView(View):
    """
    GET /lti/config/
    Returns the tool's configuration as a JSON object (useful for auto-registration).
    """
    def get(self, request):
        base_url = request.build_absolute_uri("/").rstrip("/")
        config = {
            "title": "Erudite",
            "description": "Erudite Learning Platform",
            "oidc_initiation_url": f"{base_url}/lti/oidc-init/",
            "target_link_uri": f"{base_url}/lti/launch/",
            "public_jwk_url": f"{base_url}/lti/jwks/",
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
            ],
            "extensions": [
                {
                    "platform": "moodle.net",
                    "settings": {
                        "platform": "moodle.net",
                        "privacy_level": "public",
                        "placements": [{"placement": "course_navigation", "message_type": "LtiResourceLinkRequest"}],
                    },
                }
            ],
        }
        return JsonResponse(config)
