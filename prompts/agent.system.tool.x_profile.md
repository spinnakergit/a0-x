## Tool: x_profile
View X.com user profiles.

**Arguments:**
- **action** (str): "me" (default) or "lookup"
- **username** (str): Required for lookup — username without @ prefix

**Examples:**
- Own profile: `action="me"`
- Look up user: `action="lookup", username="elonmusk"`

**Returns:** Username, name, bio, location, follower/following counts, tweet count, join date.
