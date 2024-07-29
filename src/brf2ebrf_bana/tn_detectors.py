#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Detectors for transcriber notes according to BANA formats"""
import re
from typing import Callable

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


_INLINE_TN_RE = re.compile(f"{_START_TN_SYMBOL}[\u2800-\u28ff\\s]+{_END_TN_SYMBOL}")
_INLINE_EXCLUDES_RE = re.compile(f"(?:\"|{_START_TN_BLOCK})$")


def tag_inline_tn(text: str, check_cancelled: Callable[[], None], start: int=0):
    prev_cursor = start
    new_text = ""
    while m := _INLINE_TN_RE.search(text, pos=start):
        start = m.start()
        new_text += text[prev_cursor:start]
        if not _INLINE_EXCLUDES_RE.search(text, pos=prev_cursor, endpos=start):
            new_text += f"{_START_TN_SPAN}{m.group()}{_END_TN_SPAN}"
        prev_cursor = start
        check_cancelled()
        start = m.end()
    return new_text + text[start:]


_TN_HEADING_START_RE = re.compile(f"<h3>{_START_TN_SYMBOL}")
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
                                _END_TN_SYMBOL):
                            return DetectionResult(list_end, state, 0.95,
                                                   f"{output_text}{text[cursor:position]}{_START_TN_BLOCK}{text[position:list_end]}{_END_TN_BLOCK}")
        end += 1
    return DetectionResult(end, state, 0.5, f"{output_text}{text[cursor:end]}")
