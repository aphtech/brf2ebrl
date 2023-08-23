import re

from brf2ebrf.parser import DetectionState, DetectionResult, Detector

_PRINT_PAGE_RE = re.compile("<\\?print-page (?P<page_number>[\u2800-\u28ff]*)\\?>")


def create_ebrf_print_page_tags() -> Detector:
    """Create detector to convert print page numbers to ebrf tags."""
    def convert_to_ebrf_print_page_numbers(text: str, cursor: int, state: DetectionState,
                                           output_text: str) -> DetectionResult | None:
        if m := _PRINT_PAGE_RE.search(text, cursor):
            if m.start() > cursor:
                return DetectionResult(m.start(), state, 0.9, f"{output_text}{text[cursor:m.start()]}")
            page_number = m.group("page_number")
            return DetectionResult(m.end(), state, 0.9,
                                   f"{output_text}<span role=\"doc-pagebreak\" id=\"page{page_number}\">{page_number}</span>")
        return DetectionResult(len(text), state, 0.5, f"{output_text}{text[cursor:]}")
    return convert_to_ebrf_print_page_numbers