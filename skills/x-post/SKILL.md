---
name: x-post
description: Compose and publish tweets with optional media, polls, and engagement strategies
triggers:
  - post to x
  - tweet about
  - post on twitter
  - write a tweet
  - share on x
  - publish to x.com
allowed_tools:
  - x_post
  - x_media
  - x_profile
  - x_analytics
metadata:
  category: social_media
  platform: x.com
---

# X.com Post Workflow

Help the user compose and publish a tweet on X.com.

## Steps

### 1. Understand the Intent
- What does the user want to say?
- Is this a standalone tweet, a reply, or a quote tweet?
- Should it include media (images, video)?
- Should it include a poll?

### 2. Compose the Tweet
- Draft the tweet text (max 280 characters)
- Optimize for engagement: clear message, strong hook, relevant hashtags
- If the content is too long, suggest using `x_thread` instead
- Consider the user's audience and tone

### 3. Handle Media (if needed)
- If the user wants to include an image or video, use `x_media` to upload first
- Note the returned `media_id` for attachment
- Add alt text for accessibility when possible

### 4. Post the Tweet
- Use `x_post` with the appropriate action (post, reply, quote)
- Include media_ids if media was uploaded
- Include poll_options and poll_duration if a poll is requested

### 5. Confirm and Follow Up
- Report the posted tweet ID
- If analytics are available (Pay-Per-Use or Basic+ tier), offer to check engagement later
- Suggest follow-up actions (pin tweet, create thread, etc.)

## Best Practices
- Keep tweets concise and punchy — shorter tweets often perform better
- Use 1-3 relevant hashtags, not more
- Ask before posting — always confirm the final text with the user
- Check usage budget with `x_analytics action="account"` if posting frequently
