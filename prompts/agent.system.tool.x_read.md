## Tool: x_read
Read tweets, timelines, and mentions from X.com.

**Arguments:**
- **action** (str): "tweet" (default), "user_tweets", "timeline", "mentions"
- **tweet_id** (str): Required for action="tweet" — specific tweet to read
- **username** (str): Required for action="user_tweets" — whose tweets to read
- **max_results** (str): Number of results (default: 20, max: 100)

**Tier:** Requires Pay-Per-Use or Basic+ tier. Legacy Free tier does NOT support read operations.

**Examples:**
- Read specific tweet: `action="tweet", tweet_id="1234567890"`
- User's tweets: `action="user_tweets", username="elonmusk", max_results="10"`
- Home timeline: `action="timeline", max_results="20"`
- Mentions: `action="mentions"`

**Notes:**
- Legacy Free tier does NOT support read operations — use Pay-Per-Use or upgrade
- For search, use x_search instead
