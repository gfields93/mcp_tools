import datetime


# Maps Oracle type names to acceptable Python types for incoming values
_TYPE_MAP: dict[str, tuple] = {
    "NUMBER": (int, float),
    "VARCHAR2": (str,),
    "DATE": (datetime.date, datetime.datetime, str),
    "TIMESTAMP": (datetime.datetime, str),
}


def _coerce(name: str, value, oracle_type: str):
    """Coerce and validate a single value against its declared Oracle type."""
    if oracle_type == "NUMBER":
        if isinstance(value, bool):
            raise TypeError(f"Parameter '{name}' expects NUMBER, got bool")
        if isinstance(value, str):
            try:
                return int(value) if "." not in value else float(value)
            except ValueError:
                raise TypeError(f"Parameter '{name}' expects NUMBER, got string {value!r}")
        if not isinstance(value, (int, float)):
            raise TypeError(f"Parameter '{name}' expects NUMBER, got {type(value).__name__}")
        return value

    if oracle_type == "DATE":
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                raise TypeError(
                    f"Parameter '{name}' expects an ISO date string (YYYY-MM-DD), got {value!r}"
                )
        raise TypeError(f"Parameter '{name}' expects DATE, got {type(value).__name__}")

    if oracle_type == "TIMESTAMP":
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.datetime.fromisoformat(value)
            except ValueError:
                raise TypeError(
                    f"Parameter '{name}' expects an ISO datetime string, got {value!r}"
                )
        raise TypeError(f"Parameter '{name}' expects TIMESTAMP, got {type(value).__name__}")

    # VARCHAR2 and any unknown types — accept as string
    if not isinstance(value, str):
        raise TypeError(f"Parameter '{name}' expects VARCHAR2, got {type(value).__name__}")
    return value


def validate_and_bind(param_definitions: list[dict], provided: dict) -> dict:
    """
    Validate and type-coerce caller-provided parameters against the stored
    parameter definitions. Returns a bind dictionary safe to pass to oracledb.

    Raises ValueError for missing required params or disallowed values.
    Raises TypeError for type mismatches.
    """
    bound: dict = {}

    for defn in param_definitions:
        name: str = defn["name"]
        required: bool = defn.get("required", True)
        oracle_type: str = defn.get("type", "VARCHAR2").upper()
        allowed_values: list | None = defn.get("allowed_values")
        default = defn.get("default")

        if name not in provided:
            if required:
                raise ValueError(f"Missing required parameter: '{name}'")
            if default is not None:
                bound[name] = default
            continue

        value = _coerce(name, provided[name], oracle_type)

        if allowed_values is not None and value not in allowed_values:
            raise ValueError(
                f"Parameter '{name}' must be one of {allowed_values}, got {value!r}"
            )

        bound[name] = value

    return bound
