import re

from brf2ebrf.parser import DetectionState, DetectionResult, Detector

_PRINT_PAGE_RE = re.compile("<\\?print-page (?P<page_number>[\u2800-\u28ff]*)\\?>")
_FIND_FOLLOWING_BLOCK_RE = re.compile("((<\\?blank-line\\?>)|\n)*<((h[1-6])|p|(pre)|(table)|(ul)|(div))(\\s|>)")
_NON_NESTED_BLOCKS_RE = re.compile("((<\\?blank-line\\?>)|\n)*<(?P<tag_name>(h[1-6])|p|(pre))(.|\n)*?</(?P=tag_name)>")
_TAG_NAME_PATTERN = "[_a-zA-Z][-_.a-zA-Z0-9]*"
_ELEMENT_TAG_RE = re.compile(f"(<(?P<start_tag_name>{_TAG_NAME_PATTERN})\\s*(/>)?)|(</(?P<end_tag_name>{_TAG_NAME_PATTERN})>)")


def _find_end_of_element(text: str, start: int = 0) -> int:
    cursor = start
    tags = []
    while m := _ELEMENT_TAG_RE.search(text, cursor):
        cursor = m.end()
        if m.group().endswith("/>"):
            continue
        else:
            if m.group().startswith("</"):
                if len(tags) == 0 or tags.pop() != m.group("end_tag_name"):
                    cursor = -1
                    tags.clear()
            else:
                tags.append(m.group("start_tag_name"))
        if len(tags) == 0:
            break
    return cursor if len(tags) == 0 else -1


def create_ebrf_print_page_tags() -> Detector:
    """Create detector to convert print page numbers to ebrf tags."""
    def convert_to_ebrf_print_page_numbers(text: str, cursor: int, state: DetectionState,
                                           output_text: str) -> DetectionResult | None:
        if m := _PRINT_PAGE_RE.search(text, cursor):
            if m.start() > cursor:
                return DetectionResult(m.start(), state, 0.9, f"{output_text}{text[cursor:m.start()]}")
            page_number = m.group("page_number")
            tag_start = m.end()
            if _FIND_FOLLOWING_BLOCK_RE.match(text, tag_start):
                end_index = _find_end_of_element(text, tag_start)
                if end_index > tag_start:
                    return DetectionResult(end_index, state, 0.9, f"{output_text}<div class=\"keeptgr\"><span role=\"doc-pagebreak\" id=\"page{page_number}\" class=\"keepwithnext\">{page_number}</span>{text[tag_start:end_index]}</div>")
            return DetectionResult(tag_start, state, 0.9,
                                   f"{output_text}<span role=\"doc-pagebreak\" id=\"page{page_number}\">{page_number}</span>")
        return DetectionResult(len(text), state, 0.5, f"{output_text}{text[cursor:]}")
    return convert_to_ebrf_print_page_numbers