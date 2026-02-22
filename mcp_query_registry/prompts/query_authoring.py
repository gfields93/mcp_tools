"""MCP prompt for drafting new SQL queries for the registry."""


def query_authoring(
    table_name: str | None = None,
    query_description: str | None = None,
) -> str:
    """Help draft a new SQL query for the registry, enforcing project conventions.

    Produces a checklist and template covering: no SELECT *, explicit
    return_values, proper parameter JSON definitions, template syntax
    for optional parameters, and the INSERT statement to register
    the query.

    Args:
        table_name: Optional target table or view name to include in
                    the template (e.g. "VLS_DEAL").
        query_description: Optional plain-English description of what
                           the query should do, used to seed the draft.
    """
    context_section = ""
    if table_name or query_description:
        context_section = "\n## Context\n"
        if table_name:
            context_section += f"- Target table/view: `{table_name}`\n"
        if query_description:
            context_section += f"- Intended purpose: {query_description}\n"
        context_section += "\n"

    return (
        "You are helping a user draft a new SQL query to be inserted into the "
        "Oracle MCP Query Registry. Follow the project conventions strictly.\n"
        + context_section
        + "\n## Mandatory Rules\n"
        "1. **No SELECT *** — every column must be listed explicitly in the "
        "SELECT clause.\n"
        "2. **return_values required** — every column in the SELECT list must "
        "have a corresponding entry in the `return_values` JSON array with "
        "`name`, `type`, and `description` keys.\n"
        "3. **Parameter definitions** — every bind variable (`:param_name`) "
        "in the SQL must have a corresponding entry in the `parameters` JSON "
        "array with:\n"
        "   - `name` (str) — matches the bind variable name\n"
        "   - `type` (str) — one of: NUMBER, VARCHAR2, DATE, TIMESTAMP\n"
        "   - `required` (bool) — true if mandatory, false if optional\n"
        "   - `description` (str) — plain-English explanation\n"
        "   - `allowed_values` (list, optional) — restrict to specific "
        "values\n"
        "   - `default` (optional) — default value when omitted\n"
        "   - `sensitive` (bool, optional) — true if value should be masked "
        "in audit logs\n"
        "4. **Optional parameter template syntax** — for optional WHERE "
        "clauses, wrap the clause in `/*[ ... ]*/` delimiters. The block is "
        "included only when all bind variables it references have non-None "
        "values. Example:\n"
        "   ```sql\n"
        "   SELECT id, name\n"
        "   FROM employees/*[ WHERE department = :department]*/\n"
        "   ORDER BY id\n"
        "   ```\n"
        "5. **Tags** — provide comma-separated tags for discoverability "
        "(e.g. 'deal,facility,reporting').\n\n"
        "## Template: INSERT Statement\n"
        "```sql\n"
        "INSERT INTO query_registry\n"
        "    (name, description, sql_text, parameters, return_values, tags)\n"
        "VALUES (\n"
        "    '<query_slug>',\n"
        "    '<Human-readable description>',\n"
        "    q'[SELECT <col1>, <col2>, ...\n"
        "FROM <table>\n"
        "WHERE <conditions>]',\n"
        "    '[{\"name\":\"<param>\",\"type\":\"<TYPE>\","
        "\"required\":true,\"description\":\"...\"}]',\n"
        "    '[{\"name\":\"<col1>\",\"type\":\"<TYPE>\","
        "\"description\":\"...\"},"
        "{\"name\":\"<col2>\",\"type\":\"<TYPE>\","
        "\"description\":\"...\"}]',\n"
        "    '<tag1>,<tag2>'\n"
        ");\n"
        "```\n\n"
        "## Process\n"
        "1. Ask the user what data they need and from which table(s).\n"
        "2. Help them identify the columns to SELECT (look at existing "
        "queries for the same table using `list_queries` with relevant "
        "tags).\n"
        "3. Draft the SQL, parameters JSON, and return_values JSON.\n"
        "4. Validate against all rules above.\n"
        "5. Present the complete INSERT statement ready for execution.\n\n"
        "## Guidelines\n"
        "- Use Oracle SQL syntax (not ANSI). Use `q'[...]'` quoting for "
        "sql_text.\n"
        "- Follow naming conventions from existing queries (snake_case "
        "slugs, entity-prefixed names like `deal_list_active`, "
        "`facility_get_by_cusip`).\n"
        "- For JOINs, use table aliases matching existing patterns "
        "(e.g. `d` for VLS_DEAL, `f` for VLS_FACILITY, `o` for "
        "VLS_OUTSTANDING).\n"
        "- Column names in the SELECT should match the view's actual "
        "column names (e.g. DEA_PID_DEAL, FAC_NME_FACILITY)."
    )
