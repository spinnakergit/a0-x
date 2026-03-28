---
status: published
repo: https://github.com/spinnakergit/a0-x
published_date: 2026-03-27
version: 1.1.0
---

# Release Status

## Publication
- **GitHub**: https://github.com/spinnakergit/a0-x
- **Published**: 2026-03-27

## v1.1.0 (2026-03-27)

### Changes
- Migrated config.html to Alpine.js framework pattern (outer Save button for settings, custom JS retained for OAuth 2.0 PKCE flow)
- Added hooks.py for plugin lifecycle management
- Added thumbnail.png (256x256 indexed PNG)
- Improved install.sh with in-place detection for plugin manager installs

### Notes
- Auth tab retains custom API-driven JS for OAuth 2.0 PKCE flow (generate auth URL, exchange callback code)
- Services/Defaults/Security tabs use Alpine.js x-model bindings saved by framework outer Save

## v1.0.0 (2026-03-27)

### Verification
- **Automated Tests**: 94/94 PASS
- **Human Verification**: In progress
