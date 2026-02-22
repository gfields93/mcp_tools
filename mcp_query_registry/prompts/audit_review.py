"""MCP prompt for reviewing query execution audit data."""


def audit_review(
    time_range: str = "24h",
    query_name: str | None = None,
) -> str:
    """Review recent query executions for performance trends and error rates.

    Guides the AI through running audit-focused queries from the registry
    to surface slow queries, error spikes, and the most-used queries
    within a given time window.

    Args:
        time_range: Lookback period for the review. Accepts "1h",
                    "24h", "7d", or "30d". Defaults to "24h".
        query_name: Optional query name to focus the review on a
                    single query's execution history.
    """
    time_map = {
        "1h": ("1 hour", 1),
        "24h": ("24 hours", 24),
        "7d": ("7 days", 168),
        "30d": ("30 days", 720),
    }
    label, hours = time_map.get(time_range, ("24 hours", 24))

    focus = ""
    if query_name:
        focus = (
            f"\n\nThe user wants to focus specifically on query: "
            f"`{query_name}`. When reviewing results, filter or highlight "
            f"rows matching this query name."
        )

    return (
        f"You are reviewing query execution audit data for the past {label}. "
        "The Oracle MCP Query Registry logs every query execution to the "
        "`query_audit_log` table. Use the audit-focused queries in the "
        "registry to surface insights.\n\n"
        f"Pass `lookback_hours={hours}` to each audit query to match the "
        "requested time range.\n\n"
        "## Step 1 — Execution summary\n"
        'Call `run_query` with name="audit_execution_summary" to get an '
        f"overview of all executions in the past {label}: total runs, "
        "success/error counts, and average duration.\n\n"
        "## Step 2 — Error analysis\n"
        'Call `run_query` with name="audit_recent_errors" to retrieve '
        "recent failed executions. Present the error messages, which "
        "queries failed, and when.\n\n"
        "## Step 3 — Performance trends\n"
        'Call `run_query` with name="audit_slow_queries" to find queries '
        "with high average or maximum duration. Highlight any that exceed "
        "1000ms.\n\n"
        "## Step 4 — Most-used queries\n"
        'Call `run_query` with name="audit_most_used" to see which queries '
        "are called most frequently. This helps identify high-value queries "
        "worth optimizing.\n\n"
        "## Step 5 — Recommendations\n"
        "Based on the data, provide actionable recommendations:\n"
        "- Queries with high error rates may have parameter issues or stale "
        "SQL.\n"
        "- Slow queries may benefit from index review or SQL optimization.\n"
        "- Unused queries may be candidates for deactivation.\n"
        "- Queries with consistently high row counts may need tighter "
        "max_rows defaults.\n\n"
        "## Guidelines\n"
        "- Present numbers in context (e.g. '12 errors out of 450 "
        "executions = 2.7% error rate').\n"
        "- If audit queries are not yet in the registry, guide the user to "
        "create them using the Query Authoring prompt.\n"
        "- Compare metrics across time ranges when asked for trends."
        + focus
    )
