## Tool: x_manage
Manage tweets and engagement on X.com: delete, like, unlike, retweet, unretweet, bookmark.

**Arguments:**
- **action** (str, required): "delete", "like", "unlike", "retweet", "unretweet", "bookmark", "unbookmark"
- **tweet_id** (str, required): The tweet ID to act on

**Tier:** All tiers (write access)

**Examples:**
- Like: `action="like", tweet_id="1234567890"`
- Retweet: `action="retweet", tweet_id="1234567890"`
- Delete own tweet: `action="delete", tweet_id="1234567890"`
- Bookmark: `action="bookmark", tweet_id="1234567890"`

**Notes:**
- Delete only works on your own tweets
- Like/retweet/bookmark work on any public tweet
