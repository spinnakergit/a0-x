# Human Test Plan: X.com Integration

> **Plugin:** `x`
> **Version:** 1.0.0
> **Type:** Social Media
> **Prerequisite:** `regression_test.sh` passed 100% (94 tests)

---

## How to Use This Plan

1. Work through each phase in order — phases are gated (don't skip ahead)
2. For each test, perform the **Action**, check against **Expected**, mark **Pass/Fail**
3. Use Claude Code as companion: say "Start human verification for x"
4. Record results in `HUMAN_TEST_RESULTS.md`
5. If any test fails: fix, redeploy, re-test that phase

---

## Phase 0: Prerequisites & Environment

Before starting, confirm:

- [ ] Target container is running: `docker ps | grep a0-verify-active`
- [ ] WebUI is accessible: `http://localhost:50088`
- [ ] Plugin is enabled (`.toggle-1` exists)
- [ ] X.com Developer Account created at developer.x.com
- [ ] Automated regression passed: `bash tests/regression_test.sh a0-verify-active 50088`

---

## Phase 1: WebUI Verification

| ID | Test | Action | Expected |
|----|------|--------|----------|
| HV-01 | Plugin visible | Open Settings > Plugins | "X.com Integration" appears in list |
| HV-02 | Toggle works | Toggle plugin off then on | Plugin disables/enables without error |
| HV-03 | Dashboard renders | Click plugin dashboard tab | `main.html` loads, status badge visible, services grid shown |
| HV-04 | Config renders | Click plugin settings tab | `config.html` loads with Auth tab active |
| HV-05 | Tab switching | Click each config tab (Auth, Services, Defaults, Security) | Each panel shows/hides correctly, active tab highlighted |
| HV-06 | No console errors | Open browser DevTools > Console | No JavaScript errors on page load |
| HV-07 | Test connection (no creds) | Click "Test Connection" with no credentials | Shows "No credentials configured" message |
| HV-08 | Save config | Change tier to "Basic", click Save | Success message, value persists on reload |
| HV-09 | Token masking | Enter a test value in Bearer Token, Save, reload | Field shows masked value (•••• pattern) |

---

## Phase 2: Connection & Credentials

### Setup
1. Configure OAuth 1.0a credentials in Auth tab (API Key, Secret, Access Token, Access Token Secret)
2. Configure OAuth 2.0 Client ID
3. Set tier to match your X Developer account tier
4. Click Save

| ID | Test | Action | Expected |
|----|------|--------|----------|
| HV-10 | Valid credentials | Enter correct OAuth credentials, click Test Connection | Shows green "Connected" badge with @username |
| HV-11 | Tier displayed | After successful connection | Correct tier label shown (Free/Basic/Pro) |
| HV-12 | Invalid credentials | Enter bad API key, click Test Connection | Clear error message (not stack trace) |
| HV-13 | Missing credentials | Clear all credentials, click Test Connection | "No credentials configured" message |
| HV-14 | Credential persistence | `supervisorctl restart run_ui`, reload page | Credentials still work after restart |
| HV-15 | Usage stats load | Check dashboard after connection | Usage section shows tweets posted / budget remaining |

---

## Phase 3: Core Tool Testing (Free Tier)

Test each tool via the Agent Zero chat interface.

### Tool: `x_profile`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-16 | Own profile | "Show me my X profile" | Returns @username, name, bio, follower count, join date |
| HV-17 | Lookup user | "Look up @elonmusk on X" | Returns their profile details and stats |
| HV-18 | Invalid username | "Look up @!!invalid!! on X" | Graceful validation error |

### Tool: `x_post`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-19 | Post tweet | "Post a tweet saying: Testing Agent Zero X plugin [timestamp]" | Success with tweet ID, tweet visible on X.com |
| HV-20 | Reply to tweet | "Reply to tweet [ID from HV-19] with: This is a reply test" | Reply posted, appears as thread on X.com |
| HV-21 | Quote tweet | "Quote tweet [ID from HV-19] with: Quoting myself for testing" | Quote tweet posted with embedded original |
| HV-22 | Usage increment | Check dashboard after posting | Tweets posted counter increased |

### Tool: `x_thread`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-23 | Post thread | "Create a 3-tweet thread about AI agents and their capabilities" | All 3 tweets posted as connected thread |
| HV-24 | Thread numbering | Check posted thread on X.com | Tweets show 1/3, 2/3, 3/3 prefix |
| HV-25 | Thread IDs returned | Check agent response | All tweet IDs listed |

### Tool: `x_manage`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-26 | Like tweet | "Like tweet [ID from HV-19]" | Confirmation message, like visible on X.com |
| HV-27 | Retweet | "Retweet tweet [ID from HV-19]" | Confirmation, retweet visible on profile |
| HV-28 | Bookmark | "Bookmark tweet [ID from HV-19]" | Confirmation message |
| HV-29 | Unlike | "Unlike tweet [ID from HV-19]" | Confirmation, like removed |
| HV-30 | Unretweet | "Remove retweet of [ID from HV-19]" | Confirmation, retweet removed |
| HV-31 | Delete tweet | "Delete tweet [ID from HV-23 first tweet]" | Confirmation, tweet no longer visible |

### Tool: `x_media` (requires OAuth 1.0a)

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-32 | Upload image | Provide a test image, "Upload this image to X" | Returns media_id |
| HV-33 | Post with media | "Post a tweet saying 'Test with image' with the uploaded media" | Tweet posted with image visible on X.com |

---

## Phase 4: Tier-Gated Tool Testing (Basic Tier Required)

> Skip this phase if on Free tier. Tests should return clear upgrade messages on Free tier.

### Tool: `x_read`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-34 | Read tweet | "Read tweet [ID from HV-19]" | Returns tweet text, metrics, author |
| HV-35 | User tweets | "Show me @[your_username]'s recent tweets" | Returns list of recent tweets |
| HV-36 | Home timeline | "Show me my X timeline" | Returns home timeline tweets |
| HV-37 | Mentions | "Show me my X mentions" | Returns mention tweets |
| HV-38 | Free tier block | (On Free tier) "Read tweet 1234567890" | Returns upgrade message with tier name and price |

### Tool: `x_search`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-39 | Basic search | "Search X for tweets about AI agents" | Returns relevant tweets with metrics |
| HV-40 | Recency sort | "Search X for 'breaking news' sorted by recency" | Returns recent tweets |
| HV-41 | Free tier block | (On Free tier) "Search X for AI" | Returns upgrade message |

### Tool: `x_analytics`

| ID | Test | Agent Prompt | Expected |
|----|------|-------------|----------|
| HV-42 | Tweet analytics | "Show analytics for tweet [ID from HV-19]" | Returns impressions, likes, retweets, replies |
| HV-43 | Account analytics | "Show my X account analytics" | Returns followers, following, tweet count, monthly usage |
| HV-44 | Free tier block | (On Free tier) "Show my X analytics" | Returns upgrade message |

---

## Phase 5: Security Verification

| ID | Test | Action | Expected |
|----|------|--------|----------|
| HV-45 | CSRF required | `curl -X POST http://localhost:50088/api/plugins/x/x_config_api -d '{}'` | 403 Forbidden |
| HV-46 | Token not leaked | GET config API response | All credentials show masked (••••) |
| HV-47 | Tweet ID injection | Ask agent to "like tweet 123; DROP TABLE" | Validation error, no crash |
| HV-48 | Path traversal | Ask agent to "upload file ../../etc/passwd" | Path restriction error |
| HV-49 | Zero-width injection | Post tweet with zero-width characters embedded | Characters stripped, clean tweet posted |

---

## Phase 6: Edge Cases & Error Handling

| ID | Test | Action | Expected |
|----|------|--------|----------|
| HV-50 | Tweet too long | Ask agent to post 300+ character tweet | Clear error with character count |
| HV-51 | Thread too long | Ask agent to create thread with 1 tweet | Error: "requires at least 2 tweets" |
| HV-52 | Invalid tweet ID | Reply to tweet ID "abc123" | Validation error message |
| HV-53 | Missing text | Ask agent to "post a tweet" with no content | Error: "text is required" |
| HV-54 | Service toggle off | Disable "posting" in Services tab, try to post | "Service disabled" message |
| HV-55 | Service toggle on | Re-enable posting, try again | Post succeeds |
| HV-56 | Post-restart | `supervisorctl restart run_ui`, then use plugin | Plugin works normally |
| HV-57 | Special characters | Post tweet with emoji, unicode, newlines | Delivered intact |

---

## Phase 7: Documentation Spot-Check

| ID | Test | Action | Expected |
|----|------|--------|----------|
| HV-58 | README accuracy | Read README.md, compare to actual features | All 8 tools and 4 skills listed and accurate |
| HV-59 | Tool count | Count tools in `tools/` vs README | 8 tools match |
| HV-60 | Quickstart works | Follow QUICKSTART.md credential setup steps | Steps are accurate and complete |
| HV-61 | Example prompts | Try 2-3 example prompts from tool prompts | They work as described |

---

## Phase 8: Sign-Off

```
Plugin:           X.com Integration
Version:          1.0.0
Container:        a0-verify-active (:50088)
Date:
Tester:
Regression Tests: 94/94  PASS
Human Tests:      ___/61  PASS
Overall:          [ ] APPROVED  [ ] NEEDS WORK  [ ] BLOCKED
Notes:
```
