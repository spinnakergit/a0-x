from helpers.tool import Tool, Response


class XRead(Tool):
    """Read tweets, timelines, and mentions from X.com. Requires Pay-Per-Use or Basic+ tier."""

    async def execute(self, **kwargs) -> Response:
        from plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("reading", self.agent):
            return Response(
                message="Reading service is disabled or requires a paid API tier. "
                "The legacy Free tier does not support read operations. "
                "Switch to Pay-Per-Use (credit-based) or upgrade at developer.x.com.",
                break_loop=False,
            )

        action = self.args.get("action", "tweet")
        tweet_id = self.args.get("tweet_id", "")
        username = self.args.get("username", "")
        max_results = int(self.args.get("max_results", "20"))

        from plugins.x.helpers.x_auth import get_x_config, require_tier
        config = get_x_config(self.agent)

        from plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            if action == "tweet":
                if not tweet_id:
                    return Response(message="Error: 'tweet_id' is required to read a tweet.", break_loop=False)
                from plugins.x.helpers.sanitize import validate_tweet_id
                try:
                    tweet_id = validate_tweet_id(tweet_id)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress("Fetching tweet...")
                result = await client.get_tweet(
                    tweet_id,
                    tweet_fields="author_id,created_at,public_metrics,conversation_id,text",
                )

            elif action == "user_tweets":
                if not username:
                    return Response(message="Error: 'username' is required for user_tweets.", break_loop=False)
                from plugins.x.helpers.sanitize import validate_username
                try:
                    username = validate_username(username)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)
                self.set_progress(f"Fetching tweets from @{username}...")
                user_result = await client.get_user_by_username(username)
                if user_result.get("error"):
                    return Response(
                        message=f"Error looking up user: {user_result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                user_id = user_result.get("data", {}).get("id")
                if not user_id:
                    return Response(message=f"User @{username} not found.", break_loop=False)
                result = await client.get_user_tweets(user_id, max_results=max_results)

            elif action == "timeline":
                ok, msg = require_tier("pay_per_use", config)
                if not ok:
                    return Response(message=msg, break_loop=False)
                self.set_progress("Fetching home timeline...")
                me = await client.get_user_me()
                if me.get("error"):
                    return Response(
                        message=f"Error: {me.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                user_id = me.get("data", {}).get("id")
                result = await client.get_home_timeline(user_id, max_results=max_results)

            elif action == "mentions":
                ok, msg = require_tier("pay_per_use", config)
                if not ok:
                    return Response(message=msg, break_loop=False)
                self.set_progress("Fetching mentions...")
                me = await client.get_user_me()
                if me.get("error"):
                    return Response(
                        message=f"Error: {me.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )
                user_id = me.get("data", {}).get("id")
                result = await client.get_mentions(user_id, max_results=max_results)

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: tweet, user_tweets, timeline, mentions.",
                    break_loop=False,
                )

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            # Format output
            data = result.get("data")
            if data is None:
                return Response(message="No data returned.", break_loop=False)

            if isinstance(data, list):
                from plugins.x.helpers.sanitize import format_tweets
                return Response(
                    message=f"Found {len(data)} tweet(s):\n\n{format_tweets(data)}",
                    break_loop=False,
                )
            else:
                from plugins.x.helpers.sanitize import format_tweet
                return Response(message=format_tweet(data), break_loop=False)

        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
