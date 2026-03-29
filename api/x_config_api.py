"""API endpoint: Get/set X.com plugin configuration.
URL: POST /api/plugins/x/x_config_api

Handles:
- GET / action=get: Return current config (with sensitive values masked)
- POST action=set: Save config (preserves masked credentials)
- POST action=oauth2_url: Generate OAuth 2.0 PKCE authorization URL
- POST action=oauth2_callback: Exchange auth code for token
- POST action=test: Test current credentials
"""
import json
import yaml
from pathlib import Path
from helpers.api import ApiHandler, Request, Response


SENSITIVE_KEYS = ["api_key", "api_secret", "access_token", "access_token_secret",
                  "client_id", "client_secret", "bearer_token"]


def _get_config_path() -> Path:
    """Find the writable config path."""
    candidates = [
        Path(__file__).parent.parent / "config.json",
        Path("/a0/usr/plugins/x/config.json"),
        Path("/a0/plugins/x/config.json"),
    ]
    for p in candidates:
        if p.parent.exists():
            return p
    return candidates[-1]


def _mask(value: str) -> str:
    """Mask a sensitive string for display."""
    if not value or len(value) < 6:
        return "••••••" if value else ""
    return value[:3] + "••••" + value[-3:]


def _deep_mask(obj, keys=None):
    """Recursively mask sensitive values in a config dict."""
    if keys is None:
        keys = SENSITIVE_KEYS
    if isinstance(obj, dict):
        masked = {}
        for k, v in obj.items():
            if k in keys and isinstance(v, str) and v:
                masked[k] = _mask(v)
            else:
                masked[k] = _deep_mask(v, keys)
        return masked
    return obj


def _deep_merge_preserve_masked(new: dict, existing: dict) -> dict:
    """Merge new config into existing, preserving masked sensitive values."""
    merged = dict(existing)
    for k, v in new.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge_preserve_masked(v, merged[k])
        elif isinstance(v, str) and "••••" in v:
            pass  # Keep existing value
        else:
            merged[k] = v
    return merged


class XConfigApi(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
        if request.method == "GET" or action == "get":
            return self._get_config()
        elif action == "set":
            return self._set_config(input)
        elif action == "oauth2_url":
            return self._get_oauth2_url()
        elif action == "oauth2_callback":
            return await self._oauth2_callback(input)
        elif action == "test":
            return self._test_connection()
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_config(self) -> dict:
        try:
            config_path = _get_config_path()
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                default_path = config_path.parent / "default_config.yaml"
                if default_path.exists():
                    with open(default_path, "r") as f:
                        config = yaml.safe_load(f) or {}
                else:
                    config = {}

            # Add auth status
            from usr.plugins.x.helpers.x_auth import has_any_auth, get_tier, get_usage, get_monthly_limit
            config["_auth_configured"] = has_any_auth(config)
            config["_tier"] = get_tier(config)
            usage = get_usage(config)
            config["_usage"] = {
                "month": usage.get("month", ""),
                "tweets_posted": usage.get("tweets_posted", 0),
                "monthly_limit": get_monthly_limit(config),
            }

            return _deep_mask(config)
        except Exception as e:
            return {"error": f"Failed to read configuration: {e}"}

    def _set_config(self, input: dict) -> dict:
        try:
            config = input.get("config", input)
            if not config or config == {"action": "set"}:
                return {"error": "No config provided"}
            config.pop("action", None)
            config.pop("_auth_configured", None)
            config.pop("_tier", None)
            config.pop("_usage", None)

            config_path = _get_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)

            existing = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    existing = json.load(f)

            merged = _deep_merge_preserve_masked(config, existing)

            # Atomic write with secure permissions
            import os
            tmp = config_path.with_suffix(".tmp")
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(merged, f, indent=2)
            os.replace(str(tmp), str(config_path))

            return {"ok": True}
        except Exception as e:
            return {"error": f"Failed to save configuration: {e}"}

    def _get_oauth2_url(self) -> dict:
        try:
            config_path = _get_config_path()
            config = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)

            from usr.plugins.x.helpers.x_auth import generate_oauth2_auth_url
            url, state, verifier = generate_oauth2_auth_url(config)

            if not url:
                return {"error": "OAuth 2.0 client_id not configured"}

            # Store state and verifier for callback
            from usr.plugins.x.helpers.x_auth import _data_dir, secure_write_json
            data_dir = _data_dir(config)
            secure_write_json(data_dir / "oauth2_state.json", {
                "state": state,
                "verifier": verifier,
            })

            return {"ok": True, "url": url}
        except Exception as e:
            return {"error": f"Failed to generate auth URL: {e}"}

    async def _oauth2_callback(self, input: dict) -> dict:
        try:
            code = input.get("code", "")
            state = input.get("state", "")

            if not code or not state:
                return {"error": "Missing code or state parameter"}

            config_path = _get_config_path()
            config = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)

            from usr.plugins.x.helpers.x_auth import _data_dir, _read_json, save_oauth2_token
            data_dir = _data_dir(config)
            stored = _read_json(data_dir / "oauth2_state.json")

            if stored.get("state") != state:
                return {"error": "State mismatch — possible CSRF attack"}

            # Exchange code for token
            import requests
            from usr.plugins.x.helpers.x_auth import OAUTH2_TOKEN_URL

            client_id = config.get("oauth2", {}).get("client_id", "")
            client_secret = config.get("oauth2", {}).get("client_secret", "")

            redirect_uri = config.get("oauth2", {}).get("redirect_uri", "http://localhost:3000/callback")
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": stored.get("verifier", ""),
            }

            if client_secret:
                resp = requests.post(
                    OAUTH2_TOKEN_URL,
                    data=token_data,
                    auth=(client_id, client_secret),
                    timeout=15,
                )
            else:
                token_data["client_id"] = client_id
                resp = requests.post(OAUTH2_TOKEN_URL, data=token_data, timeout=15)

            if resp.status_code != 200:
                return {"error": f"Token exchange failed ({resp.status_code}): {resp.text}"}

            token = resp.json()
            save_oauth2_token(config, token)

            # Clean up state file
            state_file = data_dir / "oauth2_state.json"
            if state_file.exists():
                state_file.unlink()

            return {"ok": True, "message": "Authentication successful"}
        except Exception as e:
            return {"error": f"OAuth callback failed: {e}"}

    def _test_connection(self) -> dict:
        try:
            config_path = _get_config_path()
            config = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)

            from usr.plugins.x.helpers.x_auth import is_authenticated, get_tier
            ok, info = is_authenticated(config)

            return {
                "ok": ok,
                "user": info if ok else None,
                "tier": get_tier(config),
                "error": info if not ok else None,
            }
        except Exception as e:
            return {"ok": False, "error": f"Connection test failed: {e}"}
