"""Detectors for blocks"""
import re
from typing import Optional

from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def detect_pre(
        text: str, cursor: int, state: DetectionState, output_text: str
) -> Optional[DetectionResult]:
    """Detects preformatted Braille"""
    brl = ""
    for c in text[cursor:]:
        if ord(c) in range(0x2800, 0x2900):
            brl += c
        else:
            break
    return DetectionResult(cursor + len(brl), state, 0.4, f"{output_text}<pre>{brl}</pre>") if brl else None


def create_cell_heading(indent: int, tag_name: str) -> Detector:
    """Creates a detector for a heading indented by the specified amount."""
    heading_re = re.compile(f"\u2800{{{indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")

    def detect_cell_heading(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> Optional[DetectionResult]:
        lines = []
        new_cursor = cursor
        while line := heading_re.match(
                text[new_cursor:],
        ):
            lines.append(line.group(1))
            new_cursor += line.end()
        brl = "\u2800".join(lines)
        return DetectionResult(
                new_cursor, state, 0.9, f"{output_text}<{tag_name}>{brl}</{tag_name}>\n"
            ) if brl else None

    return detect_cell_heading


def create_centered_detector(
        cells_per_line: int, min_indent: int, tag_name: str
) -> Detector:
    """Creates a detector for detecting centered text."""
    heading_re = re.compile(f"(\u2800{{{min_indent},}})([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+", )

    def detect_centered(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> Optional[DetectionResult]:
        lines = []
        new_cursor = cursor
        while line := heading_re.match(
                text[new_cursor:],
        ):
            line_brl = line.group(2).rstrip("\u2800")
            indent, indent_mod = divmod(cells_per_line - len(line_brl), 2)
            indents = [indent] if indent_mod == 0 else [indent, indent + indent_mod]
            if len(line.group(1)) in indents:
                lines.append(line_brl)
                new_cursor += line.end()
            else:
                break
        brl = "\u2800".join(lines)
        return DetectionResult(
                new_cursor, state, 0.9, f"{output_text}<{tag_name}>{brl}</{tag_name}>\n"
            ) if brl else None

    return detect_centered


def create_paragraph_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding paragraphs with the specified first line indent and run over."""
    first_line_re = re.compile(f"^\u2800{{{first_line_indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")
    run_over_re = re.compile(f"^\u2800{{{run_over}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")

    def detect_paragraph(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> Optional[DetectionResult]:
        lines = []
        new_cursor = cursor
        if line := first_line_re.match(
                text[new_cursor:]
        ):
            lines.append(line.group(1))
            new_cursor += line.end()+1 #+ 1 for the end line
            while line := run_over_re.match(
                    text[new_cursor:]
            ):
                lines.append(line.group(1))
                new_cursor += line.end()+1 # + 1 for the new line
        brl = "\u2800".join(lines)
        return DetectionResult(new_cursor, state, 0.9, f"{output_text}<p>{brl}</p>\n") if brl else None

    return detect_paragraph


def create_list_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding lists with the specified first line indent and run over."""
    first_line_re = re.compile(f"^\u2800{{{first_line_indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")
    run_over_re = re.compile(f"^\u2800{{{run_over}}}+([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")


    # numbers = "\u283c[\u2801|\u2803|\u2809|\u2819|\u2811|\u280b|\u281b|\u2813|\u280a|\u281a]+\u2832 "
    # first_line_re = re.compile(
    #    f"^(\u2800{{{first_line_indent}}})(\u283c[\u2801\u2803\u2809\u2819\u2811\u280b\u281b\u2813\u280a\u281a]+\u2832) ([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+"
    #)
    #run_over_re = re.compile(
    #    f"^\u2800{{{run_over}}}+ ,mbvnhc([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+"
    #)

    def detect_list(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> Optional[DetectionResult]:
        lines = []
        new_cursor = cursor
        li_items = []
        brl = ''
        while line := first_line_re.match(text[new_cursor:]):
            lines.append(line.group(1))
            new_cursor += line.end()
            while line := run_over_re.match(text[new_cursor:]):
                lines.append(line.group(1))
                new_cursor += line.end()
            li_items.append("<li>" + "\u2800".join(lines) + "</li>")
            lines = []
        if li_items:
            brl ='<ul style="list-style-type: none">'+''.join(li_items) + "</ul>" 
        return (
            DetectionResult(new_cursor, state, 0.9, f"{output_text}<p>{brl}</p>\n")
            if brl
            else None
        )

    return detect_list
