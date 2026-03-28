# X.com Integration Plugin — Setup Guide

## Requirements

- Agent Zero v2026-03-13 or later
- Docker or local Python 3.10+
- X.com Developer Account ([developer.x.com](https://developer.x.com))

## Dependencies

Installed automatically by `initialize.py`:
- `aiohttp` — Async HTTP client for API v2
- `requests-oauthlib` — OAuth 1.0a for media upload
- `pyyaml` — Config parsing

## Installation

### Option A: Install Script

```bash
# Copy plugin to container and run install
docker cp a0-x/. a0-container:/a0/usr/plugins/x/
docker exec a0-container bash /a0/usr/plugins/x/install.sh
```

### Option B: Manual Installation

```bash
# Copy files
docker cp a0-x/. a0-container:/a0/usr/plugins/x/

# Create symlink
docker exec a0-container ln -sf /a0/usr/plugins/x /a0/plugins/x

# Install dependencies
docker exec a0-container /opt/venv-a0/bin/python /a0/usr/plugins/x/initialize.py

# Enable the plugin
docker exec a0-container touch /a0/usr/plugins/x/.toggle-1

# Restart
docker exec a0-container supervisorctl restart run_ui
```

## X Developer Account Setup

### 0. Developer Onboarding

Before creating an app, you must complete the X Developer onboarding:

1. Go to [console.x.com/onboarding](https://console.x.com/onboarding)
2. Review and accept the following agreements:
   - **Developer Agreement** — License terms, data handling obligations, termination rights
   - **Incorporated Developer Terms** — Technical and operational requirements
   - **X Developer Policy** — Permitted/restricted uses, automation rules, privacy requirements
3. Complete your developer profile
4. When prompted to **"Describe all of your use cases of X's data and API"**, provide a description of how you intend to use the API. Your use case description is binding per the Developer Agreement — substantive deviations may constitute a violation.

#### Sample Use Case Description

Below is a sample you can adapt to fit your specific needs:

> Personal content management and engagement on X via an AI assistant (Agent Zero). The application enables a single authenticated user to:
>
> - Compose and post tweets, threads, and replies on their own account
> - Schedule posts via the assistant's task scheduling capability
> - Upload images, videos, and GIFs as media attachments
> - Read and search public tweets for topic research and conversation discovery
> - View engagement analytics (likes, retweets, impressions) on own posts
> - Manage engagement actions (like, retweet, bookmark) on individual posts
> - Look up public user profiles
>
> Posts may be scheduled or coordinated through the assistant's automation features, but all content is authored or approved by the account owner. No bulk operations or multi-account management. No DM access. No data is cached offline or used for training AI models. OAuth 2.0 PKCE is used for authentication.

#### Key Policy Requirements

By accepting these agreements, you are committing to:

- **No spam or platform manipulation** — No bulk following, coordinated posting across accounts, or identical content on multiple accounts
- **Explicit user consent** — Obtain consent before taking actions on behalf of users or sending automated messages
- **Content integrity** — Do not modify tweet content; remove deleted/protected content within 24 hours
- **Credential security** — Keep all API keys and tokens private; use OAuth authentication (never store passwords)
- **Rate limit compliance** — Respect all API rate limits; do not attempt to circumvent them
- **No sensitive data derivation** — Do not infer health, political affiliation, ethnicity, religion, or sexual orientation from user data
- **No AI training** — Do not use X content to fine-tune or train foundation models
- **No surveillance** — Do not use the API for user tracking, background checks, or monitoring
- **Bot disclosure** — If operating an automated account, clearly identify it as a bot in the account bio
- **Privacy policy** — Your use of X data must be covered by a privacy policy no less protective than X's own
- **Use case binding** — Your described use case during onboarding is binding; substantive deviations may violate the agreement

> **Note:** This plugin is designed to comply with all of the above. It enforces rate limits, uses OAuth authentication, does not cache content offline, and its agent prompts discourage spam and inauthentic engagement. However, **you as the account operator** are ultimately responsible for how you use the API.

Full policy documents:
- [Developer Agreement](https://developer.x.com/en/developer-terms/agreement)
- [Developer Policy](https://developer.x.com/en/developer-terms/policy)
- [Restricted Use Cases](https://developer.x.com/en/developer-terms/restricted-use-cases)

### 1. Create a Project and App

1. Go to [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Click "Create Project" (or use an existing project)
3. Create an App within the project
4. Note your pricing tier:
   - **Pay-Per-Use** (recommended) — credit-based, all endpoints, no subscription
   - **Free** (legacy) — write-only, 1,500 tweets/mo
   - **Basic** (legacy) — $200/mo, read + search + 50K tweets/mo
   - **Pro** (legacy) — $5,000/mo, full access + 300K tweets/mo

### 2. Generate Credentials

You need credentials from **two different sections** of the X Developer Console:

**From "Keys and tokens" tab:**

| Console Section | Console Label | What It Is |
|----------------|---------------|------------|
| Consumer Keys | Consumer Key | OAuth 1.0a consumer key |
| Consumer Keys | Consumer Key Secret | OAuth 1.0a consumer secret |
| Authentication Tokens | Access Token | OAuth 1.0a user access token |
| Authentication Tokens | Access Token Secret | OAuth 1.0a user access token secret |
| Authentication Tokens | Bearer Token | App-only bearer token (optional) |

**From "Settings" tab > "User authentication settings":**

| Console Section | Console Label | What It Is |
|----------------|---------------|------------|
| User auth settings | Client ID | OAuth 2.0 client identifier |
| User auth settings | Client Secret | OAuth 2.0 client secret |

### 3. Configure OAuth 2.0 Settings

In your App > Settings > User authentication settings:
- **App permissions**: Read and write
- **Type of App**: Web App
- **Callback URI / Redirect URL**: `http://localhost:3000/callback`
- **Website URL**: Any valid URL (e.g. `https://example.com`)

### 4. Plugin Configuration

See [QUICKSTART.md](QUICKSTART.md) for step-by-step configuration in the WebUI.

## Credential Mapping Reference

| X Console Location | Console Label | Plugin Config Field |
|---|---|---|
| Keys and tokens > Consumer Keys | Consumer Key | Auth > OAuth 1.0a > Consumer Key |
| Keys and tokens > Consumer Keys | Consumer Key Secret | Auth > OAuth 1.0a > Consumer Key Secret |
| Keys and tokens > Authentication Tokens | Access Token | Auth > OAuth 1.0a > Access Token |
| Keys and tokens > Authentication Tokens | Access Token Secret | Auth > OAuth 1.0a > Access Token Secret |
| Settings > User auth settings | Client ID | Auth > OAuth 2.0 > Client ID |
| Settings > User auth settings | Client Secret | Auth > OAuth 2.0 > Client Secret |
| Settings > User auth settings | Callback URI | Auth > OAuth 2.0 > Callback URL |
| Keys and tokens > Authentication Tokens | Bearer Token | Auth > Bearer Token |

> **Important:** "Consumer Keys" (Consumer Key) and "OAuth 2.0" (Client ID) are **different credentials** from different sections. Do not mix them up.

## Verifying Installation

1. Open Agent Zero WebUI
2. Go to Settings > External Services
3. Confirm "X.com Integration" appears in the plugin list
4. Click the plugin, go to the Auth tab
5. Enter credentials and click "Test Connection"
6. Expected: green "Connected" badge with your @username

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not visible | Check `.toggle-1` exists: `ls /a0/usr/plugins/x/.toggle-1` |
| Import errors | Run `initialize.py` again to install dependencies |
| 401 Unauthorized | OAuth 2.0 token may have expired; the plugin auto-refreshes but may need re-auth |
| CSRF 403 errors | Normal for unauthenticated requests — use the WebUI |
| "Service disabled" | Check Services tab — the service may be toggled off |
