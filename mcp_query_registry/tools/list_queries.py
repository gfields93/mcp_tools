from db.registry import fetch_all_queries


def list_queries(tags: str | None = None) -> list[dict]:
    """
    Returns all active queries from the registry.

    Each entry includes the query name, description, tags, and full parameter
    definitions. This is the primary discovery tool — call it before deciding
    which query to run.

    Args:
        tags: Optional comma-separated tag filter. When provided, only queries
              matching at least one of the supplied tags are returned.

    Returns:
        List of query summaries with keys: name, description, tags, parameters, return_values.
    """
    return fetch_all_queries(tags=tags)
