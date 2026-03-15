#!/bin/bash
# X.com Plugin Regression Test Suite
# Runs against a live Agent Zero container with the X plugin installed.
#
# Usage:
#   ./regression_test.sh                    # Test against default (a0-verify-active on port 50088)
#   ./regression_test.sh <container> <port> # Test against specific container
#
# Requires: docker, python3 (for JSON parsing)

CONTAINER="${1:-a0-verify-active}"
PORT="${2:-50088}"
BASE_URL="http://localhost:${PORT}"

PASSED=0
FAILED=0
SKIPPED=0
ERRORS=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

pass() {
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}PASS${NC} $1"
}

fail() {
    FAILED=$((FAILED + 1))
    ERRORS="${ERRORS}\n  - $1: $2"
    echo -e "  ${RED}FAIL${NC} $1 — $2"
}

skip() {
    SKIPPED=$((SKIPPED + 1))
    echo -e "  ${YELLOW}SKIP${NC} $1 — $2"
}

section() {
    echo ""
    echo -e "${CYAN}━━━ $1 ━━━${NC}"
}

# Helper: acquire CSRF token + session cookie from the container
CSRF_TOKEN=""
setup_csrf() {
    if [ -z "$CSRF_TOKEN" ]; then
        CSRF_TOKEN=$(docker exec "$CONTAINER" bash -c '
            curl -s -c /tmp/test_cookies.txt \
                -H "Origin: http://localhost" \
                "http://localhost/api/csrf_token" 2>/dev/null
        ' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
    fi
}

# Helper: curl the container's internal API (with CSRF token)
api() {
    local endpoint="$1"
    local data="${2:-}"
    setup_csrf
    if [ -n "$data" ]; then
        docker exec "$CONTAINER" curl -s -X POST "http://localhost/api/plugins/x/${endpoint}" \
            -H "Content-Type: application/json" \
            -H "Origin: http://localhost" \
            -H "X-CSRF-Token: ${CSRF_TOKEN}" \
            -b /tmp/test_cookies.txt \
            -d "$data" 2>/dev/null
    else
        docker exec "$CONTAINER" curl -s "http://localhost/api/plugins/x/${endpoint}" \
            -H "Origin: http://localhost" \
            -H "X-CSRF-Token: ${CSRF_TOKEN}" \
            -b /tmp/test_cookies.txt 2>/dev/null
    fi
}

# Helper: run Python inside the container
pyexec() {
    docker exec "$CONTAINER" /opt/venv-a0/bin/python -c "$1" 2>&1
}

# Helper: check file exists inside container
container_file_exists() {
    docker exec "$CONTAINER" test -f "$1" 2>/dev/null
}

# Helper: check directory exists inside container
container_dir_exists() {
    docker exec "$CONTAINER" test -d "$1" 2>/dev/null
}

echo "========================================"
echo " X.com Plugin Regression Test Suite"
echo "========================================"
echo "Container: $CONTAINER"
echo "Port:      $PORT"
echo "Date:      $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# ━━━ T1: Plugin Infrastructure ━━━
section "T1: Plugin Infrastructure"

# T1.1 — Plugin directory exists
if container_dir_exists "/a0/plugins/x" || container_dir_exists "/a0/usr/plugins/x"; then
    pass "T1.1 Plugin directory exists"
else
    fail "T1.1 Plugin directory exists" "not found"
fi

# T1.2 — plugin.yaml exists and has name field
if container_file_exists "/a0/usr/plugins/x/plugin.yaml"; then
    NAME=$(docker exec "$CONTAINER" grep '^name:' /a0/usr/plugins/x/plugin.yaml 2>/dev/null | head -1)
    if echo "$NAME" | grep -q 'x'; then
        pass "T1.2 plugin.yaml has name: x"
    else
        fail "T1.2 plugin.yaml has name: x" "got: $NAME"
    fi
else
    fail "T1.2 plugin.yaml exists" "not found"
fi

# T1.3 — default_config.yaml exists and has tier field
if container_file_exists "/a0/usr/plugins/x/default_config.yaml"; then
    TIER=$(docker exec "$CONTAINER" grep '^tier:' /a0/usr/plugins/x/default_config.yaml 2>/dev/null)
    if [ -n "$TIER" ]; then
        pass "T1.3 default_config.yaml has tier field"
    else
        fail "T1.3 default_config.yaml has tier field" "tier not found"
    fi
else
    fail "T1.3 default_config.yaml exists" "not found"
fi

# T1.4 — symlink or directory at /a0/plugins/x
if docker exec "$CONTAINER" test -e "/a0/plugins/x" 2>/dev/null; then
    pass "T1.4 Plugin accessible at /a0/plugins/x"
else
    fail "T1.4 Plugin accessible at /a0/plugins/x" "not found"
fi

# T1.5 — .toggle-1 exists (plugin enabled)
if container_file_exists "/a0/usr/plugins/x/.toggle-1"; then
    pass "T1.5 Plugin enabled (.toggle-1 exists)"
else
    skip "T1.5 Plugin enabled" "no .toggle-1 — plugin may not be initialized yet"
fi

# T1.6 — .gitignore exists
if [ -f "$(dirname "$0")/../.gitignore" ]; then
    pass "T1.6 .gitignore exists"
else
    fail "T1.6 .gitignore exists" "not found"
fi

# ━━━ T2: Helper Modules ━━━
section "T2: Helper Modules"

# T2.1 — x_auth.py imports cleanly
RESULT=$(pyexec "import sys; sys.path.insert(0,'/a0/usr/plugins'); from x.helpers.x_auth import get_tier, TIER_CAPABILITIES; print('ok')" 2>&1)
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.1 x_auth.py imports cleanly"
else
    fail "T2.1 x_auth.py imports cleanly" "$RESULT"
fi

# T2.2 — Tier capabilities defined correctly
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.x_auth import TIER_CAPABILITIES
assert 'pay_per_use' in TIER_CAPABILITIES
assert 'free' in TIER_CAPABILITIES
assert 'basic' in TIER_CAPABILITIES
assert 'pro' in TIER_CAPABILITIES
assert TIER_CAPABILITIES['pay_per_use']['write'] == True
assert TIER_CAPABILITIES['pay_per_use']['read'] == True
assert TIER_CAPABILITIES['pay_per_use']['search'] == True
assert TIER_CAPABILITIES['free']['write'] == True
assert TIER_CAPABILITIES['free']['read'] == False
assert TIER_CAPABILITIES['basic']['read'] == True
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.2 Tier capabilities defined correctly"
else
    fail "T2.2 Tier capabilities" "$RESULT"
fi

# T2.3 — sanitize.py imports and validates
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import sanitize_tweet_text, validate_tweet_length, validate_tweet_id, validate_username
t = sanitize_tweet_text('  hello\u200b world  ')
assert t == 'hello world', f'got: {t}'
ok, c = validate_tweet_length('a' * 280)
assert ok and c == 280
ok2, c2 = validate_tweet_length('a' * 281)
assert not ok2 and c2 == 281
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.3 sanitize.py validates correctly"
else
    fail "T2.3 sanitize.py validation" "$RESULT"
fi

# T2.4 — validate_tweet_id rejects bad IDs
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import validate_tweet_id
try:
    validate_tweet_id('abc')
    print('FAIL: should reject')
except ValueError:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.4 validate_tweet_id rejects non-numeric"
else
    fail "T2.4 validate_tweet_id rejection" "$RESULT"
fi

# T2.5 — validate_username strips @ and validates
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import validate_username
u = validate_username('@elonmusk')
assert u == 'elonmusk', f'got: {u}'
try:
    validate_username('invalid username!!')
    print('FAIL')
except ValueError:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.5 validate_username strips @ and validates"
else
    fail "T2.5 validate_username" "$RESULT"
fi

# T2.6 — validate_poll_options enforces 2-4 options
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import validate_poll_options
r = validate_poll_options(['A', 'B'])
assert r == ['A', 'B']
try:
    validate_poll_options(['only one'])
    print('FAIL')
except ValueError:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.6 validate_poll_options enforces 2-4 options"
else
    fail "T2.6 validate_poll_options" "$RESULT"
fi

# T2.7 — x_client.py imports cleanly
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.x_client import XClient, XRateLimiter
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.7 x_client.py imports cleanly"
else
    fail "T2.7 x_client.py import" "$RESULT"
fi

# T2.8 — x_media_client.py imports cleanly
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.x_media_client import XMediaClient
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.8 x_media_client.py imports cleanly"
else
    fail "T2.8 x_media_client.py import" "$RESULT"
fi

# T2.9 — require_tier correctly compares tiers
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.x_auth import require_tier
ok, msg = require_tier('free', {'tier': 'free'})
assert ok and not msg
ok2, msg2 = require_tier('pay_per_use', {'tier': 'free'})
assert not ok2 and 'Free' in msg2
ok3, msg3 = require_tier('pay_per_use', {'tier': 'pay_per_use'})
assert ok3 and not msg3
ok4, msg4 = require_tier('pay_per_use', {'tier': 'basic'})
assert ok4 and not msg4
ok5, msg5 = require_tier('pay_per_use', {'tier': 'pro'})
assert ok5 and not msg5
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.9 require_tier tier comparison"
else
    fail "T2.9 require_tier" "$RESULT"
fi

# T2.10 — PKCE generation produces valid values
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.x_auth import generate_pkce
v, c = generate_pkce()
assert len(v) > 40
assert len(c) > 20
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.10 PKCE generation"
else
    fail "T2.10 PKCE generation" "$RESULT"
fi

# T2.11 — format_tweet produces expected output
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import format_tweet
tweet = {'id': '123', 'author': 'test', 'text': 'hello world', 'created_at': '2026-01-01'}
out = format_tweet(tweet)
assert '@test' in out
assert 'hello world' in out
assert '123' in out
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T2.11 format_tweet output"
else
    fail "T2.11 format_tweet" "$RESULT"
fi

# ━━━ T3: Tool Files ━━━
section "T3: Tool Files"

EXPECTED_TOOLS="x_post x_thread x_manage x_media x_read x_search x_analytics x_profile"
for tool in $EXPECTED_TOOLS; do
    if container_file_exists "/a0/usr/plugins/x/tools/${tool}.py"; then
        pass "T3: ${tool}.py exists"
    else
        fail "T3: ${tool}.py exists" "not found"
    fi
done

# ━━━ T4: Tool Imports ━━━
section "T4: Tool Imports"

# T4.1 — All tools import cleanly
for tool in $EXPECTED_TOOLS; do
    class_name=$(echo "$tool" | python3 -c "import sys; parts=sys.stdin.read().strip().split('_'); print(''.join(p.title() for p in parts))")
    RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0')
sys.path.insert(0,'/a0/usr/plugins')
from x.tools.${tool} import ${class_name}
print('ok')
" 2>&1)
    if echo "$RESULT" | grep -q 'ok'; then
        pass "T4: ${tool}.py imports ${class_name}"
    else
        fail "T4: ${tool}.py import" "$RESULT"
    fi
done

# ━━━ T5: Prompt Files ━━━
section "T5: Prompt Files"

# T5.1 — tool_group.md exists
if container_file_exists "/a0/usr/plugins/x/prompts/agent.system.tool_group.md"; then
    pass "T5.1 tool_group.md exists"
else
    fail "T5.1 tool_group.md exists" "not found"
fi

# T5.2 — Each tool has a prompt file
for tool in $EXPECTED_TOOLS; do
    PROMPT="/a0/usr/plugins/x/prompts/agent.system.tool.${tool}.md"
    if container_file_exists "$PROMPT"; then
        pass "T5.2 prompt for ${tool}"
    else
        fail "T5.2 prompt for ${tool}" "not found: $PROMPT"
    fi
done

# T5.3 — tool_group.md references all tools
RESULT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/prompts/agent.system.tool_group.md 2>/dev/null)
MISSING=""
for tool in $EXPECTED_TOOLS; do
    if ! echo "$RESULT" | grep -q "$tool"; then
        MISSING="$MISSING $tool"
    fi
done
if [ -z "$MISSING" ]; then
    pass "T5.3 tool_group.md references all tools"
else
    fail "T5.3 tool_group.md completeness" "missing:$MISSING"
fi

# ━━━ T6: API Handlers ━━━
section "T6: API Handlers"

# T6.1 — Config API file exists
if container_file_exists "/a0/usr/plugins/x/api/x_config_api.py"; then
    pass "T6.1 x_config_api.py exists"
else
    fail "T6.1 x_config_api.py exists" "not found"
fi

# T6.2 — Test API file exists
if container_file_exists "/a0/usr/plugins/x/api/x_test.py"; then
    pass "T6.2 x_test.py exists"
else
    fail "T6.2 x_test.py exists" "not found"
fi

# T6.3 — Config API imports cleanly
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_config_api import XConfigApi
print('ok')
" 2>&1)
if echo "$RESULT" | grep -q 'ok'; then
    pass "T6.3 XConfigApi imports"
else
    fail "T6.3 XConfigApi import" "$RESULT"
fi

# T6.4 — Test API imports cleanly
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_test import XTest
print('ok')
" 2>&1)
if echo "$RESULT" | grep -q 'ok'; then
    pass "T6.4 XTest imports"
else
    fail "T6.4 XTest import" "$RESULT"
fi

# T6.5 — Config API requires CSRF
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_config_api import XConfigApi
assert XConfigApi.requires_csrf() == True
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T6.5 XConfigApi requires CSRF"
else
    fail "T6.5 CSRF enforcement" "$RESULT"
fi

# T6.6 — Test API requires CSRF
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_test import XTest
assert XTest.requires_csrf() == True
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T6.6 XTest requires CSRF"
else
    fail "T6.6 CSRF enforcement" "$RESULT"
fi

# T6.7 — Config API GET endpoint responds
RESULT=$(api "x_config_api" 2>/dev/null)
if [ -n "$RESULT" ] && echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok')" 2>/dev/null; then
    pass "T6.7 Config API responds to GET"
else
    skip "T6.7 Config API GET" "API not responding (container may need restart)"
fi

# ━━━ T7: WebUI ━━━
section "T7: WebUI"

# T7.1 — main.html exists and has data- attributes
if container_file_exists "/a0/usr/plugins/x/webui/main.html"; then
    CONTENT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/webui/main.html 2>/dev/null)
    if echo "$CONTENT" | grep -q 'data-xm='; then
        pass "T7.1 main.html uses data-xm attributes"
    else
        fail "T7.1 main.html data attributes" "no data-xm= found"
    fi
else
    fail "T7.1 main.html exists" "not found"
fi

# T7.2 — config.html exists and has data- attributes
if container_file_exists "/a0/usr/plugins/x/webui/config.html"; then
    CONTENT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/webui/config.html 2>/dev/null)
    if echo "$CONTENT" | grep -q 'data-xc='; then
        pass "T7.2 config.html uses data-xc attributes"
    else
        fail "T7.2 config.html data attributes" "no data-xc= found"
    fi
else
    fail "T7.2 config.html exists" "not found"
fi

# T7.3 — main.html uses globalThis.fetchApi
CONTENT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/webui/main.html 2>/dev/null)
if echo "$CONTENT" | grep -q 'globalThis.fetchApi'; then
    pass "T7.3 main.html uses globalThis.fetchApi"
else
    fail "T7.3 globalThis.fetchApi in main.html" "not found"
fi

# T7.4 — config.html uses globalThis.fetchApi
CONTENT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/webui/config.html 2>/dev/null)
if echo "$CONTENT" | grep -q 'globalThis.fetchApi'; then
    pass "T7.4 config.html uses globalThis.fetchApi"
else
    fail "T7.4 globalThis.fetchApi in config.html" "not found"
fi

# T7.5 — config.html has tabbed interface
if echo "$CONTENT" | grep -q 'tab-auth'; then
    pass "T7.5 config.html has tabbed interface"
else
    fail "T7.5 config.html tabs" "no tab-auth found"
fi

# T7.6 — config.html has OAuth 1.0a fields
if echo "$CONTENT" | grep -q 'oauth1_api_key'; then
    pass "T7.6 config.html has OAuth 1.0a fields"
else
    fail "T7.6 OAuth 1.0a fields" "not found"
fi

# T7.7 — config.html has OAuth 2.0 fields
if echo "$CONTENT" | grep -q 'oauth2_client_id'; then
    pass "T7.7 config.html has OAuth 2.0 fields"
else
    fail "T7.7 OAuth 2.0 fields" "not found"
fi

# T7.8 — No bare IDs (only data- attributes)
if echo "$CONTENT" | grep -qP '\bid="[^"]*"'; then
    fail "T7.8 No bare IDs in config.html" "found bare id= attributes"
else
    pass "T7.8 No bare IDs in config.html"
fi

MAIN_CONTENT=$(docker exec "$CONTAINER" cat /a0/usr/plugins/x/webui/main.html 2>/dev/null)
if echo "$MAIN_CONTENT" | grep -qP '\bid="[^"]*"'; then
    fail "T7.9 No bare IDs in main.html" "found bare id= attributes"
else
    pass "T7.9 No bare IDs in main.html"
fi

# ━━━ T8: Security ━━━
section "T8: Security"

# T8.1 — Config API masks sensitive values
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_config_api import _mask, _deep_mask
m = _mask('sk_test_1234567890abcdef')
assert '••••' in m
assert 'sk_' in m
d = _deep_mask({'oauth1': {'api_key': 'secret123456'}})
assert '••••' in d['oauth1']['api_key']
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.1 Sensitive values masked"
else
    fail "T8.1 Value masking" "$RESULT"
fi

# T8.2 — deep_merge preserves masked values
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0'); sys.path.insert(0,'/a0/usr/plugins')
from x.api.x_config_api import _deep_merge_preserve_masked
existing = {'oauth1': {'api_key': 'real_secret'}}
new = {'oauth1': {'api_key': 'rea••••ret'}}
merged = _deep_merge_preserve_masked(new, existing)
assert merged['oauth1']['api_key'] == 'real_secret'
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.2 Masked values preserved on save"
else
    fail "T8.2 Masked value preservation" "$RESULT"
fi

# T8.3 — sanitize_tweet_content strips zero-width chars
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import sanitize_tweet_content
text = 'he\u200bllo\u200c wor\u200dld'
result = sanitize_tweet_content(text)
assert result == 'hello world', f'got: {result}'
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.3 Zero-width char stripping"
else
    fail "T8.3 Zero-width stripping" "$RESULT"
fi

# T8.4 — validate_tweet_id rejects injection
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
from x.helpers.sanitize import validate_tweet_id
bad_ids = ['12345; DROP TABLE', '../../../etc/passwd', '<script>alert(1)</script>', '']
for bad in bad_ids:
    try:
        validate_tweet_id(bad)
        if bad:  # empty returns empty, which is ok
            print(f'FAIL: accepted {bad}')
            sys.exit(1)
    except ValueError:
        pass
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.4 Tweet ID injection defense"
else
    fail "T8.4 Tweet ID injection" "$RESULT"
fi

# T8.5 — x_media.py restricts file paths
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
# Check that x_media.py source contains path restriction
with open('/a0/usr/plugins/x/tools/x_media.py') as f:
    content = f.read()
assert 'allowed_prefixes' in content
assert '/a0/' in content
assert '/tmp/' in content
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.5 Media upload path restriction"
else
    fail "T8.5 Media path restriction" "$RESULT"
fi

# T8.6 — secure_write_json uses 0o600 permissions
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
with open('/a0/usr/plugins/x/helpers/x_auth.py') as f:
    content = f.read()
assert '0o600' in content
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T8.6 Token files use 0o600 permissions"
else
    fail "T8.6 File permissions" "$RESULT"
fi

# ━━━ T9: Dependencies ━━━
section "T9: Dependencies"

# T9.1 — aiohttp importable
RESULT=$(pyexec "import aiohttp; print('ok')")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T9.1 aiohttp installed"
else
    skip "T9.1 aiohttp" "not installed — run initialize.py"
fi

# T9.2 — requests_oauthlib importable
RESULT=$(pyexec "from requests_oauthlib import OAuth1; print('ok')")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T9.2 requests-oauthlib installed"
else
    skip "T9.2 requests-oauthlib" "not installed — run initialize.py"
fi

# T9.3 — yaml importable
RESULT=$(pyexec "import yaml; print('ok')")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T9.3 pyyaml installed"
else
    skip "T9.3 pyyaml" "not installed — run initialize.py"
fi

# T9.4 — initialize.py has correct deps list
RESULT=$(pyexec "
import sys; sys.path.insert(0,'/a0/usr/plugins')
with open('/a0/usr/plugins/x/initialize.py') as f:
    content = f.read()
assert 'aiohttp' in content
assert 'requests_oauthlib' in content
assert 'yaml' in content
print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T9.4 initialize.py lists all dependencies"
else
    fail "T9.4 initialize.py deps" "$RESULT"
fi

# ━━━ T10: Configuration ━━━
section "T10: Configuration"

# T10.1 — default_config.yaml has all required sections
RESULT=$(pyexec "
import yaml, sys
with open('/a0/usr/plugins/x/default_config.yaml') as f:
    config = yaml.safe_load(f)
required = ['tier', 'services', 'oauth1', 'oauth2', 'bearer_token', 'defaults', 'usage', 'security']
missing = [k for k in required if k not in config]
if missing:
    print(f'missing: {missing}')
else:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T10.1 default_config.yaml has all sections"
else
    fail "T10.1 config sections" "$RESULT"
fi

# T10.2 — Services section has all expected services
RESULT=$(pyexec "
import yaml
with open('/a0/usr/plugins/x/default_config.yaml') as f:
    config = yaml.safe_load(f)
services = config.get('services', {})
expected = ['posting', 'reading', 'search', 'media', 'analytics']
missing = [s for s in expected if s not in services]
if missing:
    print(f'missing: {missing}')
else:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T10.2 All services defined in config"
else
    fail "T10.2 Services" "$RESULT"
fi

# T10.3 — OAuth 1.0a has all four credential fields
RESULT=$(pyexec "
import yaml
with open('/a0/usr/plugins/x/default_config.yaml') as f:
    config = yaml.safe_load(f)
oauth1 = config.get('oauth1', {})
expected = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
missing = [k for k in expected if k not in oauth1]
if missing:
    print(f'missing: {missing}')
else:
    print('ok')
")
if echo "$RESULT" | grep -q 'ok'; then
    pass "T10.3 OAuth 1.0a credential fields"
else
    fail "T10.3 OAuth 1.0a fields" "$RESULT"
fi

# ━━━ T11: Skills ━━━
section "T11: Skills"

EXPECTED_SKILLS="x-post x-thread x-research x-engage"

# T11.1 — All skill directories exist
for skill in $EXPECTED_SKILLS; do
    if container_dir_exists "/a0/usr/plugins/x/skills/${skill}"; then
        pass "T11.1 skill dir ${skill} exists"
    else
        fail "T11.1 skill dir ${skill}" "not found"
    fi
done

# T11.2 — Every skill has SKILL.md
for skill in $EXPECTED_SKILLS; do
    if container_file_exists "/a0/usr/plugins/x/skills/${skill}/SKILL.md"; then
        pass "T11.2 ${skill}/SKILL.md exists"
    else
        fail "T11.2 ${skill}/SKILL.md" "not found"
    fi
done

# T11.3 — All SKILL.md files have YAML frontmatter
for skill in $EXPECTED_SKILLS; do
    RESULT=$(docker exec "$CONTAINER" head -1 "/a0/usr/plugins/x/skills/${skill}/SKILL.md" 2>/dev/null)
    if echo "$RESULT" | grep -q '^\-\-\-'; then
        pass "T11.3 ${skill} has YAML frontmatter"
    else
        fail "T11.3 ${skill} frontmatter" "no --- found"
    fi
done

# T11.4 — All SKILL.md files have required fields
for skill in $EXPECTED_SKILLS; do
    RESULT=$(docker exec "$CONTAINER" bash -c "
        head -20 /a0/usr/plugins/x/skills/${skill}/SKILL.md | grep -cE '^(name|triggers|allowed_tools):'
    " 2>/dev/null)
    if [ "$RESULT" -ge 3 ] 2>/dev/null; then
        pass "T11.4 ${skill} has name/triggers/allowed_tools"
    else
        fail "T11.4 ${skill} required fields" "found $RESULT of 3"
    fi
done

# T11.5 — All allowed_tools reference existing tool files
RESULT=$(docker exec "$CONTAINER" bash -c '
    cd /a0/usr/plugins/x
    TOOL_NAMES=""
    while read f; do
        TOOL_NAMES="$TOOL_NAMES $(basename "$f" .py)"
    done < <(find tools/ -name "*.py" -not -name "__*")

    FAILED=""
    for skill_dir in skills/*/; do
        skill_file="${skill_dir}SKILL.md"
        [ -f "$skill_file" ] || continue
        in_tools=0
        while IFS= read -r line; do
            if echo "$line" | grep -q "^allowed_tools:"; then
                in_tools=1
                continue
            fi
            if [ $in_tools -eq 1 ]; then
                if echo "$line" | grep -q "^  - "; then
                    tool=$(echo "$line" | sed "s/^  - //")
                    if ! echo "$TOOL_NAMES" | grep -qw "$tool"; then
                        FAILED="$FAILED $tool"
                    fi
                elif ! echo "$line" | grep -q "^  "; then
                    in_tools=0
                fi
            fi
        done < "$skill_file"
    done

    if [ -z "$FAILED" ]; then
        echo "ok"
    else
        echo "invalid:$FAILED"
    fi
' 2>/dev/null)
if echo "$RESULT" | grep -q '^ok'; then
    pass "T11.5 All skill allowed_tools reference valid tools"
else
    fail "T11.5 Skill tool references" "$RESULT"
fi

# ━━━ T12: Documentation ━━━
section "T12: Documentation"

# T12.1 — README.md exists and has features
if [ -f "$(dirname "$0")/../README.md" ]; then
    CONTENT=$(cat "$(dirname "$0")/../README.md")
    if echo "$CONTENT" | grep -q 'x_post'; then
        pass "T12.1 README.md lists tools"
    else
        fail "T12.1 README.md content" "tools not listed"
    fi
else
    fail "T12.1 README.md exists" "not found"
fi

# T12.2 — docs/README.md exists
if [ -f "$(dirname "$0")/../docs/README.md" ]; then
    pass "T12.2 docs/README.md exists"
else
    fail "T12.2 docs/README.md" "not found"
fi

# T12.3 — docs/QUICKSTART.md exists
if [ -f "$(dirname "$0")/../docs/QUICKSTART.md" ]; then
    pass "T12.3 docs/QUICKSTART.md exists"
else
    fail "T12.3 docs/QUICKSTART.md" "not found"
fi

# T12.4 — docs/DEVELOPMENT.md exists
if [ -f "$(dirname "$0")/../docs/DEVELOPMENT.md" ]; then
    pass "T12.4 docs/DEVELOPMENT.md exists"
else
    fail "T12.4 docs/DEVELOPMENT.md" "not found"
fi

# T12.5 — LICENSE exists
if [ -f "$(dirname "$0")/../LICENSE" ]; then
    pass "T12.5 LICENSE exists"
else
    fail "T12.5 LICENSE" "not found"
fi

# ━━━ SUMMARY ━━━
echo ""
echo "========================================"
TOTAL=$((PASSED + FAILED + SKIPPED))
echo -e " Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}, ${YELLOW}${SKIPPED} skipped${NC} (${TOTAL} total)"

if [ $FAILED -gt 0 ]; then
    echo -e "\n${RED}Failures:${NC}${ERRORS}"
    echo "========================================"
    exit 1
else
    echo "========================================"
    exit 0
fi
