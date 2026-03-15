---
name: x-engage
description: Engage with content on X.com — like, retweet, reply, bookmark, and build presence
triggers:
  - engage with tweets
  - like tweets about
  - retweet
  - interact on x
  - build x presence
  - bookmark tweets
  - reply to tweets
allowed_tools:
  - x_manage
  - x_post
  - x_read
  - x_search
  - x_profile
metadata:
  category: social_media
  platform: x.com
---

# X.com Engagement Workflow

Help the user engage with content and build their X.com presence.

## Steps

### 1. Identify Engagement Target
- Is the user responding to specific tweets?
- Are they doing general engagement in a niche/topic?
- Do they want to engage with a specific user's content?

### 2. Find Content to Engage With
If no specific tweets are provided:
- Use `x_search` to find relevant tweets in the user's niche
- Use `x_read action="mentions"` to find unanswered mentions
- Use `x_read action="timeline"` for timeline content

### 3. Execute Engagement
For each piece of content:

**Passive Engagement:**
- `x_manage action="like"` — show appreciation
- `x_manage action="retweet"` — amplify to your audience
- `x_manage action="bookmark"` — save for later reference

**Active Engagement:**
- `x_post action="reply"` — add thoughtful commentary
- `x_post action="quote"` — share with your own perspective

### 4. Engagement Best Practices
- **Be genuine** — don't just like-spam. Add value with replies.
- **Be consistent** — regular engagement beats burst activity
- **Be strategic** — engage with accounts in your niche
- **Add value** — replies should contribute to the conversation
- **Don't over-engage** — 20-30 meaningful interactions per session is plenty

### 5. Report Results
- Summarize actions taken (X likes, Y retweets, Z replies)
- Check remaining budget with `x_analytics action="account"`
- Note any particularly promising conversations to follow up on
