# X.com Integration Plugin — Quick Start

## Prerequisites

- Agent Zero instance (Docker or local)
- X.com Developer Account at [developer.x.com](https://developer.x.com)
- API credentials (see below)

## Getting API Credentials

### 1. Create a Developer App
1. Go to [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Create a new Project and App
3. Note your pricing tier — Pay-Per-Use (recommended, credit-based) or a legacy subscription (Free/Basic/Pro)

### 2. Get OAuth 1.0a Credentials (for media upload)
1. In your App, go to **"Keys and tokens"** tab
2. Under **"Consumer Keys"** — generate or reveal **API Key** and **API Key Secret**
3. Under **"Authentication Tokens"** — generate **Access Token** and **Access Token Secret**
4. These 4 values enable media upload (which requires OAuth 1.0a)

### 3. Get OAuth 2.0 Credentials (for API v2 posting, reading, managing)
1. In your App, go to **"Settings"** tab
2. Scroll to **"User authentication settings"** and click **Set up** (or Edit)
3. Under **App permissions**, select **Read and write**
4. Under **Type of App**, select **Web App** (enables confidential client with Client Secret)
5. Set **Callback URI / Redirect URL** to `http://localhost:3000/callback`
6. Set **Website URL** to any valid URL (e.g. `https://example.com`)
7. Click **Save**
8. Copy the **Client ID** and **Client Secret** shown on the confirmation page

### 4. Get Bearer Token (optional — app-only read access)
1. In your App, go to **"Keys and tokens"** tab
2. Under **"Authentication Tokens"** — generate **Bearer Token**
3. This is only needed if you want read-only access without user context

### Credential Mapping: X Console to Plugin Fields

Use this table to know exactly which value from the X Developer Console goes into which plugin field.

| X Developer Console Location | Console Label | Plugin Config Field |
|-----|------|------|
| Keys and tokens > **Consumer Keys** | API Key | Auth tab > OAuth 1.0a > **API Key** |
| Keys and tokens > **Consumer Keys** | API Key Secret | Auth tab > OAuth 1.0a > **API Secret** |
| Keys and tokens > **Authentication Tokens** | Access Token | Auth tab > OAuth 1.0a > **Access Token** |
| Keys and tokens > **Authentication Tokens** | Access Token Secret | Auth tab > OAuth 1.0a > **Access Token Secret** |
| Settings > **User authentication settings** | Client ID | Auth tab > OAuth 2.0 > **Client ID** |
| Settings > **User authentication settings** | Client Secret | Auth tab > OAuth 2.0 > **Client Secret** |
| Settings > **User authentication settings** | Callback URI / Redirect URL | Auth tab > OAuth 2.0 > **Callback URL** |
| Keys and tokens > **Authentication Tokens** | Bearer Token | Auth tab > **Bearer Token (App-only)** |

> **Note:** "Consumer Keys" (API Key / API Key Secret) and "OAuth 2.0" (Client ID / Client Secret) are **different credential pairs** from different sections of the console. Do not mix them up — the API Key is NOT the Client ID.

## Installation

```bash
# From inside the Agent Zero container:
./install.sh

# Or manually:
cp -r a0-x/. /a0/usr/plugins/x/
ln -sf /a0/usr/plugins/x /a0/plugins/x
python /a0/usr/plugins/x/initialize.py
touch /a0/usr/plugins/x/.toggle-1
```

## Configuration

1. Open Agent Zero WebUI
2. Go to Settings > External Services > X.com Integration
3. **Authentication tab:**
   - Select your API tier (Pay-Per-Use recommended, or legacy Free / Basic / Pro)
   - Enter OAuth 1.0a credentials using the mapping table above (all 4 fields)
   - Enter OAuth 2.0 Client ID and Client Secret using the mapping table above
   - Verify the Callback URL matches what you set in the X Developer Console
   - Click **"Save Settings"** (you must save before starting the OAuth flow)
   - Click **"Start OAuth 2.0 Flow"** — this opens X.com in a new tab to authorize
   - After authorizing on X.com, your browser redirects to the callback URL (which won't load — that's expected)
   - Copy the **full URL** from your browser's address bar (it contains `?code=...&state=...`)
   - Paste it into the **"Paste redirect URL"** field that appeared, and click **"Complete Authorization"**
4. **Services tab:** Toggle which features to enable
5. Click **"Test Connection"** on the dashboard — should show green "Connected" with your @username

## First Use

Ask the agent:
> "Post a tweet saying: Hello from Agent Zero!"

> "Create a thread about the top 5 AI trends in 2026"

> "Search X for tweets about crypto airdrops" (requires Pay-Per-Use or Basic+ tier)

## API Pricing (as of Feb 2026)

| Tier | Price | Post | Read | Search | Media | Analytics |
|------|-------|------|------|--------|-------|-----------|
| **Pay-Per-Use** | **Credit-based** | **~$0.01/post** | **~$0.005/read** | **Yes** | **Yes** | **Yes** |
| Free (legacy) | $0 | 1,500/mo | No | No | Yes | No |
| Basic (legacy) | $200/mo | 50,000/mo | Yes | Yes (7 days) | Yes | Yes |
| Pro (legacy) | $5,000/mo | 300,000/mo | Yes | Yes (full archive) | Yes | Yes |

> **Recommendation:** Use Pay-Per-Use — no subscription, all endpoints, pay only for what you use.
