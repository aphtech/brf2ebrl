#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Detectors for transcriber notes according to BANA formats"""
import re

from brf2ebrf.parser import DetectionState, DetectionResult
from brf2ebrf.utils import find_end_of_element

_START_TN_BLOCK = "<div class=\"tn\">"
_END_TN_BLOCK = "</div>"
_START_TN_SPAN = "<span class=\"tn\">"
_END_TN_SPAN = "</span>"
_START_TN_SYMBOL = "\u2808\u2828\u2823"
_END_TN_SYMBOL = "\u2808\u2828\u281c"


def tn_indicators_block_matcher(brl: str, state: DetectionState) -> (str | None, DetectionState):
    if brl.startswith(_START_TN_SYMBOL) and brl.endswith(_END_TN_SYMBOL):
        return f"{_START_TN_BLOCK}{brl}{_END_TN_BLOCK}>", state
    return None, state


_INLINE_TN_RE = re.compile(f"((?<!{_START_TN_BLOCK}){_START_TN_SYMBOL}[\u2800-\u28ff\\s]+{_END_TN_SYMBOL})")


def detect_inline_tn(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Detect inline TNs.

    This detector will process the entire text until the end."""
    new_text = _INLINE_TN_RE.subn(f"{_START_TN_SPAN}\\1{_END_TN_SPAN}", text[cursor:])[0]
    return DetectionResult(len(text), state, 1.0, f"{output_text}{new_text}")


_TN_HEADING_START_RE = re.compile("<h3>\u2808\u2828\u2823")
_TN_HEADING_LIST_SEP_RE = re.compile("((<\\?blank-line\\?>)|\\s)*")
_TN_LIST_START_RE = re.compile("<ul")


def detect_symbols_list_tn(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    end = cursor
    while end < len(text):
        position = end
        if m := _TN_HEADING_START_RE.search(text, position):
            if m.start() == position:
                heading_end = find_end_of_element(text, m.start())
                if heading_end >= 0 and (m := _TN_HEADING_LIST_SEP_RE.match(text, heading_end)):
                    list_start = m.end()
                    if _TN_LIST_START_RE.match(text, list_start):
                        list_end = find_end_of_element(text, list_start)
                        if list_end >= 0 and "".join(
                                c for c in text[cursor:list_end] if "\u2800" < c <= "\u28ff").endswith(
                                "\u2808\u2828\u281c"):
                            return DetectionResult(list_end, state, 0.95,
                                                   f"{output_text}{text[cursor:position]}{_START_TN_BLOCK}{text[position:list_end]}{_END_TN_BLOCK}")
        end += 1
    return DetectionResult(end, state, 0.5, f"{output_text}{text[cursor:end]}")
