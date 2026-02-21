import re

_BLOCK_RE = re.compile(r"/\*\[(.+?)\]\*/", re.DOTALL)
_BIND_RE = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def render_sql(sql: str, bind_dict: dict) -> str:
    """
    Evaluate conditional template blocks in sql against the active bind variables.

    Blocks are delimited by /*[ ... ]*/. A block is included (without its
    delimiters) only when every bind variable it references is present in
    bind_dict with a non-None value. Blocks whose variables are absent or
    None are stripped entirely.

    Non-template SQL is returned unchanged.
    """
    def _resolve(match: re.Match) -> str:
        content = match.group(1)
        vars_needed = set(_BIND_RE.findall(content))
        if vars_needed and all(bind_dict.get(v) is not None for v in vars_needed):
            return content
        return ""

    return _BLOCK_RE.sub(_resolve, sql).strip()
