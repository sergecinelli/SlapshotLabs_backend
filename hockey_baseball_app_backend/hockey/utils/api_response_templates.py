def entry_already_exists(entry_name: str, details: str | None = None) -> tuple[int, dict[str, str]]:
    res = 400, {"message": f"{entry_name} already exists or data is incorrect."}
    if details is not None:
        res[1]['details'] = details
    return res