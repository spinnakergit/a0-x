## Tool: x_media
Upload media (images, videos, GIFs) to X.com for use in tweets.

**Arguments:**
- **action** (str): "upload" (default)
- **file_path** (str, required): Path to the file to upload (must be in /a0/, /tmp/, or /git/)
- **media_type** (str): MIME type (auto-detected from extension if omitted)
- **alt_text** (str): Accessibility alt text (max 1000 chars)

**Tier:** All tiers (requires OAuth 1.0a credentials)

**Supported formats:**
- Images: .jpg, .jpeg, .png, .gif, .webp (max 5 MB)
- GIFs: .gif (max 15 MB)
- Videos: .mp4, .mov (max 512 MB)

**Example:**
- Upload image: `file_path="/a0/files/photo.jpg", alt_text="A sunset over the ocean"`

**Returns:** media_id to use with x_post's media_ids parameter.

**Notes:**
- Requires OAuth 1.0a credentials (API Key + Secret + Access Token + Secret)
- Upload media first, then reference the media_id in x_post
- Videos may take time to process before they can be attached to tweets
