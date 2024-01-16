#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Detectors for transcriber notes according to BANA formats"""
import re

from brf2ebrf.parser import DetectionState, DetectionResult
from brf2ebrf.utils import find_end_of_element


def tn_indicators_block_matcher(brl: str, state: DetectionState) -> (str | None, DetectionState):
    if brl.startswith("\u2808\u2828\u2823") and brl.endswith("\u2808\u2828\u281c"):
        return f"<div class=\"tn\">{brl}</div>", state
    return None, state


_TN_HEADING_START_RE = re.compile("<h3>\u2808\u2828\u2823")
_TN_HEADING_LIST_SEP_RE = re.compile("((<?blank-line?>)|\\s)*")
_TN_LIST_START_RE = re.compile("<ul")
_TN_LIST_END_RE = re.compile("\u2808\u2828\u281c(</[-a-zA-Z0-9])>$")


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
                        if list_end >= 0 and _TN_LIST_END_RE.search(text, position, list_end):
                            return DetectionResult(position, state, 0.95,
                                                   f"{output_text}<div class=\"tn\">{text[cursor:list_end]}</div>")
    return DetectionResult(end, state, 0.5, f"{output_text}{text[cursor:end]}")
