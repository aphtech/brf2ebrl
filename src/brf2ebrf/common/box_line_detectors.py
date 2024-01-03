#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detectors for Box lines"""
import re
from collections.abc import Iterable
import logging

from brf2ebrf.parser import DetectionState, DetectionResult, Detector

# Define the regular expression patterns
_ENCLOSING_RE = re.compile(r"(?:([\u2801-\u28ff]+?)\u2800)*?(\u283f{10,})(.+?)(\u283f{10,})",re.DOTALL)
_BOX_RE = re.compile(r"(?:([\u2801-\u28ff]+?)\u2800)*?(\u2836{10,})(.+?)(\u281b{10,})",re.DOTALL)
_BOX_LINES_PROCESSING_INSTRUCTION_RE = re.compile(R"<\?box ([\u2800-\u28ff]+)\?>")

def _convert_groups(match):
    if match.group(1):
        return f'<div screen_type="<?box {match.group(1)}?>" type="<?box {match.group(2)[0]}?>">{match.group(3)}</div>'
    return  f'<div type="<?box {match.group(2)[0]}?>">{match.group(3)}</div>'


def convert_box_lines(
        text: str, cursor: int, state: DetectionState, output_text: str
) -> DetectionResult | None:
    """
    converts all box and screen material to their div equivlant or returns None if not a box line

    Arguments:
    - text of the file

    Returns:
    - The changed file worth of text in a detection result
    
    """
    return DetectionResult(len(text), state, 1.0, output_text + _ENCLOSING_RE.sub(_convert_groups,_BOX_RE.sub(_convert_groups,text)))


def remove_box_lines_processing_instructions(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    """Remove box processing instructions. This was to stop the pre problem."""
    
    return DetectionResult(len(text), state, 1.0, output_text + _BOX_LINES_PROCESSING_INSTRUCTION_RE.sub(lambda m: m.group(1),text))

