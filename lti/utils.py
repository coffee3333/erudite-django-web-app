import json
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
import base64


def generate_rsa_keypair():
    """Generate a new RS256 key pair. Returns (private_pem, public_pem) strings."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().private_bytes if False else private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def public_key_to_jwk(public_pem: str, key_id: str) -> dict:
    """Convert a PEM public key to a JWK dict."""
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    public_key: RSAPublicKey = load_pem_public_key(public_pem.encode(), backend=default_backend())
    pub_numbers = public_key.public_key().public_numbers() if hasattr(public_key, 'public_key') else public_key.public_numbers()

    def int_to_base64url(n):
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode("ascii")

    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": str(key_id),
        "n": int_to_base64url(pub_numbers.n),
        "e": int_to_base64url(pub_numbers.e),
    }


def fetch_platform_jwks(jwks_url: str) -> dict:
    """
    Fetch the platform's JWKS (Moodle's public keys).
    Rewrites public-facing hostnames to internal Docker IPs but keeps
    the original Host header so Moodle serves the correct response.
    """
    from django.conf import settings
    from urllib.parse import urlparse

    internal_url = jwks_url
    for public, internal in getattr(settings, 'LTI_HOST_REWRITES', {}).items():
        internal_url = internal_url.replace(public, internal)

    # Keep original Host header so Moodle doesn't redirect
    original_host = urlparse(jwks_url).netloc
    resp = requests.get(internal_url, timeout=10, allow_redirects=False,
                        headers={"Host": original_host})
    resp.raise_for_status()
    return resp.json()


def verify_lti_jwt(token: str, jwks_url: str, client_id: str, issuer: str) -> dict:
    """
    Verify the LTI 1.3 JWT from the platform.
    Returns the decoded claims dict or raises an exception.
    """
    # Get the key id from the token header
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    jwks = fetch_platform_jwks(jwks_url)
    keys = jwks.get("keys", [])

    # Find matching key
    matching_key = None
    for key_data in keys:
        if kid and key_data.get("kid") == kid:
            matching_key = key_data
            break
    if not matching_key and keys:
        matching_key = keys[0]  # fallback to first key

    if not matching_key:
        raise ValueError("No matching public key found in platform JWKS")

    # Convert JWK to public key
    from jwt.algorithms import RSAAlgorithm
    public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))

    claims = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=issuer,
    )
    return claims


def get_platform_access_token(registration) -> str:
    """
    Get an OAuth2 access token from the platform (needed for AGS grade passback).
    Uses client_credentials grant with a signed JWT assertion.
    """
    import time
    import uuid as uuid_mod

    now = int(time.time())
    payload = {
        "iss": registration.client_id,
        "sub": registration.client_id,
        "aud": registration.access_token_url,
        "iat": now,
        "exp": now + 300,
        "jti": str(uuid_mod.uuid4()),
    }

    private_key = serialization.load_pem_private_key(
        registration.tool_private_key.encode(),
        password=None,
        backend=default_backend(),
    )

    client_assertion = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": str(registration.tool_key_id)},
    )

    from django.conf import settings
    from urllib.parse import urlparse

    token_url = registration.access_token_url
    for public, internal in getattr(settings, 'LTI_HOST_REWRITES', {}).items():
        token_url = token_url.replace(public, internal)
    original_host = urlparse(registration.access_token_url).netloc

    resp = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
            "scope": "https://purl.imsglobal.org/spec/lti-ags/scope/score",
        },
        headers={"Host": original_host},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]
