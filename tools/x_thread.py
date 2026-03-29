from helpers.tool import Tool, Response


class XThread(Tool):
    """Post a thread (multiple connected tweets) on X.com."""

    async def execute(self, **kwargs) -> Response:
        from usr.plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("posting", self.agent):
            return Response(
                message="Posting service is disabled. Enable it in X.com plugin settings.",
                break_loop=False,
            )

        tweets_raw = self.args.get("tweets", "")
        numbering = self.args.get("numbering", "true").lower() == "true"

        if not tweets_raw:
            return Response(
                message="Error: 'tweets' is required. Provide tweets separated by '|||' or as a JSON array.",
                break_loop=False,
            )

        # Parse tweets — support ||| delimiter or JSON array
        import json as _json
        tweets = []
        if tweets_raw.strip().startswith("["):
            try:
                tweets = _json.loads(tweets_raw)
            except _json.JSONDecodeError:
                return Response(message="Error: Invalid JSON array for tweets.", break_loop=False)
        else:
            tweets = [t.strip() for t in tweets_raw.split("|||") if t.strip()]

        if len(tweets) < 2:
            return Response(
                message="Error: A thread requires at least 2 tweets. Use x_post for a single tweet.",
                break_loop=False,
            )

        from usr.plugins.x.helpers.sanitize import (
            sanitize_tweet_text,
            validate_tweet_length,
            MAX_THREAD_TWEETS,
        )

        if len(tweets) > MAX_THREAD_TWEETS:
            return Response(
                message=f"Error: Thread too long ({len(tweets)} tweets, max {MAX_THREAD_TWEETS}).",
                break_loop=False,
            )

        # Validate each tweet
        total = len(tweets)
        validated = []
        for i, text in enumerate(tweets):
            text = sanitize_tweet_text(str(text))
            if numbering:
                text = f"{i + 1}/{total} {text}"
            ok, char_count = validate_tweet_length(text)
            if not ok:
                return Response(
                    message=f"Tweet {i + 1}/{total} too long: {char_count}/280 characters. Shorten it.",
                    break_loop=False,
                )
            validated.append(text)

        # Check write budget for all tweets
        from usr.plugins.x.helpers.x_auth import get_x_config, check_write_budget, get_usage, get_monthly_limit
        config = get_x_config(self.agent)
        usage = get_usage(config)
        monthly_limit = get_monthly_limit(config)
        posted = usage.get("tweets_posted", 0)

        if posted + total > monthly_limit:
            return Response(
                message=f"Error: Thread requires {total} tweets but only {monthly_limit - posted} remaining in budget.",
                break_loop=False,
            )

        from usr.plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            self.set_progress(f"Posting thread ({total} tweets)...")
            posted_ids = []
            reply_to = None

            for i, text in enumerate(validated):
                self.set_progress(f"Posting tweet {i + 1}/{total}...")
                result = await client.post_tweet(text=text, reply_to=reply_to)

                if result.get("error"):
                    if posted_ids:
                        return Response(
                            message=f"Thread partially posted ({len(posted_ids)}/{total}). "
                            f"Error on tweet {i + 1}: {result.get('detail', 'Unknown error')}\n"
                            f"Posted IDs: {', '.join(posted_ids)}",
                            break_loop=False,
                        )
                    return Response(
                        message=f"Error posting first tweet: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )

                new_id = result.get("data", {}).get("id")
                if not new_id:
                    return Response(
                        message=f"Error: No ID returned for tweet {i + 1}. Posted so far: {', '.join(posted_ids)}",
                        break_loop=False,
                    )
                posted_ids.append(new_id)
                reply_to = new_id

            return Response(
                message=f"Thread posted successfully ({total} tweets).\nFirst tweet ID: {posted_ids[0]}\nAll IDs: {', '.join(posted_ids)}",
                break_loop=False,
            )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
