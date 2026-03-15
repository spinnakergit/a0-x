## Tool: x_thread
Post a thread (multiple connected tweets) on X.com.

**Arguments:**
- **tweets** (str, required): Tweets separated by "|||" or as a JSON array
- **numbering** (str): "true" (default) or "false" — add 1/N numbering prefix

**Tier:** All tiers (write access)

**Examples:**
- Delimiter format: `tweets="First tweet|||Second tweet|||Third tweet"`
- JSON format: `tweets='["First tweet", "Second tweet", "Third tweet"]'`
- No numbering: `tweets="First|||Second", numbering="false"`

**Notes:**
- Minimum 2 tweets, maximum 25 tweets per thread
- Each tweet must be under 280 characters (including numbering if enabled)
- If numbering is on, "1/3 " prefix is added (uses ~5 chars)
- Budget check ensures enough quota for all tweets before starting
- If a tweet fails mid-thread, you'll get partial results with posted IDs
- For single tweets, use x_post instead
