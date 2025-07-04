
#  Copyright (c) 2024. American Printing House for the Blind.
"""
#
git log
# This Source Code Form is subject to the terms of the Mozilla Public
415
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

Detectors for blocks
"""

import re

from collections.abc import Iterable, Callable

from brf2ebrl.parser import DetectionState, DetectionResult, Detector


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
    return (
        DetectionResult(cursor + len(brl), state, 0.4, f"{output_text}<pre>{brl}</pre>")
        if brl
        else None
    )


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
        return (
            DetectionResult(
                new_cursor, state, 0.9, f"{output_text}<{tag_name}>{brl}</{tag_name}>\n"
            )
            if brl
            else None
        )

    return detect_cell_heading


def create_centered_detector(
    cells_per_line: int, min_indent: int, tag_name: str
) -> Detector:
    """Creates a detector for detecting centered text."""
    heading_re = re.compile(
        f"(\u2800{{{min_indent},}})([\u2801-\u28ff][\u2800-\u28ff]*)\n+",
    )

    _next_line_re = re.compile(
        rf"{_BLANK_LINE_RE}\n|\u2836{{{cells_per_line/2},{cells_per_line}}}\n|\u283f{{{cells_per_line/2},{cells_per_line}}}\n|^[\u2801-\u28ff][\u2800-\u28ff]*\n"
    )

    def detect_centered(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        brl = ""
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
        if _next_line_re.match(text[new_cursor:]):
            brl = "\u2800".join(lines)
        return (
            DetectionResult(
                new_cursor, state, 0.9, f"{output_text}<{tag_name}>{brl}</{tag_name}>\n"
            )
            if brl
            else None
        )

    return detect_centered


def create_table_detector() -> Detector:
    """Creates a detector for finding simple tables more can be added"""
    seperator_re = re.compile(
        "((?:[\u2800-\u28ff]+?\n){1,2})(\u2810\u2812+?(?:\u2800\u2800\u2810\u2812+?)+?)\n"
    )

    def row_column_check(widths: list[int], line: str) -> bool:
        """compares each row to make sure it has the right seperator to see if it is a row"""
        i = 0
        for width in widths[:-1]:
            end_of_cell = i + width
            start_of_next_cell = end_of_cell + 2
            if line[end_of_cell:start_of_next_cell] != "\u2800\u2800":
                return False
            i = start_of_next_cell
        return True

    def get_line(brf_text: str, pos: int, widths: list[int]) -> int | None:
        """Gets each line after table header that matches table columns"""
        pos2 = brf_text[pos:].find("\n") + 1

        return pos2 if row_column_check(widths, brf_text[pos : pos + pos2]) else None

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
        col_widths = [len(col) for col in match.group(2).split("\u2800\u2800")]

        # create header
        header_lines = match.group(1).split("\n")
        table = ["<tr>"]
        if len(header_lines) > 1:
            pos = 0
            for index, width in enumerate(col_widths):
                cell_text = header_lines[0][pos : pos + width + 2].strip("\u2800")
                if cell_text and header_lines[1].strip("\u2800"):
                    cell_text += "\u2800"
                cell_text = (
                    "<th>"
                    + cell_text
                    + ""
                    + header_lines[1][pos : pos + width + 2].strip("\u2800")
                    + "</th>"
                )
                pos += width + 2
                table[0] += cell_text
        else:
            table[0] += wrap_and_join(
                "<th>{}</th>",
                [
                    cell.strip("\u2800")
                    for cell in header_lines[0].split("\u2800\u2800")
                ],
            )
        table[0] += "</tr>"
        # header done

        cursor += match.end(2) + 1
        # cells
        row = 0
        while end_cursor := get_line(text, cursor, col_widths):
            line = text[cursor : cursor + end_cursor]
            if line.startswith("\u2800\u2800"):
                sep = "\u2800"
            else:
                sep = ""
                table.append([""] * len(col_widths))
                row += 1

            for index, cell in enumerate(line.split("\u2800\u2800")):
                if index < len(col_widths):
                    # need this temp var because of backslashes.
                    cell_strip = cell.strip("\u2800\u2810\n")
                    table[row] += f"{sep}{cell_strip}"
            cursor += end_cursor

        complete_table = table[0] + "\n"
        complete_table += wrap_and_join(
            "<tr>{}</tr>\n", [wrap_and_join("<td>{}</td>", row) for row in table[1:]]
        )
        complete_table = f"<table>\n{complete_table}\n</table>"
        return DetectionResult(cursor, state, 0.9, f"{output_text}{complete_table}\n")

    return detect_table


# constants for list and paragraph.
_PRINT_PAGE_RE = "(?:<\\?print-page[ \u2800-\u28ff]*?\\?>)"
_RUNNING_HEAD_RE = "(?:<\\?running-head[ \u2800-\u28ff]*\\?>)"
_BRAILLE_PAGE_RE = "(?:<\\?braille-page[ \u2800-\u28ff]*\\?>)"
_BRAILLE_PPN_RE = "(?:<\\?braille-ppn [ \u2800-\u28ff]*\\?>)"
_BLANK_LINE_RE = "(?:<\\?blank-line\\?>)"
_PROCESSING_INSTRUCTION_RE = f"(?:(?:{_BRAILLE_PAGE_RE}\n)?(?:{_BRAILLE_PPN_RE}\n)?(?:{_PRINT_PAGE_RE}\n)?(?:{_RUNNING_HEAD_RE}\n)?)"


def _create_indented_block_finder(
    first_line_indent: int, run_over: int
) -> Callable[[str, int], (str | None, int)]:
    _first_line_re = re.compile(
        f"\u2800{{{first_line_indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)\n"
    )
    _run_over_re = re.compile(
        f"({_PROCESSING_INSTRUCTION_RE}?)\u2800{{{run_over}}}([\u2801-\u28ff][\u2800-\u28ff]*)\n"
    )

    def find_paragraph_braille(text: str, cursor: int) -> tuple[str | None, int]:
        if line := _first_line_re.match(text[cursor:]):
            lines = [line.group(1)]
            new_cursor = cursor + line.end()
            while line := _run_over_re.match(text[new_cursor:]):
                lines.append(line.group(1) + line.group(2))
                new_cursor += line.end()
            brl = "\u2800".join([x for x in lines if x is not None])
            return brl, new_cursor
        return None, cursor

    return find_paragraph_braille


def _no_indicators_block_matcher(
    brl: str, state: DetectionState, tags: tuple[str, str] = ("<p>", "</p>")
) -> tuple[str | None, DetectionState]:
    return f"{tags[0]}{brl}{tags[1]}", state


def create_paragraph_detector(
    first_line_indent: int,
    run_over: int,
    indicator_matcher: Callable[
        [str, DetectionState], (str | None, DetectionState)
    ] = _no_indicators_block_matcher,
    confidence: float = 0.9,
) -> Detector:
    """Creates a detector for finding paragraphs with the specified first line indent and run over."""
    find_paragraph_braille = _create_indented_block_finder(first_line_indent, run_over)

    def detect_paragraph(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        brl, new_cursor = find_paragraph_braille(text, cursor)
        if brl:
            tag, new_state = indicator_matcher(brl, state)
            if tag:
                return DetectionResult(
                    new_cursor, new_state, confidence, f"{output_text}{tag}\n"
                )
        return None

    return detect_paragraph


# tools for paragraphs and blocks:
def has_toc(lines: list[list[int, str, str]]) -> bool:
    """return if one of the tiems is a toc entry"""
    for line in lines:
        if re.search(r".*?\u2810{2,}.*", line[2]):
            return True
    return False


def is_block_paragraph(
    lines: list[list[str, int, str]], depth: int = 0, cells_per_line: int = 0
) -> bool:
    """Check if this is a list or block paragraph."""


    
    _roman_re = re.compile(
        "^\u280d{0,3}(\u2809\u280d|\u2809\u2819|\u2819?\u2809{0,3})(\u282d\u2809|\u282d\u2807|\u2807?\u282d{0,3})(\u280a\u282d|\u280a\u2827|\u2827?\u280a{0,3})\u2800[2800-28ff]+$"
    )
    _lower_alpha_with_period_re = re.compile(
        "[\u2801\u2803\u2805\u2807\u2809\u280a\u280b\u280d\u280e\u280f\u2811\u2813\u2815\u2817\u2819\u281a\u281b\u281d\u281e\u281f\u2825\u2827\u282d\u2835\u283a\u283d]+\u2832\u2800[2800-28ff]+"
    )
    _lower_alpha_with_paran_re = re.compile(
        "[\u2801\u2803\u2805\u2807\u2809\u280a\u280b\u280d\u280e\u280f\u2811\u2813\u2815\u2817\u2819\u281a\u281b\u281d\u281e\u281f\u2825\u2827\u282d\u2835\u283a\u283d]+\u2802\u28c1\u2800[\u2800-\u28ff]+"
    )
    _cells_per_line = cells_per_line
    _end_punctuation_equal_re = re.compile(".*[\u2832\u2826\u2816][\u2804\u2834]*$")

    # copy and remove just PI
    _lines = [line for line in lines if line[0] != -1]
    # if it is length one it is a block because who makes a 1 line list in braille
    if len(_lines) == 1:
        return True


    block_len = len(_lines)
    block = [line[2] for line in _lines if line[0] == depth]
    # if not all lines have depth  indent
    if len(block) != block_len:
        return False

    # Willo idea.
    # # if any of the lines start with a word that could fit on the previous line its a list
    i = 1
    line_len = len(_lines)
    while i < line_len:
        prev_line_len = len(_lines[i - 1][2]) + depth
        if prev_line_len < _cells_per_line:
            word = _lines[i][2].strip("\u2800").split("\u2800", maxsplit=1)[0]
            if (len(word) + 1) < (_cells_per_line - prev_line_len):
                return False
        i += 1

    # if all lines start with roman with out punctuation
    if not [line for line in block if not _roman_re.match(line)]:
        return False

    # if all lines start with letter  period  assume list with small letters or small roman
    if not [line for line in block if not _lower_alpha_with_period_re.match(line)]:
        return False

    # if all lines start with letter  right paran   assume list with small letters or small roman
    if not [line for line in block if not _lower_alpha_with_paran_re.match(line)]:
        return False

    # if all lines end in punctuation assume list
    if not [line for line in block if not _end_punctuation_equal_re.match(line)]:
        return False

    return True


def get_run_over_depth(
    lines: list[list[int, str]], cells_per_line: int
) -> list[list[list[int, str]]]:
    """Get the lists of the deepest groupings."""
    max_depth = 0
    current_depth = 0
    current_start = 0
    groupings = []

    for index, line in enumerate(lines):
        if line[0] > current_depth:
            current_depth = line[0]
            current_start = index
        elif line[0] < current_depth:
            if current_depth > max_depth:
                max_depth = current_depth
                groupings = [lines[current_start:index]]
            elif current_depth == max_depth:
                groupings.append(lines[current_start:index])
            current_depth = line[0]

    if current_depth == max_depth:
        groupings.append(lines[current_start:])
    elif current_depth > max_depth:
        groupings = [lines[current_start:]]

    for group in groupings:
        if is_block_paragraph(group, group[0][0], cells_per_line):
            return group[0][0]

    return 0


# detect block aligned paragraphs
def create_block_paragraph_detector(cells_per_line: int) -> Detector:
    """Creates a detector for finding blokc paragraphs"""
    first_line_re = re.compile("([\u2801-\u28ff][\u2800-\u28ff]*)\n")
    run_over_re = re.compile(
        "(\u2800{2}|\u2800{4}|\u2800{6}|\u2800{8}|\u2800{10}|\u2800{12}|\u2800{14})([\u2801-\u28ff][\u2800-\u28ff]*)\n"
    )

    pi_re = re.compile(
        f"((?:{_BRAILLE_PAGE_RE}\n)?(?:{_BRAILLE_PPN_RE}\n)?(?:{_PRINT_PAGE_RE}\n)?(?:{_RUNNING_HEAD_RE}\n)?)"
    )



    def match_block_line(
        lines: list[list[int, str, str]], current_line: str
    ) -> list[int, str, str]:
        """Match lines if they are part of a block"""

        # if this is a page processing instruction with a blank line after.
        _pattern = f"(?:(?:{_BRAILLE_PAGE_RE}[\n ])?(?:{_BRAILLE_PPN_RE}[\n ])?(?:{_PRINT_PAGE_RE}[\n ])?(?:</span role.*?</span>[\n ])?(?:{_RUNNING_HEAD_RE}[\n ])?{_BLANK_LINE_RE })"
        if re.match(_pattern, current_line):
            return []

        if line := first_line_re.match(current_line):
            return [0, "", line.group(1), line.end()]

        line = run_over_re.match(current_line)
        if lines and line:

            level = len(line.group(1))

            # create length of lines without pi
            levels = [level[0] for level in lines if level[0] != -1]
            levels_len = len(levels)
            # # create clean set of levels acending in a list for access
            levels = list(set(levels))

            if lines[-1][0] == -1:
                # check for heading on next page.
                run_over = get_run_over_depth(lines, cells_per_line)
                if has_toc(lines):
                    if run_over and level > run_over:
                        return []
                else:
                    if run_over and level >= run_over:
                        return []
                if level not in levels and level > (max(levels) + 2):
                    return []

            # this is to catch paragraphs after blocks with no blanks
            if (
                not has_toc(lines)
                and levels_len > 2
                and len(levels) == 1
                and levels[0] == 0
                and level == 2
                and is_block_paragraph(lines, 0, cells_per_line)
            ):
                return []

            return [level, "", line.group(2), line.end()]

        line = pi_re.match(current_line)
        if lines and line and line.group(1):
            return [-1, line.group(1), "", line.end()]

        return []

    def make_block_paragrap(lines: list[list[str, int, str]]) -> str:
        return (
            '<p class="left-justified">'
            + "\u2800".join([item for tup in lines for item in tup[1:]])
            + "</p>"
        )

    def detect_block_paragraph(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        brl = ""
        while line := match_block_line(lines, text[new_cursor:]):
            lines.append(line[:3])
            new_cursor += line[3]

        if lines and is_block_paragraph(lines, 0, cells_per_line):
            brl = make_block_paragrap(lines)
        return (
            DetectionResult(new_cursor, state, 0.91, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_block_paragraph


# detect lists
def create_list_detector(cells_per_line: int) -> Detector:
    """Creates a detector for finding blokc paragraphs"""
    first_line_re = re.compile("([\u2801-\u28ff][\u2800-\u28ff]*)\n")
    run_over_re = re.compile(
        "(\u2800{2}|\u2800{4}|\u2800{6}|\u2800{8}|\u2800{10}|\u2800{12}|\u2800{14})([\u2801-\u28ff][\u2800-\u28ff]*)\n"
    )

    pi_re = re.compile(
        f"((?:{_BRAILLE_PAGE_RE}\n)?(?:{_BRAILLE_PPN_RE}\n)?(?:{_PRINT_PAGE_RE}\n)?(?:{_RUNNING_HEAD_RE}\n)?)"
    )

    def join_list(lines: list[list[int, str, str]]) -> str:
        """
        First fine out if toc
        second if toc set class type
        third if toc spin through and replace dot 5 and make span and anchor
        check for dot five split if there take last item if not for anchor
        if not toc make list
        """
        list_head = '\n<ul style="list-style-type: none">'
        list_tail = "</ul>"
        list_str = f"{list_head}\n"
        for line in lines:
            if line[1]:
                list_str += f"{line[1]}\n"
            if line[2]:
                list_str += f"<li>{line[2]}</li>\n"
        list_str += f"{list_tail}\n"
        return list_str

    def match_list_line(
        lines: list[list[int, str, str]], current_line: str
    ) -> list[int, str, str]:
        """Match lines if they are possibly part of a list"""
        if has_toc(lines):
            return []

        # if this is a page processing instruction with a blank line after.
        _pattern = f"(?:(?:{_BRAILLE_PAGE_RE}[\n ])?(?:{_BRAILLE_PPN_RE}[\n ])?(?:{_PRINT_PAGE_RE}[\n ])?(?:</span role.*?</span>[\n ])?(?:{_RUNNING_HEAD_RE}[\n ])?{_BLANK_LINE_RE })"
        if re.match(_pattern, current_line):
            return []

        if line := first_line_re.match(current_line):
            return [0, "", line.group(1), line.end()]

        line = run_over_re.match(current_line)
        if lines and line:

            level = len(line.group(1))

            # create length of lines without pi
            levels = [level[0] for level in lines if level[0] != -1]
            levels_len = len(levels)
            # # create clean set of levels acending in a list for access
            levels = list(set(levels))

            if lines[-1][0] == -1:
                # check for heading on next page.
                run_over = get_run_over_depth(lines, cells_per_line)
                if run_over and level >= run_over:
                    return []
                if level not in levels and level > (max(levels) + 2):
                    return []

            # this is to catch paragraphs after blocks with no blanks
            if (
                levels_len > 2
                and len(levels) == 1
                and levels[0] == 0
                and level == 2
                and is_block_paragraph(lines, 0, cells_per_line)
            ):
                return []

            return [level, "", line.group(2), line.end()]

        line = pi_re.match(current_line)
        if lines and line and line.group(1):
            return [-1, line.group(1), "", line.end()]

        return []

    def build_list(
        lines: list[list[int, str, str]],
        index: int,
        length: int,
        levels: list[int],
        current_level: int,
    ) -> list:
        """Recursive list builder, preserving processing instructions and supporting nested lists"""
        list_level = []
        original_index = index

        while index < length:
            current = lines[index]
            next_line = lines[index + 1] if (index + 1) < length else None

            # Always include processing instructions
            if current[0] == -1:
                list_level.append(current)
                index += 1
                continue

            # Check for deeper nested structure
            if next_line and next_line[0] > current_level:
                list_level.append(current)
                nested_index_diff, nested_html = build_list(
                    lines, index + 1, length, levels, next_line[0]
                )
                # Avoid mutating original line â€” use a copy
                updated = current.copy()
                updated[2] += nested_html
                list_level[-1] = updated
                index += nested_index_diff + 1
                continue

            # Check for return to a shallower level
            if next_line and next_line[0] < current_level and next_line[0] != -1:
                list_level.append(current)
                index += 1
                break

            # Normal list entry
            list_level.append(current)
            index += 1

        # At deepest level, check if it's a block paragraph
        if current_level == levels[-1] and is_block_paragraph(
            list_level, current_level, cells_per_line
        ):
            joined = "".join(
                f"{line[1]}\u2800{line[2]}" if line[1] else line[2]
                for line in list_level
            )
            return [index - original_index, joined]

        # Otherwise, render HTML list, preserving PI lines
        return [index - original_index, join_list(list_level)]

    def make_lists(lines: list[list[int, str, str]]) -> str:
        """Make a list or nested list"""

        # create clean set of levels acending
        levels = list({level[0] for level in lines if level[0] != -1})

        # one level list
        if len(levels) == 1:
            return join_list(lines)

        #  nested list or over run list
        _, brl_str = build_list(lines, 0, len(lines), levels, 0)
        return brl_str

    def detect_list(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        brl = ""
        while line := match_list_line(lines, text[new_cursor:]):
            lines.append(line[:3])
            new_cursor += line[3]

        if lines and not is_block_paragraph(lines, 0, cells_per_line):
            brl = make_lists(lines)
        return (
            DetectionResult(new_cursor, state, 0.91, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_list


# detect TOC
def create_toc_detector(cells_per_line: int) -> Detector:
    """Creates a detector for finding TOC"""
    first_line_re = re.compile("([\u2801-\u28ff][\u2800-\u28ff]*)\n")
    run_over_re = re.compile(
        "(\u2800{2}|\u2800{4}|\u2800{6}|\u2800{8}|\u2800{10}|\u2800{12}|\u2800{14})([\u2801-\u28ff][\u2800-\u28ff]*)\n"
    )

    pi_re = re.compile(
        f"((?:{_BRAILLE_PAGE_RE}\n)?(?:{_BRAILLE_PPN_RE}\n)?(?:{_PRINT_PAGE_RE}\n)?(?:{_RUNNING_HEAD_RE}\n)?)"
    )

    def parse_and_create_toc_entry(line: str) -> str:
        """Do not use re because there were problems."""
        end_line = ""
        pos = line.find("<")
        if pos != -1:
            end_line = line[pos:]
            line = line[:pos].strip("\u2800 ")

        line = line.rsplit("\u2800", maxsplit=1)
        if len(line) < 2:
            return line[0]
        line[0] = line[0].strip("\u2810\u2800")
        return f"<span>{line[0]}</span> <span>{line[1]}</span>{end_line}"

    def join_list(lines: list[list[int, str, str]]) -> str:
        """
        First fine out if toc
        second if toc set class type
        third if toc spin through and replace dot 5 and make span and anchor
        check for dot five split if there take last item if not for anchor
        if not toc make list
        """
        toc = None
        for line in lines:
            if line[0] == -1:
                continue
            if re.match(r"(.*)(\u2800\u2810{2,}\u2800)(.*)", line[2]):
                toc = "toc"
            if toc:
                break

        if toc:
            for index, line in enumerate(lines):
                if line[0] != -1 and line[2]:
                    lines[index][2] = parse_and_create_toc_entry(lines[index][2])

        list_head = '\n<ul style="list-style-type: none">'
        list_tail = "</ul>"
        if toc:
            list_head = '<ol class="toc" style="list-style-type: none">'
            list_tail = "</ol>"

        list_str = f"{list_head}\n"
        for line in lines:
            if line[1]:
                list_str += f"{line[1]}\n"
            if line[2]:
                list_str += f"<li>{line[2]}</li>\n"
        list_str += f"{list_tail}\n"
        return list_str

    def is_toc_page_transition(
        current_line: str
    ) -> list[int, str, str]:
        """Return if we are crossing a toc blank page blank boundey.
        return the .match if found None if not
        """
        pattern = re.compile(
            r"(<\?blank-line\?>[\s]*?"
            r"<\?braille-page[ \u2801-\u28ff]+\?>[\s]*?"
            r"<\?braille-ppn[ \u2801-\u28ff]+\?>[\s]*?"
            r"(?:<\?print-page[ \u2801-\u28ff]+\?>[\s]*?)?"
            r"(?:<\?running-head[ \u2800-\u28ff]*?\?>[\s]*?)?"
            r"<\?blank-line\?>[\s]*)"
        )
        match = pattern.match(current_line)
        if match:
            return match
        return []

    def match_toc_line(
        lines: list[list[int, str, str]], current_line: str
    ) -> list[int, str, str]:
        """Match lines if they are possibly part of a Toc"""

        toc = is_toc_page_transition(current_line)
        if toc:
            if not lines:
                return []
            return [-1, toc.group(1), "", toc.end()]

        # if this is a page processing instruction with a blank line after.
        _pattern = f"(?:(?:{_BRAILLE_PAGE_RE}[\n ])?(?:{_BRAILLE_PPN_RE}[\n ])?(?:{_PRINT_PAGE_RE}[\n ])?(?:</span role.*?</span>[\n ])?(?:{_RUNNING_HEAD_RE}[\n ])?{_BLANK_LINE_RE })"
        if re.match(_pattern, current_line):
            return []

        if line := first_line_re.match(current_line):
            return [0, "", line.group(1), line.end()]

        line = run_over_re.match(current_line)
        if lines and line:

            level = len(line.group(1))

            # create length of lines without pi
            levels = [level[0] for level in lines if level[0] != -1]
            levels_len = len(levels)
            # # create clean set of levels acending in a list for access
            levels = list(set(levels))

            if lines[-1][0] == -1:
                # check for heading on next page.
                run_over = get_run_over_depth(lines, cells_per_line)
                if has_toc(lines):
                    if run_over and level > run_over:
                        return []
                else:
                    if run_over and level >= run_over:
                        return []
                if level not in levels and level > (max(levels) + 2):
                    return []

            # this is to catch paragraphs after blocks with no blanks
            if (
                not has_toc(lines)
                and levels_len > 2
                and len(levels) == 1
                and levels[0] == 0
                and level == 2
                and is_block_paragraph(lines, 0, cells_per_line)
            ):
                return []

            return [level, "", line.group(2), line.end()]

        line = pi_re.match(current_line)
        if lines and line and line.group(1):
            return [-1, line.group(1), "", line.end()]

        return []

    def build_list(
        lines: list[list[int, str, str]],
        index: int,
        length: int,
        levels: list[int],
        current_level: int,
    ) -> list:
        """Recursive list builder, preserving processing instructions and supporting nested lists"""
        list_level = []
        original_index = index

        while index < length:
            current = lines[index]
            next_line = lines[index + 1] if (index + 1) < length else None

            # Always include processing instructions
            if current[0] == -1:
                list_level.append(current)
                index += 1
                continue

            # Check for deeper nested structure
            if next_line and next_line[0] > current_level:
                list_level.append(current)
                nested_index_diff, nested_html = build_list(
                    lines, index + 1, length, levels, next_line[0]
                )
                # Avoid mutating original line â€” use a copy
                updated = current.copy()
                updated[2] += nested_html
                list_level[-1] = updated
                index += nested_index_diff + 1
                continue

            # Check for return to a shallower level
            if next_line and next_line[0] < current_level and next_line[0] != -1:
                list_level.append(current)
                index += 1
                break

            # Normal list entry
            list_level.append(current)
            index += 1

        # At deepest level, check if it's a block paragraph
        if current_level == levels[-1] and is_block_paragraph(
            list_level, current_level, cells_per_line
        ):
            joined = "".join(
                f"{line[1]}\u2800{line[2]}" if line[1] else line[2]
                for line in list_level
            )
            return [index - original_index, joined]

        # Otherwise, render HTML list, preserving PI lines
        return [index - original_index, join_list(list_level)]

    def make_toc(lines: list[list[int, str, str]]) -> str:
        """Make a list or nested list"""
        if not has_toc(lines):
            return []

        # create clean set of levels acending
        levels = list({level[0] for level in lines if level[0] != -1})

        # one level list
        if len(levels) == 1:
            return join_list(lines)

        #  nested list or over run list
        _, brl_str = build_list(lines, 0, len(lines), levels, 0)
        return brl_str

    def detect_toc(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        brl = ""
        while line := match_toc_line(lines, text[new_cursor:]):
            lines.append(line[:3])
            new_cursor += line[3]

        if lines and not is_block_paragraph(lines, 0, cells_per_line):
            brl = make_toc(lines)
        return (
            DetectionResult(new_cursor, state, 0.91, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_toc
