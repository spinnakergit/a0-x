# X.com Integration Plugin — Development Guide

## Project Structure

```
a0-x/
├── plugin.yaml              # Plugin manifest
├── default_config.yaml      # Default settings
├── initialize.py            # Dependency installer
├── install.sh               # Deployment script
├── helpers/
│   ├── x_auth.py            # Dual OAuth (PKCE + 1.0a), tier detection, usage tracking
│   ├── x_client.py          # API v2 async client with rate limiting
│   ├── x_media_client.py    # v1.1 chunked media upload
│   └── sanitize.py          # Tweet validation and content sanitization
├── tools/                   # 8 tool implementations
├── prompts/                 # 8 tool prompts + tool_group.md
├── skills/                  # 4 skill workflows
│   ├── x-post/SKILL.md
│   ├── x-thread/SKILL.md
│   ├── x-research/SKILL.md
│   └── x-engage/SKILL.md
├── api/                     # API handlers
├── webui/                   # Dashboard + tabbed config
├── tests/                   # Regression + human test plan
└── docs/                    # Documentation
```

## Development Setup

1. Start the dev container:
   ```bash
   docker start agent-zero-dev
   ```

2. Install the plugin:
   ```bash
   docker cp a0-x/. agent-zero-dev:/a0/usr/plugins/x/
   docker exec agent-zero-dev ln -sf /a0/usr/plugins/x /a0/plugins/x
   docker exec agent-zero-dev supervisorctl restart run_ui
   ```

3. Run tests:
   ```bash
   bash tests/regression_test.sh agent-zero-dev 50083
   ```

## Key Concepts

### Dual OAuth Architecture
- **OAuth 2.0 PKCE**: Used for all API v2 endpoints (posting, reading, managing)
- **OAuth 1.0a**: Used only for media upload (v1.1 endpoint requires it)
- **Bearer Token**: App-only auth for read operations without user context

### Tier System
- `x_auth.py` defines `TIER_CAPABILITIES` and `SERVICE_TIER_REQUIREMENTS`
- Pay-Per-Use (default, recommended) supports all endpoints; legacy Free is write-only
- Tools check tier before executing: `require_tier("pay_per_use", config)`
- Services can be individually toggled in config

### Rate Limiting
- `XRateLimiter` tracks per-endpoint limits from response headers
- Automatic retry on 429 with exponential backoff
- Client-side wait before requests to rate-limited endpoints

### Usage Budgeting
- Monthly tweet counter in `data/usage.json`
- Auto-resets on new month
- `check_write_budget()` called before every write operation

## Adding a New Tool

1. Create `tools/x_<action>.py` with a Tool subclass
2. Create `prompts/agent.system.tool.x_<action>.md`
3. Add service toggle guard: `is_service_enabled("<service>", self.agent)`
4. Add tier check if needed: `require_tier("<tier>", config)`
5. Add tests in `tests/regression_test.sh`
6. Update documentation

## Adding a New Skill

1. Create `skills/x-<name>/SKILL.md` with YAML frontmatter
2. Include: name, description, triggers, allowed_tools, metadata
3. Add tests to verify SKILL.md structure
4. Update documentation

## Code Style

- Use `async/await` for all I/O operations
- Always close client connections in `try/finally`
- Return `Response(message=..., break_loop=False)` from tools
- Validate all user input through `sanitize.py`
- Use `secure_write_json()` for credential files (0o600 permissions)
