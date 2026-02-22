"""MCP prompt for exploring related data across deals, facilities, and outstandings."""


def data_exploration(
    deal_name: str | None = None,
    cusip: str | None = None,
) -> str:
    """Guide exploration of related data across deals, facilities, and outstandings.

    Produces a step-by-step plan for understanding a deal's full structure:
    the deal itself, its facilities, outstanding positions, and cross-entity
    summaries.

    Args:
        deal_name: Optional deal name (or partial name) to search for.
                   The prompt will use deal_search_by_name to locate the
                   deal and resolve its ID before proceeding.
        cusip: Optional CUSIP number to look up the deal or facility.
               Takes precedence over deal_name when both are provided.
               The prompt will use deal_get_by_cusip to resolve the deal ID.
    """
    if cusip:
        step1 = (
            f'The user has CUSIP: `{cusip}`. Call `run_query` with '
            f'name="deal_get_by_cusip", parameters={{"cusip_num": "{cusip}"}} '
            "to identify the deal. Extract the deal ID from the result — "
            "you will need it for all subsequent steps. If the CUSIP belongs "
            'to a facility rather than a deal, try `facility_get_by_cusip` '
            "and extract the deal ID from the facility record.\n\n"
        )
    elif deal_name:
        step1 = (
            f'The user is looking for deal: `{deal_name}`. Call `run_query` '
            f'with name="deal_search_by_name", parameters={{"name_search": '
            f'"{deal_name}"}} to find matching deals. If multiple results are '
            "returned, present them to the user and ask which one to explore. "
            "Extract the deal ID from the chosen row — you will need it for "
            "all subsequent steps.\n\n"
        )
    else:
        step1 = (
            "Ask the user how they want to identify the deal:\n"
            "- **By name**: Call `deal_search_by_name` with a partial or full "
            "deal name.\n"
            "- **By CUSIP**: Call `deal_get_by_cusip` (or "
            "`facility_get_by_cusip` if it is a facility CUSIP) to find the "
            "deal.\n"
            "- **Browse active deals**: Call `deal_list_active` to see all "
            "active deals.\n\n"
            "Once you have the deal ID, proceed to Step 2.\n\n"
        )

    return (
        "You are guiding a user through exploring related lending data across "
        "deals, facilities, and outstanding positions in the Oracle MCP Query "
        "Registry. The registry contains queries spanning three core views: "
        "VLS_DEAL, VLS_FACILITY, and VLS_OUTSTANDING.\n\n"
        "## Step 1 — Identify the deal\n"
        + step1
        + "## Step 2 — Retrieve deal details\n"
        'Call `run_query` with name="deal_get_by_id", parameters={"deal_id": '
        '"<resolved deal ID>"} to retrieve the full deal record. Present key '
        "fields: name, status, currency, amounts, and dates.\n\n"
        "## Step 3 — Retrieve facilities\n"
        'Call `run_query` with name="facility_list_by_deal", '
        'parameters={"deal_id": "<resolved deal ID>"} to see all facilities '
        "under this deal. Present facility names, types, currencies, and "
        "amounts.\n\n"
        "## Step 4 — Retrieve outstanding positions\n"
        'Call `run_query` with name="outstanding_list_by_deal", '
        'parameters={"deal_id": "<resolved deal ID>"} to see all outstanding '
        "positions. Highlight current amounts, accrual rates, and performance "
        "status.\n\n"
        "## Step 5 — Cross-entity summary\n"
        'Call `run_query` with name="deal_facility_outstanding_summary", '
        'parameters={"deal_id": "<resolved deal ID>"} to get a rollup of '
        "outstanding counts and amounts per facility.\n\n"
        "## Step 6 — Additional exploration\n"
        "Based on the data, suggest related queries the user might find "
        "useful:\n"
        "- `outstanding_summary_by_currency` — portfolio-wide currency "
        "breakdown\n"
        "- `facility_list_maturing` — facilities approaching maturity\n\n"
        "## Guidelines\n"
        "- Present results in readable tables.\n"
        "- After each step, summarize key findings before moving to the "
        "next.\n"
        "- Highlight any data anomalies (e.g. zero amounts, missing dates, "
        "non-performing status).\n"
        "- If a query returns no rows, explain what that means in context "
        "(e.g. no outstanding positions may indicate the deal is fully "
        "repaid)."
    )
