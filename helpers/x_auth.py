"""
X.com (Twitter) dual-auth module.

Supports:
- OAuth 2.0 with PKCE for API v2 endpoints (posting, reading, managing)
- OAuth 1.0a for media upload (v1.1 endpoint)
- App-only Bearer Token for read endpoints without user context

Pricing tiers (as of Feb 2026):
- Pay-Per-Use (recommended): Credit-based, all endpoints, no subscription.
  ~$0.005/read, ~$0.01/post, ~$0.01/user lookup. 2M reads/mo cap.
- Free (legacy/deprecated):  1,500 tweets/mo write, NO read/search.
- Basic (legacy/deprecated): $200/mo fixed. 50K tweets/mo + read + search.
- Pro (legacy/deprecated):   $5,000/mo fixed. 300K tweets/mo + full archive.
"""

import os
import json
import hashlib
import base64
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

TIER_CAPABILITIES = {
    "pay_per_use": {
        "write": True,
        "read": True,
        "search": True,
        "monthly_tweets": 100000,  # Soft limit — credit-based, configurable
    },
    # Legacy tiers (deprecated Feb 2026 — still functional for existing subscribers)
    "free": {
        "write": True,
        "read": False,
        "search": False,
        "monthly_tweets": 1500,
    },
    "basic": {
        "write": True,
        "read": True,
        "search": True,
        "monthly_tweets": 50000,
    },
    "pro": {
        "write": True,
        "read": True,
        "search": True,
        "monthly_tweets": 300000,
    },
}

SERVICE_TIER_REQUIREMENTS = {
    "posting": "free",
    "reading": "pay_per_use",
    "search": "pay_per_use",
    "media": "free",
    "analytics": "pay_per_use",
}

# OAuth 2.0 endpoints
OAUTH2_AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
OAUTH2_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
OAUTH2_SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "offline.access",
    "like.read",
    "like.write",
    "bookmark.read",
    "bookmark.write",
]


def get_x_config(agent=None):
    """Load plugin config through A0's plugin config system."""
    try:
        from helpers import plugins
        return plugins.get_plugin_config("x", agent=agent)
    except Exception:
        return {}


def get_tier(config: dict) -> str:
    """Return the API tier from config."""
    return config.get("tier", "free").lower()


def get_tier_capabilities(config: dict) -> dict:
    """Return capability dict for current tier."""
    tier = get_tier(config)
    return TIER_CAPABILITIES.get(tier, TIER_CAPABILITIES["free"])


def can_read(config: dict) -> bool:
    """Whether current tier supports read operations."""
    return get_tier_capabilities(config).get("read", False)


def can_search(config: dict) -> bool:
    """Whether current tier supports search operations."""
    return get_tier_capabilities(config).get("search", False)


def can_write(config: dict) -> bool:
    """Whether current tier supports write operations."""
    return get_tier_capabilities(config).get("write", True)


def get_monthly_limit(config: dict) -> int:
    """Return the monthly tweet limit for current tier."""
    return get_tier_capabilities(config).get("monthly_tweets", 1500)


def require_tier(required: str, config: dict) -> tuple:
    """
    Check if current tier meets requirement.
    Returns (ok, error_message). error_message is empty if ok.
    """
    tier_order = {"free": 0, "pay_per_use": 1, "basic": 1, "pro": 2}
    current = get_tier(config)
    current_level = tier_order.get(current, 0)
    required_level = tier_order.get(required, 0)

    if current_level >= required_level:
        return (True, "")

    return (
        False,
        "This action requires read/search access which is not available on the "
        f"Free (legacy) tier. Switch to Pay-Per-Use (credit-based, no subscription) "
        f"or upgrade to Basic/Pro at developer.x.com.",
    )


def is_service_enabled(service_name: str, agent=None) -> bool:
    """Check if a service is enabled in config AND tier supports it."""
    config = get_x_config(agent)
    services = config.get("services", {})
    service = services.get(service_name, {})
    if not service.get("enabled", True):
        return False

    required_tier = SERVICE_TIER_REQUIREMENTS.get(service_name, "free")
    ok, _ = require_tier(required_tier, config)
    return ok


def _data_dir(config: dict) -> Path:
    """Get the data directory for storing credentials and tokens."""
    try:
        from helpers import plugins
        plugin_dir = plugins.get_plugin_dir("x")
        data_dir = Path(plugin_dir) / "data"
    except Exception:
        data_dir = Path("/a0/usr/plugins/x/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _token_path(config: dict) -> Path:
    """Path to the OAuth 2.0 token file."""
    return _data_dir(config) / "token.json"


def _usage_path(config: dict) -> Path:
    """Path to the usage tracking file."""
    return _data_dir(config) / "usage.json"


def secure_write_json(path: Path, data: dict):
    """Atomic write with 0o600 permissions."""
    tmp = path.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        os.unlink(str(tmp))
        raise
    os.replace(str(tmp), str(path))


def _read_json(path: Path) -> dict:
    """Read a JSON file, return empty dict if missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# --- OAuth 2.0 PKCE Flow ---

def generate_pkce():
    """Generate PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def generate_oauth2_auth_url(config: dict) -> tuple:
    """
    Generate OAuth 2.0 authorization URL with PKCE.
    Returns (url, state, code_verifier) — store state and verifier for callback.
    """
    client_id = config.get("oauth2", {}).get("client_id", "")
    if not client_id:
        return ("", "", "")

    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce()

    redirect_uri = config.get("oauth2", {}).get("redirect_uri", "http://localhost:3000/callback")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(OAUTH2_SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    url = OAUTH2_AUTHORIZE_URL + "?" + urlencode(params)
    return (url, state, verifier)


def get_oauth2_token(config: dict) -> dict:
    """Load stored OAuth 2.0 token from file."""
    return _read_json(_token_path(config))


def save_oauth2_token(config: dict, token_data: dict):
    """Persist OAuth 2.0 token to file with timestamp."""
    token_data["saved_at"] = int(time.time())
    secure_write_json(_token_path(config), token_data)


def _is_token_expired(token: dict) -> bool:
    """Check if OAuth 2.0 token is expired (with 60s buffer)."""
    saved_at = token.get("saved_at", 0)
    expires_in = token.get("expires_in", 7200)
    if not saved_at:
        return False  # No timestamp — assume valid, let API reject if not
    return time.time() > (saved_at + expires_in - 60)


def refresh_oauth2_token(config: dict) -> dict:
    """
    Refresh the OAuth 2.0 access token using the stored refresh token.
    Returns the new token dict, or {"error": "..."} on failure.
    """
    token = get_oauth2_token(config)
    refresh_tok = token.get("refresh_token", "")
    if not refresh_tok:
        return {"error": "No refresh token available"}

    client_id = config.get("oauth2", {}).get("client_id", "")
    client_secret = config.get("oauth2", {}).get("client_secret", "")
    if not client_id:
        return {"error": "No OAuth 2.0 client_id configured"}

    import requests as _requests
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok,
    }

    try:
        if client_secret:
            resp = _requests.post(
                OAUTH2_TOKEN_URL,
                data=data,
                auth=(client_id, client_secret),
                timeout=15,
            )
        else:
            data["client_id"] = client_id
            resp = _requests.post(OAUTH2_TOKEN_URL, data=data, timeout=15)

        if resp.status_code != 200:
            return {"error": f"Refresh failed ({resp.status_code}): {resp.text}"}

        new_token = resp.json()
        save_oauth2_token(config, new_token)
        return new_token
    except Exception as e:
        return {"error": f"Refresh request failed: {e}"}


def get_oauth2_headers(config: dict) -> dict:
    """Get Authorization headers for API v2 requests. Auto-refreshes expired tokens."""
    token = get_oauth2_token(config)
    access_token = token.get("access_token", "")

    if not access_token:
        bearer = config.get("bearer_token", "")
        if bearer:
            return {"Authorization": f"Bearer {bearer}"}
        return {}

    # Auto-refresh if expired
    if _is_token_expired(token) and token.get("refresh_token"):
        refreshed = refresh_oauth2_token(config)
        if not refreshed.get("error"):
            access_token = refreshed.get("access_token", access_token)

    return {"Authorization": f"Bearer {access_token}"}


def get_bearer_headers(config: dict) -> dict:
    """Get Bearer token headers (app-only auth)."""
    bearer = config.get("bearer_token", "")
    if bearer:
        return {"Authorization": f"Bearer {bearer}"}
    return {}


# --- OAuth 1.0a (for media upload) ---

def get_oauth1_credentials(config: dict) -> dict:
    """Extract OAuth 1.0a credentials from config."""
    oauth1 = config.get("oauth1", {})
    return {
        "consumer_key": oauth1.get("api_key", ""),
        "consumer_secret": oauth1.get("api_secret", ""),
        "access_token": oauth1.get("access_token", ""),
        "access_token_secret": oauth1.get("access_token_secret", ""),
    }


def has_oauth1(config: dict) -> bool:
    """Check if OAuth 1.0a credentials are configured."""
    creds = get_oauth1_credentials(config)
    return all(creds.values())


def has_any_auth(config: dict) -> bool:
    """Check if any authentication method is configured."""
    if has_oauth1(config):
        return True
    token = get_oauth2_token(config)
    if token.get("access_token"):
        return True
    if config.get("bearer_token"):
        return True
    return False


# --- Authentication Status ---

def is_authenticated(config: dict) -> tuple:
    """
    Check if credentials are valid by calling /2/users/me.
    Returns (authenticated: bool, info: str).
    """
    if not has_any_auth(config):
        return (False, "No credentials configured")

    try:
        import requests
        headers = get_oauth2_headers(config)
        if not headers:
            # Fall back to OAuth 1.0a for user verification
            if has_oauth1(config):
                from requests_oauthlib import OAuth1
                creds = get_oauth1_credentials(config)
                auth = OAuth1(
                    creds["consumer_key"],
                    creds["consumer_secret"],
                    creds["access_token"],
                    creds["access_token_secret"],
                )
                resp = requests.get(
                    "https://api.twitter.com/2/users/me",
                    auth=auth,
                    params={"user.fields": "username"},
                    timeout=10,
                )
            else:
                return (False, "No valid auth credentials")
        else:
            resp = requests.get(
                "https://api.twitter.com/2/users/me",
                headers=headers,
                params={"user.fields": "username"},
                timeout=10,
            )

        if resp.status_code == 200:
            data = resp.json().get("data", {})
            username = data.get("username", "unknown")
            return (True, f"@{username}")
        elif resp.status_code == 401:
            # Token may be expired — try refreshing
            token = get_oauth2_token(config)
            if token.get("refresh_token"):
                refreshed = refresh_oauth2_token(config)
                if not refreshed.get("error"):
                    retry = requests.get(
                        "https://api.twitter.com/2/users/me",
                        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
                        params={"user.fields": "username"},
                        timeout=10,
                    )
                    if retry.status_code == 200:
                        data = retry.json().get("data", {})
                        return (True, f"@{data.get('username', 'unknown')}")
            return (False, f"API error: {resp.status_code} (token may be expired)")
        elif resp.status_code == 403:
            # Might be Free tier — can write but /users/me may be restricted
            if has_oauth1(config):
                return (True, "Authenticated (Free tier — read access limited)")
            return (False, f"Access denied: {resp.status_code}")
        else:
            return (False, f"API error: {resp.status_code}")
    except Exception as e:
        return (False, str(e))


# --- Usage Tracking ---

def get_usage(config: dict) -> dict:
    """Get current month's usage stats."""
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    usage = _read_json(_usage_path(config))
    if usage.get("month") != current_month:
        usage = {"month": current_month, "tweets_posted": 0, "tweets_deleted": 0}
        secure_write_json(_usage_path(config), usage)
    return usage


def increment_usage(config: dict, field: str = "tweets_posted"):
    """Increment a usage counter for the current month."""
    usage = get_usage(config)
    usage[field] = usage.get(field, 0) + 1
    secure_write_json(_usage_path(config), usage)


def check_write_budget(config: dict) -> tuple:
    """
    Check if we can write another tweet.
    Returns (can_write: bool, message: str).
    """
    usage = get_usage(config)
    monthly_limit = get_monthly_limit(config)
    daily_limit = config.get("usage", {}).get("daily_tweet_limit", 50)
    posted = usage.get("tweets_posted", 0)

    if posted >= monthly_limit:
        return (False, f"Monthly tweet limit reached ({posted}/{monthly_limit})")

    if posted >= monthly_limit * 0.9:
        return (True, f"Warning: approaching monthly limit ({posted}/{monthly_limit})")

    return (True, "")
