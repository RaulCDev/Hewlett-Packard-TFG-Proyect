import re
from urllib.parse import urlencode


EXAMPLE_VALUES = {"replace-me", "changeme"}
OAUTH_CALLBACK_QUERY = re.compile(r"(/callback)\?[^ ]*")


def _is_configured(value):
    normalized = (value or "").strip()
    return bool(normalized) and normalized.lower() not in EXAMPLE_VALUES


def google_integration_status(environ):
    missing = [
        name
        for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
        if not _is_configured(environ.get(name))
    ]
    return {
        "service": "google",
        "configured": not missing,
        "missingCredentials": missing,
    }


def google_identity_from_claims(claims):
    if not isinstance(claims, dict):
        raise ValueError("Google identity claims must be a dictionary")

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        raise ValueError("Google identity did not include an email")
    email = email.strip()

    name = claims.get("name")
    if not isinstance(name, str) or not name.strip():
        name = email.split("@", 1)[0]
    return {"email": email, "name": name.strip()}


def redact_oauth_callback_log(value):
    return OAUTH_CALLBACK_QUERY.sub(
        r"\1?<oauth-parameters-redacted>",
        str(value),
    )


def build_google_authorization_url(environ, redirect_uri, state):
    status = google_integration_status(environ)
    if not status["configured"]:
        raise ValueError("Google credentials are not configured")
    query = urlencode(
        {
            "response_type": "code",
            "client_id": environ["GOOGLE_CLIENT_ID"].strip(),
            "scope": "openid email profile",
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
