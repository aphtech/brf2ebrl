"""Detects BANA blocks"""
import re

from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def create_cell_heading(indent: int, tag_name: str) -> Detector:
    """Creates a detector for a heading inented by the specified amount."""
    def detect_cell_heading(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
        lines = []
        new_cursor = cursor
        while line := re.search(f"^\u2800{{{indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+", text[new_cursor:]):
            lines.append(line.group(1))
            new_cursor += line.end()
        brl = "\u2800".join(lines)
        return DetectionResult(new_cursor, state, 0.9,
                               f"{output_text}<{tag_name}>{brl}</{tag_name}>\n") if brl else DetectionResult(cursor + 1, state, 0.0,
                                                                                           output_text + text[cursor])

    return detect_cell_heading

def extract_indented_line(text, indent):
    brl = ""
    if re.search(f"^\u2800{{{indent}}}[\u2801-\u28ff]", text):
        for c in text[indent:]:
            if ord(c) in range(0x2800, 0x2900):
                brl += c
            else:
                break
    return brl
