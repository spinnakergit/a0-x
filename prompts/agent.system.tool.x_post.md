## Tool: x_post
Post tweets, replies, and quote tweets on X.com.

**Arguments:**
- **action** (str): "post" (default), "reply", or "quote"
- **text** (str, required): Tweet content (max 280 characters)
- **tweet_id** (str): Required for reply/quote — the tweet to reply to or quote
- **media_ids** (str): Comma-separated media IDs from x_media upload
- **poll_options** (str): Comma-separated poll choices (2-4 options, max 25 chars each)
- **poll_duration** (str): Poll duration in minutes (default: 1440 = 24 hours)

**Tier:** All tiers (write access)

**Examples:**
- Post: `action="post", text="Hello world!"`
- Reply: `action="reply", text="Great point!", tweet_id="1234567890"`
- Quote: `action="quote", text="This is interesting", tweet_id="1234567890"`
- With media: `action="post", text="Check this out", media_ids="1234567890"`
- With poll: `action="post", text="What do you think?", poll_options="Option A,Option B,Option C"`

**Notes:**
- Use x_thread for multi-tweet threads
- Use x_media to upload images/videos first, then pass the media_id here
- Tweet length is enforced at 280 characters
- Pay-Per-Use: ~$0.01/post. Legacy Free: 1,500/mo cap
