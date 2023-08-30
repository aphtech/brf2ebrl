"""Detectors for blocks"""
import re
from collections.abc import Iterable
#import logging

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
    heading_re = re.compile(f"\u2800{{{indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")

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
    heading_re = re.compile(f"(\u2800{{{min_indent},}})([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+", )

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


def create_paragraph_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding paragraphs with the specified first line indent and run over."""
    first_line_re = re.compile(f"^\u2800{{{first_line_indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n]")
    run_over_re = re.compile(f"^\u2800{{{run_over}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n]")

    def detect_paragraph(
            text: str, cursor: int, state: DetectionState, output_text: str
            
    ) -> DetectionResult | None:
        lines = []
        new_cursor = cursor
        if line := first_line_re.match(
                text[new_cursor:]
        ):
            lines.append(line.group(1))
            new_cursor += line.end()
            while line := run_over_re.match(
                    text[new_cursor:]
            ):
                lines.append(line.group(1))
                new_cursor += line.end()
        brl = "\u2800".join(lines)
        return DetectionResult(new_cursor, state, 0.9, f"{output_text}<p>{brl}</p>\n") if brl else None

    return detect_paragraph


def create_list_detector(first_line_indent: int, run_over: int) -> Detector:
    """Creates a detector for finding lists with the specified first line indent and run over."""
    first_line_re = re.compile(f"^\u2800{{{first_line_indent}}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")
    run_over_re = re.compile(f"^\u2800{{{run_over},}}([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+")


    # numbers = "\u283c[\u2801|\u2803|\u2809|\u2819|\u2811|\u280b|\u281b|\u2813|\u280a|\u281a]+\u2832 "
    # first_line_re = re.compile(
    #    f"^(\u2800{{{first_line_indent}}})(\u283c[\u2801\u2803\u2809\u2819\u2811\u280b\u281b\u2813\u280a\u281a]+\u2832) ([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+"
    #)
    #run_over_re = re.compile(
    #    f"^\u2800{{{run_over}}}+ ,mbvnhc([\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]+"
    #)

    def detect_list(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
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
                DetectionResult(new_cursor, state, 0.9, f"{output_text}{brl}\n")
            if brl
            else None
        )

    return detect_list

def create_table_detector() -> Detector:
    """Creates a detector for finding simple tables more can be added"""
    seperator_re = re.compile("((?:[\u2800-\u28ff]+?\n){1,2})(\u2810\u2812+?(?:\u2800\u2800\u2810\u2812+?)+?)\n")

    def row_column_check(widths: list[int], line: str) -> bool:
        """compares each row to make sure it has the right seperator to see if it is a row"""
        i=0
        for width in widths[:-1]:
            end_of_cell = i + width
            start_of_next_cell = end_of_cell + 2
            if line[end_of_cell:start_of_next_cell] != '\u2800\u2800':
                return False
            i = start_of_next_cell
        return True

    def get_line(brf_text: str,pos: int,widths: list[int]) -> int | None:
        """Gets each line after table header that matches table columns"""
        pos2 = brf_text[pos:].find('\n') + 1

        return pos2 if row_column_check(widths,brf_text[pos:pos+pos2]) else None

    def wrap_and_join(fmt: str, items: Iterable[str]) -> str:
        """Wraps each element and joins into a single string."""
        return "".join([fmt.format(s) for s in items])

    def detect_table(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        match = seperator_re.match(text[cursor:])
        if not match:
            return None
        
        #code
        col_widths=[len(l) for l in match.group(2).split('\u2800\u2800')]        


        #create header
        header_lines=match.group(1).split('\n')
        table=['<tr>']
        if len(header_lines)>1:
            pos=0
            for  index, width in enumerate(col_widths):
                cell_text = header_lines[0][pos:pos+width+2].strip('\u2800')
                if cell_text and header_lines[1].strip('\u2800'):
                    cell_text += '\u2800'
                cell_text = "<th>"+cell_text+""+header_lines[1][pos:pos+width+2].strip('\u2800')+"</th>" 
                pos+=width+2
                table[0] += cell_text
        else:
            table[0] += wrap_and_join("<th>{}</th>", [cell.strip("\u2800") for cell in header_lines[0].split('\u2800\u2800')])
        table[0] +='</tr>'
                #header done

        cursor+=match.end(2)+1
        #cells
        row=0
        while end_cursor := get_line(text,cursor,col_widths):
            line=text[cursor:cursor+end_cursor]
            if line.startswith('\u2800\u2800'):
                sep='\u2800'
            else:
                sep=''
                table.append(['']*len(col_widths))
                row += 1
            
            for  index, cell in  enumerate(line.split('\u2800\u2800')):
                if index < len(col_widths):
                    table[row][index] += sep + "" + cell.strip('\u2800\u2810\n')
            cursor+=end_cursor

        complete_table=table[0]+"\n"
        complete_table += wrap_and_join("<tr>{}</tr>\n", [wrap_and_join("<td>{}</td>", row) for row in table[1:]])
        complete_table =f"<table>\n{complete_table}\n</table>"    
        return DetectionResult(cursor, state, 0.9, f"{output_text}{complete_table}\n")

    return detect_table        
