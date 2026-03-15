# X.com Integration Plugin Documentation

## Overview

Post, read, search, and manage content on X.com (Twitter) via API v2 with dual OAuth authentication.

## Contents

- [Quick Start](QUICKSTART.md) — Installation and first-use guide
- [Setup](SETUP.md) — Detailed setup, credentials, and troubleshooting
- [Development](DEVELOPMENT.md) — Contributing and development setup

## Architecture

```
a0-x/
├── plugin.yaml              # Plugin manifest
├── default_config.yaml      # Default settings (tier, services, OAuth, security)
├── initialize.py            # Dependency installer (aiohttp, requests-oauthlib, pyyaml)
├── install.sh               # Deployment script
├── .gitignore
├── helpers/
│   ├── x_auth.py            # Dual OAuth module (OAuth 2.0 PKCE + OAuth 1.0a)
│   ├── x_client.py          # API v2 async client with rate limiting
│   ├── x_media_client.py    # v1.1 chunked media upload client
│   └── sanitize.py          # Tweet validation and content sanitization
├── tools/
│   ├── x_post.py            # Post tweets, replies, quote tweets
│   ├── x_thread.py          # Multi-tweet thread posting
│   ├── x_manage.py          # Delete, like, retweet, bookmark
│   ├── x_media.py           # Media upload (images, videos, GIFs)
│   ├── x_read.py            # Read tweets, timelines, mentions
│   ├── x_search.py          # Search recent tweets
│   ├── x_analytics.py       # Tweet and account analytics
│   └── x_profile.py         # User profile lookup
├── prompts/
│   ├── agent.system.tool_group.md
│   ├── agent.system.tool.x_post.md
│   ├── agent.system.tool.x_thread.md
│   ├── agent.system.tool.x_manage.md
│   ├── agent.system.tool.x_media.md
│   ├── agent.system.tool.x_read.md
│   ├── agent.system.tool.x_search.md
│   ├── agent.system.tool.x_analytics.md
│   └── agent.system.tool.x_profile.md
├── skills/
│   ├── x-post/SKILL.md
│   ├── x-thread/SKILL.md
│   ├── x-research/SKILL.md
│   └── x-engage/SKILL.md
├── api/
│   ├── x_config_api.py      # Config CRUD + OAuth flow + test
│   └── x_test.py            # Connection test endpoint
├── webui/
│   ├── main.html            # Dashboard (status, usage, services)
│   └── config.html          # Tabbed settings (Auth, Services, Defaults, Security)
├── tests/
│   ├── regression_test.sh
│   └── HUMAN_TEST_PLAN.md
└── docs/
    ├── README.md
    ├── QUICKSTART.md
    └── DEVELOPMENT.md
```

## Tools (8)

| Tool | Description | Tier | Actions |
|------|-------------|------|---------|
| `x_post` | Post tweets | All | post, reply, quote |
| `x_thread` | Post threads | All | — |
| `x_manage` | Engagement | All | delete, like, unlike, retweet, unretweet, bookmark, unbookmark |
| `x_media` | Media upload | All | upload |
| `x_read` | Read tweets | Pay-Per-Use / Basic+ | tweet, user_tweets, timeline, mentions |
| `x_search` | Search | Pay-Per-Use / Basic+ | — |
| `x_analytics` | Analytics | Pay-Per-Use / Basic+ | tweet, account |
| `x_profile` | Profiles | All | me, lookup |

## Skills (4)

| Skill | Category | Triggers |
|-------|----------|----------|
| `x-post` | Compose & publish | "post to x", "tweet about", "write a tweet" |
| `x-thread` | Thread creation | "create a thread", "tweet thread", "turn this into a thread" |
| `x-research` | Search & analyze | "search x for", "find tweets about", "what are people saying" |
| `x-engage` | Engagement | "engage with tweets", "like tweets", "build x presence" |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plugins/x/x_config_api` | GET/POST | Config CRUD, OAuth flow, connection test |
| `/api/plugins/x/x_test` | GET/POST | Quick connection test |
