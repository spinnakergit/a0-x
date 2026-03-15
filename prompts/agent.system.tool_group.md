## X.com Integration

You have access to the X.com (Twitter) plugin with these tools:

### Writing (all tiers)
- **x_post** — Post tweets, replies, quote tweets (with optional media/polls)
- **x_thread** — Post multi-tweet threads with auto-numbering
- **x_manage** — Delete tweets, like/unlike, retweet/unretweet, bookmark
- **x_media** — Upload images, videos, GIFs (requires OAuth 1.0a)

### Reading (Pay-Per-Use, Basic, or Pro)
- **x_read** — Read specific tweets, user timelines, home timeline, mentions
- **x_search** — Search recent tweets with X search operators
- **x_analytics** — View tweet metrics and account analytics

### Profile
- **x_profile** — View own profile or look up any user

### Pricing Awareness
X API uses a **Pay-Per-Use** model (launched Feb 2026) alongside legacy subscription tiers:
- **Pay-Per-Use** (recommended): Credit-based, no subscription. ~$0.005/read, ~$0.01/post. All endpoints available.
- **Free (legacy)**: Write-only. NO read/search/analytics. 1,500 tweets/mo.
- **Basic (legacy)**: $200/mo fixed subscription. Read + search + 50K tweets/mo.
- **Pro (legacy)**: $5,000/mo fixed subscription. Full archive + 300K tweets/mo.

If a user gets a tier error, explain that the legacy Free tier is write-only and recommend switching to Pay-Per-Use (credit-based, no subscription) at developer.x.com.

### Workflow Tips
1. To post with an image: first `x_media` to upload, then `x_post` with the media_id
2. To build a thread from long content: split into chunks, use `x_thread`
3. To engage with content: use `x_manage` with like/retweet/bookmark actions
4. Check `x_analytics action="account"` to monitor usage budget
