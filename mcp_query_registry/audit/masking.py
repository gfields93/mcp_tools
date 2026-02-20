MASKED = "***MASKED***"
UPPER_ENVS = {"uat", "prod"}


def mask_parameters(
    params: dict,
    param_definitions: list[dict],
    environment: str,
) -> dict:
    """
    Returns a copy of params safe for audit logging.

    In lower environments (local / dev / sit), params are returned unchanged
    to aid debugging. In upper environments (uat / prod), values for parameters
    flagged as sensitive in the registry definition are replaced with MASKED.
    """
    if environment not in UPPER_ENVS:
        return dict(params)

    sensitive_keys = {
        p["name"] for p in param_definitions if p.get("sensitive", False)
    }
    return {k: MASKED if k in sensitive_keys else v for k, v in params.items()}
