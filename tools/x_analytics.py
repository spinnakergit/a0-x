from helpers.tool import Tool, Response


class XAnalytics(Tool):
    """View tweet and account analytics on X.com. Requires Pay-Per-Use or Basic+ tier."""

    async def execute(self, **kwargs) -> Response:
        from usr.plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("analytics", self.agent):
            return Response(
                message="Analytics service is disabled or requires a paid API tier. "
                "The legacy Free tier does not support analytics. "
                "Switch to Pay-Per-Use (credit-based) or upgrade at developer.x.com.",
                break_loop=False,
            )

        action = self.args.get("action", "tweet")
        tweet_id = self.args.get("tweet_id", "")

        from usr.plugins.x.helpers.x_auth import get_x_config, require_tier
        config = get_x_config(self.agent)

        ok, msg = require_tier("pay_per_use", config)
        if not ok:
            return Response(message=msg, break_loop=False)

        from usr.plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            if action == "tweet":
                if not tweet_id:
                    return Response(message="Error: 'tweet_id' is required for tweet analytics.", break_loop=False)
                from usr.plugins.x.helpers.sanitize import validate_tweet_id
                try:
                    tweet_id = validate_tweet_id(tweet_id)
                except ValueError as e:
                    return Response(message=f"Validation error: {e}", break_loop=False)

                self.set_progress("Fetching tweet analytics...")
                result = await client.get_tweet(
                    tweet_id,
                    tweet_fields="author_id,created_at,public_metrics,organic_metrics,text",
                )

                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )

                tweet = result.get("data", {})
                if not tweet:
                    return Response(message="No tweet data returned.", break_loop=False)

                return Response(message=_format_tweet_analytics(tweet), break_loop=False)

            elif action == "account":
                self.set_progress("Fetching account analytics...")
                result = await client.get_user_me(
                    user_fields="username,name,public_metrics,created_at"
                )

                if result.get("error"):
                    return Response(
                        message=f"Error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )

                user = result.get("data", {})
                if not user:
                    return Response(message="No user data returned.", break_loop=False)

                # Get usage stats
                from usr.plugins.x.helpers.x_auth import get_usage, get_monthly_limit
                usage = get_usage(config)
                monthly_limit = get_monthly_limit(config)

                return Response(
                    message=_format_account_analytics(user, usage, monthly_limit),
                    break_loop=False,
                )

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'. Use: tweet, account.",
                    break_loop=False,
                )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()


def _format_tweet_analytics(tweet: dict) -> str:
    """Format tweet analytics for display."""
    text_preview = tweet.get("text", "")[:100]
    created = tweet.get("created_at", "")
    metrics = tweet.get("public_metrics", {})
    organic = tweet.get("organic_metrics", {})

    parts = [f"**Tweet Analytics** (ID: {tweet.get('id', '?')})"]
    if created:
        parts.append(f"Posted: {created}")
    parts.append(f"Text: {text_preview}{'...' if len(tweet.get('text', '')) > 100 else ''}")
    parts.append("")

    if metrics:
        parts.append("**Public Metrics:**")
        metric_labels = {
            "impression_count": "Impressions",
            "like_count": "Likes",
            "retweet_count": "Retweets",
            "reply_count": "Replies",
            "quote_count": "Quotes",
            "bookmark_count": "Bookmarks",
        }
        for key, label in metric_labels.items():
            if key in metrics:
                parts.append(f"  {label}: {metrics[key]:,}")

    if organic:
        parts.append("\n**Organic Metrics:**")
        for key, val in organic.items():
            label = key.replace("_count", "").replace("_", " ").title()
            parts.append(f"  {label}: {val:,}")

    return "\n".join(parts)


def _format_account_analytics(user: dict, usage: dict, monthly_limit: int) -> str:
    """Format account analytics for display."""
    username = user.get("username", "unknown")
    metrics = user.get("public_metrics", {})
    created = user.get("created_at", "")

    parts = [f"**Account Analytics** — @{username}"]
    if created:
        parts.append(f"Account created: {created[:10]}")
    parts.append("")

    if metrics:
        parts.append("**Public Metrics:**")
        parts.append(f"  Followers: {metrics.get('followers_count', 0):,}")
        parts.append(f"  Following: {metrics.get('following_count', 0):,}")
        parts.append(f"  Tweets: {metrics.get('tweet_count', 0):,}")
        parts.append(f"  Listed: {metrics.get('listed_count', 0):,}")

    posted = usage.get("tweets_posted", 0)
    deleted = usage.get("tweets_deleted", 0)
    month = usage.get("month", "unknown")
    parts.append(f"\n**Usage This Month** ({month}):")
    parts.append(f"  Tweets posted: {posted:,} / {monthly_limit:,}")
    parts.append(f"  Tweets deleted: {deleted:,}")
    parts.append(f"  Budget remaining: {max(0, monthly_limit - posted):,}")

    return "\n".join(parts)
