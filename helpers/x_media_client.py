"""
X.com media upload client using the v1.1 chunked upload endpoint.

Media upload uses OAuth 1.0a (not OAuth 2.0) because the /1.1/media/upload
endpoint requires it. This is a separate client from XClient which uses v2.

Upload flow (chunked):
1. INIT   — declare file size, type, category
2. APPEND — send file in chunks (up to 5 MB each)
3. FINALIZE — complete upload, get media_id
4. (optional) STATUS — poll processing for video/GIF

Reference: https://developer.x.com/en/docs/twitter-api/v1/media/upload-media/uploading-media/chunked-media-upload
"""

import asyncio
import os

UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB chunks


class XMediaClient:
    """Async chunked media upload client for X.com v1.1 API."""

    def __init__(self, config: dict):
        self.config = config
        self._session = None

    def _get_oauth1(self):
        """Build OAuth1 auth object for requests."""
        from requests_oauthlib import OAuth1
        from usr.plugins.x.helpers.x_auth import get_oauth1_credentials

        creds = get_oauth1_credentials(self.config)
        return OAuth1(
            creds["consumer_key"],
            creds["consumer_secret"],
            creds["access_token"],
            creds["access_token_secret"],
        )

    async def upload(
        self,
        file_path: str,
        media_type: str,
        media_category: str = "tweet_image",
    ) -> dict:
        """
        Upload a file using chunked upload.
        Returns dict with media_id_string on success or error dict on failure.
        """
        file_size = os.path.getsize(file_path)

        # INIT
        init_result = await self._init(file_size, media_type, media_category)
        if "error" in init_result:
            return init_result

        media_id = init_result.get("media_id_string", str(init_result.get("media_id", "")))
        if not media_id:
            return {"error": True, "detail": "No media_id in INIT response"}

        # APPEND chunks
        append_result = await self._append_chunks(media_id, file_path, file_size)
        if append_result and append_result.get("error"):
            return append_result

        # FINALIZE
        finalize_result = await self._finalize(media_id)
        if "error" in finalize_result:
            return finalize_result

        # Poll for processing if needed (video/GIF)
        processing = finalize_result.get("processing_info")
        if processing:
            poll_result = await self._poll_status(media_id, processing)
            if poll_result and poll_result.get("error"):
                return poll_result

        return finalize_result

    async def _init(self, file_size: int, media_type: str, media_category: str) -> dict:
        """INIT command: declare the upload."""
        import requests

        data = {
            "command": "INIT",
            "total_bytes": file_size,
            "media_type": media_type,
            "media_category": media_category,
        }
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(UPLOAD_URL, data=data, auth=self._get_oauth1(), timeout=30),
            )
            if resp.status_code >= 400:
                return {"error": True, "detail": f"INIT failed ({resp.status_code}): {resp.text}"}
            return resp.json()
        except Exception as e:
            return {"error": True, "detail": f"INIT error: {e}"}

    async def _append_chunks(self, media_id: str, file_path: str, file_size: int) -> dict:
        """APPEND command: send file in chunks."""
        import requests

        loop = asyncio.get_event_loop()
        segment = 0

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                try:
                    resp = await loop.run_in_executor(
                        None,
                        lambda chunk=chunk, segment=segment: requests.post(
                            UPLOAD_URL,
                            data={"command": "APPEND", "media_id": media_id, "segment_index": segment},
                            files={"media": chunk},
                            auth=self._get_oauth1(),
                            timeout=120,
                        ),
                    )
                    if resp.status_code >= 400:
                        return {"error": True, "detail": f"APPEND failed segment {segment} ({resp.status_code}): {resp.text}"}
                except Exception as e:
                    return {"error": True, "detail": f"APPEND error segment {segment}: {e}"}

                segment += 1

        return {}

    async def _finalize(self, media_id: str) -> dict:
        """FINALIZE command: complete the upload."""
        import requests

        data = {"command": "FINALIZE", "media_id": media_id}
        loop = asyncio.get_event_loop()

        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(UPLOAD_URL, data=data, auth=self._get_oauth1(), timeout=30),
            )
            if resp.status_code >= 400:
                return {"error": True, "detail": f"FINALIZE failed ({resp.status_code}): {resp.text}"}
            return resp.json()
        except Exception as e:
            return {"error": True, "detail": f"FINALIZE error: {e}"}

    async def _poll_status(self, media_id: str, processing_info: dict) -> dict:
        """Poll for video/GIF processing completion."""
        import requests

        check_after = processing_info.get("check_after_secs", 5)
        max_polls = 30  # Max ~150 seconds of polling
        loop = asyncio.get_event_loop()

        for _ in range(max_polls):
            await asyncio.sleep(check_after)

            try:
                resp = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        UPLOAD_URL,
                        params={"command": "STATUS", "media_id": media_id},
                        auth=self._get_oauth1(),
                        timeout=30,
                    ),
                )
                if resp.status_code >= 400:
                    return {"error": True, "detail": f"STATUS check failed ({resp.status_code}): {resp.text}"}

                result = resp.json()
                info = result.get("processing_info", {})
                state = info.get("state", "")

                if state == "succeeded":
                    return {}
                elif state == "failed":
                    error = info.get("error", {})
                    return {"error": True, "detail": f"Processing failed: {error.get('message', 'Unknown error')}"}

                check_after = info.get("check_after_secs", 5)
            except Exception as e:
                return {"error": True, "detail": f"STATUS poll error: {e}"}

        return {"error": True, "detail": "Processing timed out"}

    async def set_alt_text(self, media_id: str, alt_text: str) -> dict:
        """Set alt text on an uploaded media item."""
        import requests
        import json

        data = {
            "media_id": media_id,
            "alt_text": {"text": alt_text[:1000]},
        }
        loop = asyncio.get_event_loop()

        try:
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    "https://upload.twitter.com/1.1/media/metadata/create.json",
                    json=data,
                    auth=self._get_oauth1(),
                    timeout=15,
                ),
            )
            if resp.status_code >= 400:
                return {"error": True, "detail": f"Alt text failed ({resp.status_code}): {resp.text}"}
            return {"ok": True}
        except Exception as e:
            return {"error": True, "detail": f"Alt text error: {e}"}

    async def close(self):
        """Cleanup (no persistent session for requests-based client)."""
        pass
