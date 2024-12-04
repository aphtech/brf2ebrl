#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Page number detectors"""

import re

from brf2ebrl.parser import DetectionState, DetectionResult, Detector
from brf2ebrl.utils import find_end_of_element

_PRINT_PAGE_RE = re.compile("<\\?print-page (?P<page_number>[\u2800-\u28ff]*)\\?>")
_FIND_FOLLOWING_BLOCK_RE = re.compile("((<\\?blank-line\\?>)|\n)*<((h[1-6])|p|(pre)|(table)|(ul)|(div))(\\s|>)")
_NON_NESTED_BLOCKS_RE = re.compile("((<\\?blank-line\\?>)|\n)*<(?P<tag_name>(h[1-6])|p|(pre))(.|\n)*?</(?P=tag_name)>")


def create_ebrf_print_page_tags() -> Detector:
    """Create detector to convert print page numbers to ebrf tags."""

    def convert_to_ebrf_print_page_numbers(text: str, cursor: int, state: DetectionState,
                                           output_text: str) -> DetectionResult | None:
        new_text = output_text
        if m := _PRINT_PAGE_RE.search(text, cursor):
            if m.start() > cursor:
                new_text += text[cursor:m.start()]
            page_number = m.group("page_number")
            tag_start = m.end()
            if _FIND_FOLLOWING_BLOCK_RE.match(text, tag_start):
                end_index = find_end_of_element(text, tag_start)
                if end_index > tag_start:
                    return DetectionResult(end_index, state, 0.9,
                                           f"{new_text}<div class=\"keeptgr\"><span role=\"doc-pagebreak\" class=\"keepwithnext\">{page_number}</span>{text[tag_start:end_index]}</div>")
            return DetectionResult(tag_start, state, 0.9,
                                   f"{new_text}<span role=\"doc-pagebreak\">{page_number}</span>")
        return DetectionResult(len(text), state, 0.5, f"{new_text}{text[cursor:]}")

    return convert_to_ebrf_print_page_numbers
