"""Detectors for Box lines"""
import re
from collections.abc import Iterable
import logging

from brf2ebrf.parser import DetectionState, DetectionResult, Detector

# Define the regular expression patterns
enclosing_re = re.compile(r"(?:([\u2801-\u28ff]+?)\u2800)*?(\u283f{10,})(.+?)(\u283f{10,})",re.DOTALL)
box_re = re.compile(r"(?:([\u2801-\u28ff]+?)\u2800)*?(\u2836{10,})(.+?)(\u281b{10,})",re.DOTALL)

def convert_groups(match):
    if match.group(1):
        return f'<div screen_type="{match.group(1)}" type="{match.group(2)[0]}">{match.group(3)}</div>'
    return  f'<div type="{match.group(2)[0]}">{match.group(3)}</div>'


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
    return DetectionResult(len(text), state, 1.0, output_text + enclosing_re.sub(convert_groups,box_re.sub(convert_groups,text)))


