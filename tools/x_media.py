from helpers.tool import Tool, Response


class XMedia(Tool):
    """Upload media (images, videos, GIFs) to X.com for use in tweets."""

    async def execute(self, **kwargs) -> Response:
        from usr.plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("media", self.agent):
            return Response(
                message="Media service is disabled. Enable it in X.com plugin settings.",
                break_loop=False,
            )

        action = self.args.get("action", "upload")
        file_path = self.args.get("file_path", "")
        media_type = self.args.get("media_type", "")
        alt_text = self.args.get("alt_text", "")

        if action == "upload":
            if not file_path:
                return Response(message="Error: 'file_path' is required for upload.", break_loop=False)

            import os
            if not os.path.isfile(file_path):
                return Response(message=f"Error: File not found: {file_path}", break_loop=False)

            # Security: restrict to safe paths
            real_path = os.path.realpath(file_path)
            allowed_prefixes = ["/a0/", "/tmp/", "/git/"]
            if not any(real_path.startswith(p) for p in allowed_prefixes):
                return Response(
                    message="Error: File path not allowed. Files must be in /a0/, /tmp/, or /git/.",
                    break_loop=False,
                )

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return Response(message="Error: File is empty.", break_loop=False)

            # Detect media type from extension if not provided
            if not media_type:
                ext = os.path.splitext(file_path)[1].lower()
                type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".mp4": "video/mp4",
                    ".mov": "video/quicktime",
                }
                media_type = type_map.get(ext, "")
                if not media_type:
                    return Response(
                        message=f"Error: Cannot determine media type for '{ext}'. "
                        "Provide 'media_type' explicitly (e.g., 'image/jpeg', 'video/mp4').",
                        break_loop=False,
                    )

            # Validate size limits
            is_video = media_type.startswith("video/")
            is_gif = media_type == "image/gif"
            max_size = 512 * 1024 * 1024 if is_video else (15 * 1024 * 1024 if is_gif else 5 * 1024 * 1024)
            if file_size > max_size:
                limit_mb = max_size / (1024 * 1024)
                actual_mb = file_size / (1024 * 1024)
                return Response(
                    message=f"Error: File too large ({actual_mb:.1f} MB, max {limit_mb:.0f} MB for {media_type}).",
                    break_loop=False,
                )

            from usr.plugins.x.helpers.x_auth import get_x_config, has_oauth1
            config = get_x_config(self.agent)

            if not has_oauth1(config):
                return Response(
                    message="Error: Media upload requires OAuth 1.0a credentials. "
                    "Configure api_key, api_secret, access_token, and access_token_secret in settings.",
                    break_loop=False,
                )

            from usr.plugins.x.helpers.x_media_client import XMediaClient
            media_client = XMediaClient(config)

            try:
                category = "tweet_video" if is_video else ("tweet_gif" if is_gif else "tweet_image")
                self.set_progress(f"Uploading {media_type} ({file_size / 1024:.0f} KB)...")

                result = await media_client.upload(
                    file_path=file_path,
                    media_type=media_type,
                    media_category=category,
                )

                if result.get("error"):
                    return Response(
                        message=f"Upload error: {result.get('detail', 'Unknown error')}",
                        break_loop=False,
                    )

                media_id = result.get("media_id_string", result.get("media_id", ""))
                if not media_id:
                    return Response(message="Error: No media ID returned.", break_loop=False)

                # Set alt text if provided
                if alt_text and media_id:
                    await media_client.set_alt_text(media_id, alt_text[:1000])

                msg = f"Media uploaded successfully (ID: {media_id})."
                msg += f"\nUse this media_id with x_post: media_ids=\"{media_id}\""
                if is_video:
                    msg += "\nNote: Video may take a moment to process before it can be used."

                return Response(message=msg, break_loop=False)
            finally:
                await media_client.close()

        else:
            return Response(
                message=f"Error: Unknown action '{action}'. Use: upload.",
                break_loop=False,
            )
