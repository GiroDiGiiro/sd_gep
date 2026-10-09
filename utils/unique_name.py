def unique_name(name: str, existing: list) -> str:
    """Retourne un nom absent de `existing` (insensible à la casse)."""
    lowered = {n.lower() for n in existing}
    if name.lower() not in lowered:
        return name
    i = 1
    while f"{name}_{i}".lower() in lowered:
        i += 1
    return f"{name}_{i}"