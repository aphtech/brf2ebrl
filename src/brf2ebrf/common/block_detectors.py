#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detectors for blocks"""
import re
from collections.abc import Iterable, Callable

from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def detect_pre(
        text: str, cursor: int, state: DetectionState, output_text: str
) -> DetectionResult | None:
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
    heading_re = re.compile(f"\u2800{{{indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)\n+")

    def detect_cell_heading(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
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
    heading_re = re.compile(f"(\u2800{{{min_indent},}})([\u2801-\u28ff][\u2800-\u28ff]*)\n+", )

    def detect_centered(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
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


# constants for list and paragraph.
_PRINT_PAGE_RE = "(?:<\\?print-page[ \u2800-\u28ff]*?\\?>)"
_RUNNING_HEAD_RE = "(?:<\\?running-head[ \u2800-\u28ff]*\\?>)"
_BRAILLE_PAGE_RE = "(?:<\\?braille-page[ \u2800-\u28ff]*\\?>)"
_BLANK_LINE_RE = "(?:<\\?blank-line\\?>)"
_PROCESSING_INSTRUCTION_RE = f"(?:(?:(?:{_BLANK_LINE_RE}\n)?{_BRAILLE_PAGE_RE}\n{_PRINT_PAGE_RE}\n(?:{_RUNNING_HEAD_RE}\n)?(?:{_BLANK_LINE_RE}\n)?)|?:{_BRAILLE_PAGE_RE}\n(?:{_RUNNING_HEAD_RE}\n)?)|(?:{_PRINT_PAGE_RE}\n))"


def _create_indented_block_finder(first_line_indent: int, run_over: int) -> Callable[[str, int], (str | None, int)]:
    _first_line_re = re.compile(
        f" {{{first_line_indent}}}([\u2801-\u28ff][ \u2800-\u28ff]*\n)")
    _run_over_re = re.compile(
        f"({_PROCESSING_INSTRUCTION_RE}*) {{{run_over}}}([\u2801-\u28ff][ \u2800-\u28ff]*\n)")

    def find_paragraph_braille(text: str, cursor: int) -> (str | None, int):
        if line := _first_line_re.match(
                text[cursor:]
        ):
            lines = [line.group(1)]
            new_cursor = cursor + line.end()
            while line := _run_over_re.match(
                    text[new_cursor:]
            ):
                lines.append(line.group(1) + line.group(2))
                new_cursor += line.end()
            brl = "\u2800".join([x for x in lines if x is not None])
            return brl, new_cursor
        else:
            return None, cursor

    return find_paragraph_braille


def _no_indicators_block_matcher(brl: str, state: DetectionState, tags: (str, str) = ("<p>", "</p>")) -> (
        str | None, DetectionState):
    return f"{tags[0]}{brl}{tags[1]}", state


def create_paragraph_detector(first_line_indent: int, run_over: int,
                              indicator_matcher: Callable[[str, DetectionState], (
                                      str | None, DetectionState)] = _no_indicators_block_matcher,
                              confidence: float = 0.9) -> Detector:
    """Creates a detector for finding paragraphs with the specified first line indent and run over."""
    find_paragraph_braille = _create_indented_block_finder(first_line_indent, run_over)

    def detect_paragraph(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        brl, new_cursor = find_paragraph_braille(text, cursor)
        if brl:
            tag, new_state = indicator_matcher(brl, state)
            if tag:
                return DetectionResult(new_cursor, new_state, confidence, f"{output_text}{tag}\n")
        return None

    return detect_paragraph


def create_nested_list_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding lists with the specified first line indent and run over."""
    first_line_re = re.compile(
        f"^\u2800{{{first_line_indent}}}({_PROCESSING_INSTRUCTION_RE}|[\u2801-\u28ff][\u2800-\u28ff\n]*){_BLANK_LINE_RE}",
        re.MULTILINE)
    run_over_re = re.compile(
        f"\u2800{{{run_over},}}({_PROCESSING_INSTRUCTION_RE}|[\u2801-\u28ff][\u2800-\u28ff]*)(?:\n)")

    def detect_nested_list(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        li_items = []
        brl = ''
        if line := first_line_re.match(text[new_cursor:]):
            lines.append(line.group(1))
            new_cursor += line.end()
            li_items.append("<li>" + "\u2800".join(lines) + "</li>")
            lines = []
        if li_items:
            brl = '<ul style="list-style-type: none">' + ''.join(li_items) + "</ul>"
        return (
            DetectionResult(new_cursor, state, 0.9, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_nested_list


def create_list_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding lists with the specified first line indent and run over."""
    first_line_re = re.compile(
        f"^({_PROCESSING_INSTRUCTION_RE}*) {{{first_line_indent}}}([\u2801-\u28ff][ \u2800-\u28ff]*)(?:\n)")
    run_over_re = re.compile(
        f"({_PROCESSING_INSTRUCTION_RE}*) {{{run_over},}}([\u2801-\u28ff][ \u2800-\u28ff]*)(?:\n)")

    def detect_list(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        li_items = []
        brl = ''
        while line := first_line_re.match(text[new_cursor:]):
            lines.append(line.group(1) + line.group(2))
            new_cursor += line.end()
            while line := run_over_re.match(text[new_cursor:]):
                lines.append(line.group(1) + line.group(2))
                new_cursor += line.end()
            lines = [x for x in lines if x is not None]
            if lines:
                li_items.append("<li>" + "\u2800".join(lines) + "</li>")
            lines = []
        if li_items:
            brl = '<ul style="list-style-type: none">' + ''.join(li_items) + "</ul>"
        return (
            DetectionResult(new_cursor, state, 0.89, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_list


def create_table_detector() -> Detector:
    """Creates a detector for finding simple tables more can be added"""
    seperator_re = re.compile("((?:[\u2800-\u28ff]+?\n){1,2})(\u2810\u2812+?(?:\u2800\u2800\u2810\u2812+?)+?)\n")

    def row_column_check(widths: list[int], line: str) -> bool:
        """compares each row to make sure it has the right seperator to see if it is a row"""
        i = 0
        for width in widths[:-1]:
            end_of_cell = i + width
            start_of_next_cell = end_of_cell + 2
            if line[end_of_cell:start_of_next_cell] != '\u2800\u2800':
                return False
            i = start_of_next_cell
        return True

    def get_line(brf_text: str, pos: int, widths: list[int]) -> int | None:
        """Gets each line after table header that matches table columns"""
        pos2 = brf_text[pos:].find('\n') + 1

        return pos2 if row_column_check(widths, brf_text[pos:pos + pos2]) else None

    def wrap_and_join(fmt: str, items: Iterable[str]) -> str:
        """Wraps each element and joins into a single string."""
        return "".join([fmt.format(s) for s in items])

    def detect_table(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        match = seperator_re.match(text[cursor:])
        if not match:
            return None

        # code
        col_widths = [len(col) for col in match.group(2).split('\u2800\u2800')]

        # create header
        header_lines = match.group(1).split('\n')
        table = ['<tr>']
        if len(header_lines) > 1:
            pos = 0
            for index, width in enumerate(col_widths):
                cell_text = header_lines[0][pos:pos + width + 2].strip('\u2800')
                if cell_text and header_lines[1].strip('\u2800'):
                    cell_text += '\u2800'
                cell_text = "<th>" + cell_text + "" + header_lines[1][pos:pos + width + 2].strip('\u2800') + "</th>"
                pos += width + 2
                table[0] += cell_text
        else:
            table[0] += wrap_and_join("<th>{}</th>",
                                      [cell.strip("\u2800") for cell in header_lines[0].split('\u2800\u2800')])
        table[0] += '</tr>'
        # header done

        cursor += match.end(2) + 1
        # cells
        row = 0
        while end_cursor := get_line(text, cursor, col_widths):
            line = text[cursor:cursor + end_cursor]
            if line.startswith('\u2800\u2800'):
                sep = '\u2800'
            else:
                sep = ''
                table.append([''] * len(col_widths))
                row += 1

            for index, cell in enumerate(line.split('\u2800\u2800')):
                if index < len(col_widths):
                    # need this temp var because of backslashes.
                    cell_strip = cell.strip('\u2800\u2810\n')
                    table[row] += f"{sep}{cell_strip}"
            cursor += end_cursor

        complete_table = table[0] + "\n"
        complete_table += wrap_and_join("<tr>{}</tr>\n", [wrap_and_join("<td>{}</td>", row) for row in table[1:]])
        complete_table = f"<table>\n{complete_table}\n</table>"
        return DetectionResult(cursor, state, 0.9, f"{output_text}{complete_table}\n")

    return detect_table
