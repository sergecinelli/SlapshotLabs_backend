def entry_already_exists(entry_name: str) -> tuple[int, dict[str, str]]:
    return 400, {"message": f"{entry_name} already exists or data is incorrect."}