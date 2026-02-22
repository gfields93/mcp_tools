"""MCP prompt for discovering queries in the registry."""


def query_discovery(tags: str | None = None) -> str:
    """Walk through discovering available queries in the registry.

    Guides the AI through listing queries, filtering by tags, understanding
    parameter definitions and return values, and choosing the right query
    before execution.

    Args:
        tags: Optional comma-separated tags to focus discovery on
              (e.g. "deal,facility"). When omitted, discovery covers
              all available queries.
    """
    tag_instruction = ""
    if tags:
        tag_instruction = (
            f'\n\nThe user is interested in queries tagged with: "{tags}". '
            f"Start by filtering with these tags."
        )

    return (
        "You are helping a user discover and understand queries available in the "
        "Oracle MCP Query Registry. Follow these steps:\n\n"
        "## Step 1 — List available queries\n"
        "Call the `list_queries` tool"
        + (f' with tags="{tags}"' if tags else "")
        + " to see what is available. "
        "Present the results as a concise table with columns: "
        "Name, Description, Tags.\n\n"
        "## Step 2 — Narrow by tags (if needed)\n"
        "If the full list is large, ask the user which domain they are "
        "interested in (e.g. deal, facility, outstanding, reporting) and "
        "re-call `list_queries` with a tag filter.\n\n"
        "## Step 3 — Inspect a specific query\n"
        "Once the user identifies a query of interest, call `get_query` "
        "with its name. Present:\n"
        "- **Description**: what it does\n"
        "- **Parameters**: name, type, required/optional, allowed values, "
        "defaults\n"
        "- **Return values**: each column name, type, and description\n"
        "- **Tags**: for cross-referencing related queries\n\n"
        "## Step 4 — Suggest execution\n"
        "After reviewing the query details, help the user build the correct "
        "`parameters` dict and suggest calling `run_query`. Confirm parameter "
        "values with the user before executing.\n\n"
        "## Guidelines\n"
        "- Never guess parameter values — always ask the user.\n"
        "- Explain what each parameter means using its description from the "
        "registry.\n"
        "- If a parameter has `allowed_values`, list them for the user.\n"
        "- If a parameter is optional, explain what happens when it is omitted."
        + tag_instruction
    )
