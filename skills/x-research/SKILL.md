---
name: x-research
description: Research topics, users, and trends on X.com using search and read tools
triggers:
  - search x for
  - find tweets about
  - research on twitter
  - what are people saying about
  - look up on x
  - x.com trends
  - twitter search
allowed_tools:
  - x_search
  - x_read
  - x_profile
  - x_analytics
metadata:
  category: social_media
  platform: x.com
---

# X.com Research Workflow

Help the user research topics, users, and conversations on X.com.

## Steps

### 1. Clarify Research Goal
- What topic, keyword, or user is the user interested in?
- Are they looking for specific tweets, general sentiment, or user profiles?
- Do they want recent activity or historical context?

### 2. Check Tier Availability
- Search and read require **Pay-Per-Use** (credit-based) or **Basic+** (legacy subscription)
- If on legacy Free tier, inform the user and recommend switching to Pay-Per-Use at developer.x.com
- Profile lookup works on all tiers

### 3. Execute Research
Depending on the goal:

**Topic Research:**
- Use `x_search` with relevant query and search operators
- Try both relevancy and recency sort orders
- Use operators like `from:username`, `#hashtag`, `lang:en`, `-is:retweet`

**User Research:**
- Use `x_profile action="lookup"` to get user details
- Use `x_read action="user_tweets"` to see their recent tweets
- Use `x_analytics action="tweet"` on their popular tweets

**Conversation Tracking:**
- Use `x_read action="mentions"` to see who's talking to/about the user
- Use `x_read action="timeline"` for home timeline context

### 4. Synthesize Findings
- Summarize key themes and sentiments
- Highlight notable tweets with high engagement
- Identify key voices and influencers in the conversation
- Note any trends or patterns

### 5. Suggest Actions
- Engage with relevant tweets (like, retweet, reply)
- Create original content responding to trends
- Follow up on promising conversations

## Search Operator Quick Reference
- `from:user` — tweets by a specific user
- `to:user` — replies to a specific user
- `#hashtag` — tweets with a hashtag
- `"exact phrase"` — exact phrase match
- `lang:en` — filter by language
- `-is:retweet` — exclude retweets
- `has:media` — only tweets with media
- `min_faves:100` — minimum likes
