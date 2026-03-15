## Tool: x_analytics
View tweet and account analytics on X.com.

**Arguments:**
- **action** (str): "tweet" (default) or "account"
- **tweet_id** (str): Required for action="tweet" — the tweet to analyze

**Tier:** Requires Pay-Per-Use or Basic+ tier. Legacy Free tier does NOT support analytics.

**Examples:**
- Tweet metrics: `action="tweet", tweet_id="1234567890"`
- Account overview: `action="account"`

**Returns:**
- Tweet: impressions, likes, retweets, replies, quotes, bookmarks
- Account: follower/following counts, total tweets, monthly usage stats
