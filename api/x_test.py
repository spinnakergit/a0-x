"""API endpoint: Test X.com connection.
URL: POST /api/plugins/x/x_test
"""
from helpers.api import ApiHandler, Request, Response


class XTest(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            import json
            from pathlib import Path

            config_paths = [
                Path(__file__).parent.parent / "config.json",
                Path("/a0/usr/plugins/x/config.json"),
                Path("/a0/plugins/x/config.json"),
            ]
            config = {}
            for p in config_paths:
                if p.exists():
                    with open(p) as f:
                        config = json.load(f)
                    break

            # Self-heal: ensure symlink exists for plugin namespace imports
            plugin_dir = Path(__file__).resolve().parent.parent
            for root in [Path("/a0"), Path("/git/agent-zero")]:
                plugins_dir = root / "plugins"
                if plugins_dir.is_dir():
                    symlink = plugins_dir / "x"
                    if not symlink.exists():
                        symlink.symlink_to(plugin_dir)
                    break

            from plugins.x.helpers.x_auth import is_authenticated, get_tier, has_any_auth

            if not has_any_auth(config):
                return {"ok": False, "error": "No credentials configured. Set up OAuth in settings."}

            ok, info = is_authenticated(config)
            tier = get_tier(config)

            if ok:
                return {"ok": True, "user": info, "tier": tier}
            else:
                return {"ok": False, "error": info, "tier": tier}

        except Exception as e:
            return {"ok": False, "error": f"Connection failed: {type(e).__name__}: {e}"}
