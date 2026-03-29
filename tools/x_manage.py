from helpers.tool import Tool, Response


class XManage(Tool):
    """Manage tweets and engagement on X.com: delete, like, unlike, retweet, unretweet, bookmark."""

    async def execute(self, **kwargs) -> Response:
        from usr.plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("posting", self.agent):
            return Response(
                message="Posting service is disabled. Enable it in X.com plugin settings.",
                break_loop=False,
            )

        action = self.args.get("action", "")
        tweet_id = self.args.get("tweet_id", "")

        if not action:
            return Response(message="Error: 'action' is required (delete, like, unlike, retweet, unretweet, bookmark, unbookmark).", break_loop=False)
        if not tweet_id:
            return Response(message="Error: 'tweet_id' is required.", break_loop=False)

        from usr.plugins.x.helpers.sanitize import validate_tweet_id
        try:
            tweet_id = validate_tweet_id(tweet_id)
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)

        from usr.plugins.x.helpers.x_auth import get_x_config, check_write_budget
        config = get_x_config(self.agent)

        # Delete counts against write budget
        if action == "delete":
            can_write, budget_msg = check_write_budget(config)
            if not can_write:
                return Response(message=f"Error: {budget_msg}", break_loop=False)

        # Bookmark/unbookmark require OAuth 2.0 User Context — not supported via OAuth 1.0a
        if action in ("bookmark", "unbookmark"):
            from usr.plugins.x.helpers.x_auth import get_oauth2_token
            token = get_oauth2_token(config)
            if not token.get("access_token"):
                return Response(
                    message=(
                        f"Error: The '{action}' action requires OAuth 2.0 User Context. "
                        "OAuth 1.0a credentials cannot be used for bookmarks per X API requirements. "
                        "Configure OAuth 2.0 (Client ID + PKCE flow) in plugin settings to use bookmarks."
                    ),
                    break_loop=False,
                )

        from usr.plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            # Get user ID for engagement endpoints
            user_id = None
            if action in ("like", "unlike", "retweet", "unretweet", "bookmark", "unbookmark"):
                me = await client.get_user_me()
                if me.get("error"):
                    return Response(
                        message=f"Error getting user info: {me.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                user_id = me.get("data", {}).get("id")
                if not user_id:
                    return Response(message="Error: Could not determine user ID.", break_loop=False)

            action_map = {
                "delete": ("Deleting tweet...", "Tweet deleted"),
                "like": ("Liking tweet...", "Tweet liked"),
                "unlike": ("Unliking tweet...", "Tweet unliked"),
                "retweet": ("Retweeting...", "Retweeted"),
                "unretweet": ("Removing retweet...", "Retweet removed"),
                "bookmark": ("Bookmarking tweet...", "Tweet bookmarked"),
                "unbookmark": ("Removing bookmark...", "Bookmark removed"),
            }

            if action not in action_map:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: delete, like, unlike, retweet, unretweet, bookmark, unbookmark.",
                    break_loop=False,
                )

            progress_msg, success_msg = action_map[action]
            self.set_progress(progress_msg)

            if action == "delete":
                result = await client.delete_tweet(tweet_id)
            elif action == "like":
                result = await client.like_tweet(user_id, tweet_id)
            elif action == "unlike":
                result = await client.unlike_tweet(user_id, tweet_id)
            elif action == "retweet":
                result = await client.retweet(user_id, tweet_id)
            elif action == "unretweet":
                result = await client.unretweet(user_id, tweet_id)
            elif action == "bookmark":
                result = await client.bookmark(user_id, tweet_id)
            elif action == "unbookmark":
                result = await client.unbookmark(user_id, tweet_id)

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            return Response(message=f"{success_msg} (ID: {tweet_id}).", break_loop=False)
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
