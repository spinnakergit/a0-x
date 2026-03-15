# X.com Integration Plugin for Agent Zero

Post, read, search, and manage content on X.com (Twitter) via API v2 with dual OAuth authentication.

## Features

### Tools (8)
| Tool | Description | Tier |
|------|-------------|------|
| `x_post` | Post tweets, replies, quote tweets with media/polls | All |
| `x_thread` | Post multi-tweet threads with auto-numbering | All |
| `x_manage` | Delete, like, unlike, retweet, bookmark | All |
| `x_media` | Upload images, videos, GIFs (chunked upload) | All |
| `x_read` | Read tweets, timelines, mentions | Pay-Per-Use / Basic+ |
| `x_search` | Search recent tweets with operators | Pay-Per-Use / Basic+ |
| `x_analytics` | Tweet metrics and account analytics | Pay-Per-Use / Basic+ |
| `x_profile` | View own profile or look up users | All |

### Skills (4)
| Skill | Triggers | Description |
|-------|----------|-------------|
| `x-post` | "post to x", "tweet about" | Compose and publish tweets |
| `x-thread` | "create a thread", "tweet thread" | Create multi-tweet threads |
| `x-research` | "search x for", "find tweets" | Research topics and users |
| `x-engage` | "engage with tweets", "like tweets" | Build presence through engagement |

### Architecture
- **Dual OAuth**: OAuth 2.0 PKCE (API v2) + OAuth 1.0a (media upload v1.1)
- **Tier-aware**: Pay-Per-Use (recommended), Free/Basic/Pro (legacy)
- **Rate limiting**: Per-endpoint tracking with automatic retry
- **Usage budgeting**: Monthly tweet tracking with configurable daily limits
- **Content sanitization**: Unicode normalization, zero-width char stripping
- **Tabbed WebUI**: Auth, Services, Defaults, Security configuration tabs

## Quick Start

1. Install the plugin:
   ```bash
   ./install.sh
   ```
2. Configure your credentials in WebUI (Settings > External Services > X.com Integration)
3. Restart Agent Zero

## API Pricing (as of Feb 2026)

| Tier | Price | Capabilities |
|------|-------|-------------|
| **Pay-Per-Use** | **Credit-based** | **All endpoints. ~$0.005/read, ~$0.01/post. No subscription.** |
| Free (legacy) | $0 | 1,500 tweets/mo, write-only, no read/search |
| Basic (legacy) | $200/mo | 50,000 tweets/mo + read + search + analytics |
| Pro (legacy) | $5,000/mo | 300,000 tweets/mo + full archive + streaming |

> Pay-Per-Use is the recommended tier. Legacy tiers remain functional for existing subscribers.

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Full Documentation](docs/README.md)

## License

MIT — see [LICENSE](LICENSE)
