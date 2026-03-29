from helpers.tool import Tool, Response


class XPost(Tool):
    """Post tweets, replies, and quote tweets on X.com."""

    async def execute(self, **kwargs) -> Response:
        # Service toggle guard
        from usr.plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("posting", self.agent):
            return Response(
                message="Posting service is disabled. Enable it in X.com plugin settings.",
                break_loop=False,
            )

        action = self.args.get("action", "post")
        text = self.args.get("text", "")
        tweet_id = self.args.get("tweet_id", "")
        media_ids = self.args.get("media_ids", "")
        poll_options = self.args.get("poll_options", "")
        poll_duration = self.args.get("poll_duration", "1440")

        if not text:
            return Response(message="Error: 'text' is required.", break_loop=False)

        # Sanitize and validate
        from usr.plugins.x.helpers.sanitize import (
            sanitize_tweet_text,
            validate_tweet_length,
            validate_tweet_id,
            validate_poll_options,
        )

        text = sanitize_tweet_text(text)
        ok, char_count = validate_tweet_length(text)
        if not ok:
            return Response(
                message=f"Tweet too long: {char_count}/280 characters. Shorten the text or use x_thread for longer content.",
                break_loop=False,
            )

        # Check write budget
        from usr.plugins.x.helpers.x_auth import get_x_config, check_write_budget
        config = get_x_config(self.agent)
        can_write, budget_msg = check_write_budget(config)
        if not can_write:
            return Response(message=f"Error: {budget_msg}", break_loop=False)

        # Build client and post
        from usr.plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            self.set_progress("Posting tweet...")

            # Parse optional fields
            parsed_media_ids = (
                [m.strip() for m in media_ids.split(",") if m.strip()]
                if media_ids
                else None
            )

            parsed_poll = None
            parsed_duration = int(poll_duration)
            if poll_options:
                opts = [o.strip() for o in poll_options.split(",") if o.strip()]
                parsed_poll = validate_poll_options(opts)

            reply_to = None
            quote_id = None

            if action == "reply":
                if not tweet_id:
                    return Response(
                        message="Error: 'tweet_id' is required for replies.",
                        break_loop=False,
                    )
                reply_to = validate_tweet_id(tweet_id)
            elif action == "quote":
                if not tweet_id:
                    return Response(
                        message="Error: 'tweet_id' is required for quote tweets.",
                        break_loop=False,
                    )
                quote_id = validate_tweet_id(tweet_id)

            result = await client.post_tweet(
                text=text,
                reply_to=reply_to,
                quote_tweet_id=quote_id,
                media_ids=parsed_media_ids,
                poll_options=parsed_poll,
                poll_duration=parsed_duration,
            )

            if result.get("error"):
                return Response(
                    message=f"Error posting tweet: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            tweet_data = result.get("data", {})
            new_id = tweet_data.get("id", "unknown")
            action_label = {"post": "Tweet", "reply": "Reply", "quote": "Quote tweet"}.get(action, "Tweet")

            if budget_msg:
                return Response(
                    message=f"{action_label} posted successfully (ID: {new_id}).\n{budget_msg}",
                    break_loop=False,
                )

            return Response(
                message=f"{action_label} posted successfully (ID: {new_id}).",
                break_loop=False,
            )
        except ValueError as e:
            return Response(message=f"Validation error: {e}", break_loop=False)
        finally:
            await client.close()
