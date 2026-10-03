def normalize_name(value: str | None) -> str:
    """
    Canonicalize curriculum entity names by trimming whitespace and collapsing multiple spaces.
    """
    if not value:
        return ""
    return " ".join(value.split())
