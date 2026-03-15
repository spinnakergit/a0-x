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
| Consumer Keys | API Key | OAuth 1.0a consumer key |
| Consumer Keys | API Key Secret | OAuth 1.0a consumer secret |
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
| Keys and tokens > Consumer Keys | API Key | Auth > OAuth 1.0a > API Key |
| Keys and tokens > Consumer Keys | API Key Secret | Auth > OAuth 1.0a > API Secret |
| Keys and tokens > Authentication Tokens | Access Token | Auth > OAuth 1.0a > Access Token |
| Keys and tokens > Authentication Tokens | Access Token Secret | Auth > OAuth 1.0a > Access Token Secret |
| Settings > User auth settings | Client ID | Auth > OAuth 2.0 > Client ID |
| Settings > User auth settings | Client Secret | Auth > OAuth 2.0 > Client Secret |
| Settings > User auth settings | Callback URI | Auth > OAuth 2.0 > Callback URL |
| Keys and tokens > Authentication Tokens | Bearer Token | Auth > Bearer Token |

> **Important:** "Consumer Keys" (API Key) and "OAuth 2.0" (Client ID) are **different credentials** from different sections. Do not mix them up.

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
