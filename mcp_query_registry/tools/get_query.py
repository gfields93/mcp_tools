from db.registry import fetch_query


def get_query(name: str) -> dict:
    """
    Returns full detail for a single named query.

    Useful for inspecting one query in depth — including its parameter
    definitions — without fetching the entire registry.

    Args:
        name: The query slug to look up.

    Returns:
        Dict with keys: name, description, parameters, return_values, version, tags.
    """
    record = fetch_query(name)
    return {
        "name": record.name,
        "description": record.description,
        "parameters": record.parameters,
        "return_values": record.return_values,
        "version": record.version,
        "tags": [t.strip() for t in record.tags.split(",")] if record.tags else [],
    }
