---
name: x-thread
description: Create and publish multi-tweet threads on X.com from long-form content
triggers:
  - create a thread on x
  - post a twitter thread
  - turn this into a thread
  - write a thread about
  - x thread
  - tweet thread
allowed_tools:
  - x_thread
  - x_post
  - x_media
  - x_analytics
metadata:
  category: social_media
  platform: x.com
---

# X.com Thread Workflow

Help the user create and publish engaging multi-tweet threads.

## Steps

### 1. Gather Content
- What is the user's topic or source material?
- How detailed should the thread be?
- Should it include a call-to-action at the end?

### 2. Plan the Thread Structure
A good thread follows this pattern:
1. **Hook** (Tweet 1) — Grab attention. Make people want to read more.
2. **Body** (Tweets 2-N) — Deliver value. One idea per tweet.
3. **Conclusion** (Last tweet) — Summarize or call-to-action.

### 3. Compose Each Tweet
- Keep each tweet under 260 characters (leave room for numbering: "1/N ")
- Each tweet should be self-contained enough to make sense alone
- Use line breaks for readability within tweets
- Maximum 25 tweets per thread

### 4. Review with User
- Present the full thread for review before posting
- Show character counts for each tweet
- Confirm numbering preference (1/N format)

### 5. Post the Thread
- Use `x_thread` with tweets separated by `|||`
- Set `numbering="true"` for numbered threads (recommended for educational content)
- Set `numbering="false"` for narrative threads

### 6. Follow Up
- Report all posted tweet IDs
- The first tweet ID is the "anchor" — this is what people share
- Suggest pinning the first tweet if it's evergreen content
- Check budget impact with `x_analytics action="account"`

## Thread Writing Tips
- First tweet is CRITICAL — it determines if people read the rest
- Use numbers and lists within tweets for scannability
- End with a clear CTA: "Follow for more", "What do you think?", "RT to share"
- 5-10 tweets is the sweet spot. Under 5 isn't a thread. Over 15 loses readers.
- If including media, upload with `x_media` first, then post individual tweets with `x_post` instead of `x_thread`
