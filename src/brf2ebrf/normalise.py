def _pad_line(line, length):
    return line.ljust(length, " ")[:length]


def _normalise_page(page: str, cells_per_line: int, lines_per_page: int) -> str:
    lines = [_pad_line(line, cells_per_line) for line in page.splitlines(False)]
    return "\n".join(lines + [""] * (lines_per_page - len(lines)))


def normalise_brf(brf: str, cells_per_line: int, lines_per_page: int) -> str:
    """Normalises a BRF into a standard form for processing.

    This function will ensure every page begins with a form feed character, every line will be padded or truncated to
    the cells per line and pages will be padded or truncated to lines per page.
    """
    brf_pages = brf.removeprefix("\f").removesuffix("\f").split("\f")
    return "\f" + "\f".join([_normalise_page(page, cells_per_line, lines_per_page) for page in brf_pages])
