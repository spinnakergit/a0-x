from helpers.tool import Tool, Response


class XProfile(Tool):
    """View X.com user profiles: own profile or lookup by username."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "me")
        username = self.args.get("username", "")

        from plugins.x.helpers.x_auth import get_x_config
        config = get_x_config(self.agent)

        from plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            if action == "me":
                self.set_progress("Fetching your profile...")
                result = await client.get_user_me(
                    user_fields="username,name,description,public_metrics,profile_image_url,created_at,verified,location,url"
                )
            elif action == "lookup":
                if not username:
                    return Response(message="Error: 'username' is required for lookup.", break_loop=False)
                from plugins.x.helpers.sanitize import validate_username
                try:
                    username = validate_username(username)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress(f"Looking up @{username}...")
                result = await client.get_user_by_username(
                    username,
                    user_fields="username,name,description,public_metrics,profile_image_url,created_at,verified,location,url",
                )
            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: me, lookup.",
                    break_loop=False,
                )

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            user = result.get("data", {})
            if not user:
                return Response(message="No user data returned.", break_loop=False)

            return Response(message=_format_profile(user), break_loop=False)
        finally:
            await client.close()


def _format_profile(user: dict) -> str:
    """Format user profile data for display."""
    name = user.get("name", "Unknown")
    username = user.get("username", "unknown")
    bio = user.get("description", "")
    metrics = user.get("public_metrics", {})
    created = user.get("created_at", "")
    location = user.get("location", "")
    url = user.get("url", "")
    verified = user.get("verified", False)

    parts = [f"**@{username}** ({name})"]
    if verified:
        parts[0] += " [Verified]"
    if bio:
        parts.append(f"Bio: {bio}")
    if location:
        parts.append(f"Location: {location}")
    if url:
        parts.append(f"URL: {url}")

    if metrics:
        stats = []
        if "followers_count" in metrics:
            stats.append(f"{metrics['followers_count']:,} followers")
        if "following_count" in metrics:
            stats.append(f"{metrics['following_count']:,} following")
        if "tweet_count" in metrics:
            stats.append(f"{metrics['tweet_count']:,} tweets")
        if "listed_count" in metrics:
            stats.append(f"{metrics['listed_count']:,} listed")
        if stats:
            parts.append(f"Stats: {', '.join(stats)}")

    if created:
        parts.append(f"Joined: {created[:10]}")

    return "\n".join(parts)
