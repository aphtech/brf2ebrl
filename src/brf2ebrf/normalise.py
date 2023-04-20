def normalise_brf(brf: str, cells_per_line: int, lines_per_page: int) -> str:
    """Normalises a BRF into a standard form for processing.

    This function will ensure every page begins with a form feed character, every line will be padded or truncated to
    the cells per line and pages will be padded or truncated to lines per page.
    """
    return brf if brf.startswith("\f") else "\f" + brf
