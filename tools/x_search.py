from helpers.tool import Tool, Response


class XSearch(Tool):
    """Search recent tweets on X.com. Requires Pay-Per-Use or Basic+ tier."""

    async def execute(self, **kwargs) -> Response:
        from plugins.x.helpers.x_auth import is_service_enabled
        if not is_service_enabled("search", self.agent):
            return Response(
                message="Search service is disabled or requires a paid API tier. "
                "The legacy Free tier does not support search. "
                "Switch to Pay-Per-Use (credit-based) or upgrade at developer.x.com.",
                break_loop=False,
            )

        query = self.args.get("query", "")
        max_results = int(self.args.get("max_results", "20"))
        sort_order = self.args.get("sort_order", "relevancy")

        if not query:
            return Response(message="Error: 'query' is required.", break_loop=False)

        if len(query) > 512:
            return Response(message="Error: Query too long (max 512 characters).", break_loop=False)

        if sort_order not in ("relevancy", "recency"):
            return Response(
                message="Error: 'sort_order' must be 'relevancy' or 'recency'.",
                break_loop=False,
            )

        from plugins.x.helpers.x_auth import get_x_config, require_tier
        config = get_x_config(self.agent)

        ok, msg = require_tier("pay_per_use", config)
        if not ok:
            return Response(message=msg, break_loop=False)

        from plugins.x.helpers.x_client import XClient
        client = XClient(config)

        try:
            self.set_progress(f"Searching: {query[:50]}...")
            result = await client.search_recent(
                query=query,
                max_results=max_results,
                sort_order=sort_order,
            )

            if result.get("error"):
                return Response(
                    message=f"Error: {result.get('detail', 'Unknown error')}",
                    break_loop=False,
                )

            data = result.get("data", [])
            meta = result.get("meta", {})
            count = meta.get("result_count", len(data) if data else 0)

            if not data:
                return Response(message=f"No tweets found for: {query}", break_loop=False)

            from plugins.x.helpers.sanitize import format_tweets
            return Response(
                message=f"Found {count} tweet(s) for \"{query}\":\n\n{format_tweets(data)}",
                break_loop=False,
            )
        finally:
            await client.close()
