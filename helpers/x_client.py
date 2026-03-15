"""
X.com API v2 client wrapper with rate limiting, retry logic, and tier awareness.
"""

import asyncio
import time
import json
import aiohttp

API_BASE = "https://api.twitter.com/2"


class XRateLimiter:
    """Track per-endpoint rate limits from X API response headers."""

    def __init__(self):
        self._limits = {}
        self._lock = asyncio.Lock()

    async def wait(self, endpoint: str):
        """Block if endpoint is currently rate-limited."""
        async with self._lock:
            info = self._limits.get(endpoint)
            if info and info["remaining"] <= 0:
                wait_time = info["reset_at"] - time.time()
                if wait_time > 0:
                    await asyncio.sleep(min(wait_time, 60))

    def update(self, endpoint: str, headers: dict):
        """Update rate limit state from response headers."""
        remaining = headers.get("x-rate-limit-remaining")
        reset = headers.get("x-rate-limit-reset")
        if remaining is not None and reset is not None:
            self._limits[endpoint] = {
                "remaining": int(remaining),
                "reset_at": int(reset),
            }


class XClient:
    """Async X.com API v2 client."""

    def __init__(self, config: dict):
        self.config = config
        self._session = None
        self._rate_limiter = XRateLimiter()

    @classmethod
    def from_config(cls, agent=None):
        """Factory: create client from A0 plugin config."""
        from plugins.x.helpers.x_auth import get_x_config
        config = get_x_config(agent)
        return cls(config)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self) -> dict:
        """Get auth headers for API v2 requests (OAuth 2.0 or Bearer)."""
        from plugins.x.helpers.x_auth import get_oauth2_headers
        headers = get_oauth2_headers(self.config)
        headers["Content-Type"] = "application/json"
        return headers

    def _use_oauth1(self) -> bool:
        """Check if we should use OAuth 1.0a for API v2 calls."""
        from plugins.x.helpers.x_auth import get_oauth2_headers, has_oauth1
        headers = get_oauth2_headers(self.config)
        # Use OAuth 1.0a when no OAuth 2.0 token or Bearer token is available
        return "Authorization" not in headers and has_oauth1(self.config)

    async def _oauth1_request(
        self, method: str, url: str, json_body: dict = None, params: dict = None
    ) -> dict:
        """Make a request using OAuth 1.0a (via requests in executor)."""
        import requests
        from requests_oauthlib import OAuth1
        from plugins.x.helpers.x_auth import get_oauth1_credentials

        creds = get_oauth1_credentials(self.config)
        auth = OAuth1(
            creds["consumer_key"],
            creds["consumer_secret"],
            creds["access_token"],
            creds["access_token_secret"],
        )

        loop = asyncio.get_event_loop()

        def _do_request():
            kwargs = {"auth": auth, "timeout": 30}
            if params:
                kwargs["params"] = params
            if json_body is not None:
                kwargs["json"] = json_body
                kwargs["headers"] = {"Content-Type": "application/json"}
            return getattr(requests, method.lower())(url, **kwargs)

        resp = await loop.run_in_executor(None, _do_request)
        self._rate_limiter.update(url, dict(resp.headers))

        if resp.status_code == 429:
            return {"error": True, "status": 429, "detail": "Rate limited"}
        if resp.status_code >= 400:
            return {"error": True, "status": resp.status_code, "detail": resp.text}
        if resp.text:
            return resp.json()
        return {"ok": True}

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_body: dict = None,
        params: dict = None,
        max_retries: int = 3,
    ) -> dict:
        """Core request method with rate limiting and retry on 429."""
        url = f"{API_BASE}{endpoint}"

        # Use OAuth 1.0a when no OAuth 2.0/Bearer token is available
        if self._use_oauth1():
            for attempt in range(max_retries):
                await self._rate_limiter.wait(endpoint)
                try:
                    result = await self._oauth1_request(
                        method, url, json_body, params
                    )
                    if result.get("status") == 429 and attempt < max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    return result
                except Exception as e:
                    if attempt == max_retries - 1:
                        return {"error": True, "detail": str(e)}
                    await asyncio.sleep(2 ** attempt)
            return {"error": True, "detail": "Max retries exceeded"}

        # OAuth 2.0 / Bearer path (aiohttp)
        headers = self._get_headers()
        session = await self._get_session()

        for attempt in range(max_retries):
            await self._rate_limiter.wait(endpoint)

            try:
                async with session.request(
                    method, url, headers=headers, json=json_body, params=params
                ) as resp:
                    self._rate_limiter.update(endpoint, dict(resp.headers))

                    if resp.status == 429:
                        retry_after = resp.headers.get("retry-after", "5")
                        wait = min(int(retry_after), 60) * (attempt + 1)
                        await asyncio.sleep(wait)
                        continue

                    body = await resp.text()
                    if resp.status >= 400:
                        return {
                            "error": True,
                            "status": resp.status,
                            "detail": body,
                        }

                    if body:
                        return json.loads(body)
                    return {"ok": True}
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    return {"error": True, "detail": str(e)}
                await asyncio.sleep(2 ** attempt)

        return {"error": True, "detail": "Max retries exceeded"}

    # --- Tweet Operations ---

    async def post_tweet(
        self,
        text: str,
        reply_to: str = None,
        quote_tweet_id: str = None,
        media_ids: list = None,
        poll_options: list = None,
        poll_duration: int = 1440,
    ) -> dict:
        """Post a tweet."""
        body = {"text": text}

        if reply_to:
            body["reply"] = {"in_reply_to_tweet_id": reply_to}
        if quote_tweet_id:
            body["quote_tweet_id"] = quote_tweet_id
        if media_ids:
            body["media"] = {"media_ids": media_ids}
        if poll_options:
            body["poll"] = {
                "options": [{"label": opt} for opt in poll_options],
                "duration_minutes": poll_duration,
            }

        result = await self._request("POST", "/tweets", json_body=body)

        if not result.get("error"):
            from plugins.x.helpers.x_auth import increment_usage
            increment_usage(self.config)

        return result

    async def delete_tweet(self, tweet_id: str) -> dict:
        """Delete a tweet by ID."""
        result = await self._request("DELETE", f"/tweets/{tweet_id}")
        if not result.get("error"):
            from plugins.x.helpers.x_auth import increment_usage
            increment_usage(self.config, "tweets_deleted")
        return result

    async def get_tweet(self, tweet_id: str, tweet_fields: str = None) -> dict:
        """Get a specific tweet by ID."""
        params = {
            "tweet.fields": tweet_fields
            or "author_id,created_at,public_metrics,conversation_id"
        }
        return await self._request("GET", f"/tweets/{tweet_id}", params=params)

    # --- User Operations ---

    async def get_user_me(self, user_fields: str = None) -> dict:
        """Get authenticated user's profile."""
        params = {
            "user.fields": user_fields
            or "username,name,description,public_metrics,profile_image_url,created_at"
        }
        return await self._request("GET", "/users/me", params=params)

    async def get_user_by_username(self, username: str, user_fields: str = None) -> dict:
        """Look up a user by username."""
        params = {
            "user.fields": user_fields
            or "username,name,description,public_metrics,profile_image_url"
        }
        return await self._request(
            "GET", f"/users/by/username/{username}", params=params
        )

    async def get_user_tweets(self, user_id: str, max_results: int = 20) -> dict:
        """Get tweets from a specific user."""
        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,conversation_id",
        }
        return await self._request("GET", f"/users/{user_id}/tweets", params=params)

    # --- Timeline and Mentions ---

    async def get_home_timeline(self, user_id: str, max_results: int = 20) -> dict:
        """Get home timeline (Pay-Per-Use or Basic+ tier required)."""
        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "author_id,created_at,public_metrics",
        }
        return await self._request(
            "GET",
            f"/users/{user_id}/timelines/reverse_chronological",
            params=params,
        )

    async def get_mentions(self, user_id: str, max_results: int = 20) -> dict:
        """Get mentions (Pay-Per-Use or Basic+ tier required)."""
        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "author_id,created_at,public_metrics",
        }
        return await self._request(
            "GET", f"/users/{user_id}/mentions", params=params
        )

    # --- Search ---

    async def search_recent(
        self, query: str, max_results: int = 20, sort_order: str = "relevancy"
    ) -> dict:
        """Search recent tweets (Pay-Per-Use or Basic+ tier required)."""
        params = {
            "query": query,
            "max_results": min(max(max_results, 10), 100),
            "sort_order": sort_order,
            "tweet.fields": "author_id,created_at,public_metrics",
        }
        return await self._request("GET", "/tweets/search/recent", params=params)

    # --- Engagement ---

    async def like_tweet(self, user_id: str, tweet_id: str) -> dict:
        """Like a tweet."""
        return await self._request(
            "POST", f"/users/{user_id}/likes", json_body={"tweet_id": tweet_id}
        )

    async def unlike_tweet(self, user_id: str, tweet_id: str) -> dict:
        """Unlike a tweet."""
        return await self._request("DELETE", f"/users/{user_id}/likes/{tweet_id}")

    async def retweet(self, user_id: str, tweet_id: str) -> dict:
        """Retweet a tweet."""
        return await self._request(
            "POST", f"/users/{user_id}/retweets", json_body={"tweet_id": tweet_id}
        )

    async def unretweet(self, user_id: str, tweet_id: str) -> dict:
        """Remove a retweet."""
        return await self._request(
            "DELETE", f"/users/{user_id}/retweets/{tweet_id}"
        )

    async def bookmark(self, user_id: str, tweet_id: str) -> dict:
        """Bookmark a tweet."""
        return await self._request(
            "POST", f"/users/{user_id}/bookmarks", json_body={"tweet_id": tweet_id}
        )

    async def unbookmark(self, user_id: str, tweet_id: str) -> dict:
        """Remove a bookmark."""
        return await self._request(
            "DELETE", f"/users/{user_id}/bookmarks/{tweet_id}"
        )
