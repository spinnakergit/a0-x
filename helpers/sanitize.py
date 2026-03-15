"""
Tweet content sanitization and validation.

Handles: text length enforcement, injection defense, content formatting,
username validation, tweet ID validation, and output formatting for LLM.
"""

import re
import unicodedata

MAX_TWEET_LENGTH = 280
MAX_BIO_LENGTH = 160
MAX_POLL_OPTIONS = 4
MAX_POLL_OPTION_LENGTH = 25
MAX_THREAD_TWEETS = 25
MAX_BULK_CHARS = 200_000


def sanitize_tweet_text(text: str) -> str:
    """Normalize and clean tweet text for posting."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    # Strip zero-width characters
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff\u180e\u00ad\u2061-\u2064\u2066-\u2069]", "", text)
    text = text.strip()
    return text


def validate_tweet_length(text: str) -> tuple:
    """
    Check tweet length. Returns (ok, char_count).
    X counts URLs as 23 chars regardless of actual length.
    """
    # Simplified: count actual chars. Full t.co resolution would need API call.
    count = len(text)
    return (count <= MAX_TWEET_LENGTH, count)


def sanitize_tweet_content(text: str) -> str:
    """
    Sanitize external tweet content before passing to LLM.
    Strips potential prompt injection patterns from tweet text.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    # Strip zero-width chars that could hide injection
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff\u180e\u00ad\u2061-\u2064\u2066-\u2069]", "", text)
    # Strip excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_tweet_id(tweet_id: str) -> str:
    """Validate and clean a tweet ID (numeric string)."""
    if not tweet_id:
        return ""
    tweet_id = str(tweet_id).strip()
    if not re.match(r"^\d{1,20}$", tweet_id):
        raise ValueError(f"Invalid tweet ID: {tweet_id}")
    return tweet_id


def validate_username(username: str) -> str:
    """Validate X username (alphanumeric + underscores, max 15 chars)."""
    if not username:
        return ""
    username = username.strip().lstrip("@")
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", username):
        raise ValueError(f"Invalid username: @{username}")
    return username


def validate_poll_options(options: list) -> list:
    """Validate poll options (2-4 choices, each max 25 chars)."""
    if len(options) < 2:
        raise ValueError("Polls require at least 2 options")
    if len(options) > MAX_POLL_OPTIONS:
        raise ValueError(f"Polls support at most {MAX_POLL_OPTIONS} options")
    cleaned = []
    for opt in options:
        opt = str(opt).strip()
        if len(opt) > MAX_POLL_OPTION_LENGTH:
            raise ValueError(
                f"Poll option too long ({len(opt)} chars, max {MAX_POLL_OPTION_LENGTH}): {opt[:30]}..."
            )
        if not opt:
            raise ValueError("Poll options cannot be empty")
        cleaned.append(opt)
    return cleaned


def truncate_for_llm(text: str, max_length: int = MAX_BULK_CHARS) -> str:
    """Truncate text for safe LLM consumption."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n\n[Truncated — showing {max_length:,} of {len(text):,} chars]"


def format_tweet(tweet: dict, include_id: bool = True) -> str:
    """Format a single tweet dict for LLM display."""
    author = tweet.get("author", tweet.get("username", "unknown"))
    text = sanitize_tweet_content(tweet.get("text", ""))
    created = tweet.get("created_at", "")
    metrics = tweet.get("public_metrics", {})

    parts = []
    if include_id:
        parts.append(f"[{tweet.get('id', '?')}]")
    parts.append(f"@{author}")
    if created:
        parts.append(f"({created})")
    parts.append(f"\n{text}")

    if metrics:
        stats = []
        for key in ["like_count", "retweet_count", "reply_count", "impression_count"]:
            if key in metrics:
                label = key.replace("_count", "").replace("impression", "views")
                stats.append(f"{metrics[key]} {label}s")
        if stats:
            parts.append(f"\n  [{', '.join(stats)}]")

    return " ".join(parts[:3]) + "".join(parts[3:])


def format_tweets(tweets: list, include_ids: bool = True) -> str:
    """Format a list of tweets for LLM display."""
    if not tweets:
        return "No tweets found."
    lines = []
    for i, tweet in enumerate(tweets, 1):
        lines.append(f"{i}. {format_tweet(tweet, include_id=include_ids)}")
    result = "\n\n".join(lines)
    return truncate_for_llm(result)
