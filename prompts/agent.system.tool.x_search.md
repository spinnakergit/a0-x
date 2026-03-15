## Tool: x_search
Search recent tweets on X.com.

**Arguments:**
- **query** (str, required): Search query (max 512 characters). Supports X search operators.
- **max_results** (str): Number of results (default: 20, max: 100, min: 10)
- **sort_order** (str): "relevancy" (default) or "recency"

**Tier:** Requires Pay-Per-Use or Basic+ tier. Legacy Free tier does NOT support search.

**Examples:**
- Basic search: `query="AI agents"`
- From user: `query="from:elonmusk AI"`
- Hashtag: `query="#crypto lang:en"`
- Recent: `query="breaking news", sort_order="recency"`

**Notes:**
- Legacy Free tier does NOT support search — use Pay-Per-Use or upgrade
- Uses X API v2 recent search (last 7 days)
