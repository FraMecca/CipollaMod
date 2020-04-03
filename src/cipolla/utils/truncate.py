def truncate(string: str, length: int) -> str:
    "Ensure a string is no longer than a given length."
    if len(string) <= length:
        return string
    else:
        return string[:length]
