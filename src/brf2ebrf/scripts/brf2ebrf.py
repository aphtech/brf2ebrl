"""Script to convert BRF into eBRF."""
import argparse
import logging
from collections.abc import Iterable

from brf2ebrf.bana import create_braille_page_detector, create_print_page_detector
from brf2ebrf.common import PageNumberPosition, PageLayout
from brf2ebrf.common.block_detectors import (
    detect_pre,
    create_cell_heading,
    create_centered_detector,
    create_paragraph_detector,
    create_list_detector,
    create_table_detector,
)
from brf2ebrf.common.detectors import (
    convert_ascii_to_unicode_braille_bulk,
    detect_and_pass_processing_instructions,
    convert_blank_line_to_pi,
    create_running_head_detector, braille_page_counter_detector,
)
from brf2ebrf.common.page_numbers import create_ebrf_print_page_tags
from brf2ebrf.common.selectors import most_confident_detector
from brf2ebrf.parser import parse, ParserPass, DetectionResult

_XHTML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/strict.dtd">
<html xmlns="http://www.w3.org/TR/xhtml1/strict" >
<body>
"""

_XHTML_FOOTER = """</body>
</html>
"""


def create_brf2ebrf_parser(
        page_layout: PageLayout = PageLayout(),
        detect_running_heads: bool = True,
) -> Iterable[ParserPass]:
    return [x for x in [
        # Convert to unicode pass
        ParserPass(
            "Convert to unicode Braille", {}, [convert_ascii_to_unicode_braille_bulk], most_confident_detector
        ),
        # Detect Braille pages pass
        ParserPass(
            "Detect Braille pages", {"StartBraillePage": True},
            [
                create_braille_page_detector(
                    page_layout=page_layout,
                    separator="\u2800" * 3,
                    format_output=lambda pc, pn: f"<?braille-page {pn}?>{pc}",
                ),
                detect_and_pass_processing_instructions,
            ],
            most_confident_detector,
        ),
        ParserPass(
            "Detect print pages", {},
            [
                create_print_page_detector(
                    page_layout=page_layout, separator="\u2800" * 3
                ),
                detect_and_pass_processing_instructions,
            ],
            most_confident_detector,
        ),
        # Running head pass
        ParserPass(
            "Detect running head", {},
            [create_running_head_detector(3), braille_page_counter_detector, detect_and_pass_processing_instructions],
            most_confident_detector
        ) if detect_running_heads else None,
        # Remove form feeds pass.
        ParserPass(
            "Remove form feeds", {},
            [
                lambda t, c, s, o: DetectionResult(
                    len(t), s, 1.0, o + t[c:].replace("\f", "\n")
                )
            ],
            most_confident_detector,
        ),
        # Detect blank lines pass
        ParserPass(
            "Detect blank lines", {},
            [convert_blank_line_to_pi, detect_and_pass_processing_instructions],
            most_confident_detector,
        ),
        # Detect blocks pass
        ParserPass(
            "Detect blocks", {},
            [
                create_centered_detector(page_layout.cells_per_line, 3, "h1"),
                create_cell_heading(6, "h3"),
                create_cell_heading(4, "h2"),
                create_paragraph_detector(2, 0),
                create_table_detector(),  # might add arguments later
                create_list_detector(0, 2),
                detect_pre,
                detect_and_pass_processing_instructions,
            ],
            most_confident_detector,
        ),
        # Convert print page numbers to ebrf tags
        ParserPass("Print page numbers to ebrf", {}, [create_ebrf_print_page_tags()], most_confident_detector),
        # Make complete XHTML pass
        ParserPass(
            "Make complete XML", {},
            [
                lambda t, c, s, o: DetectionResult(
                    len(t), s, 1.0, f"{o}{_XHTML_HEADER}{t[c:]}{_XHTML_FOOTER}"
                )
            ],
            most_confident_detector,
        ),
    ] if x is not None]


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(asctime)s:%(module)s:%(message)s")
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to eBRF")
    arg_parser.add_argument("--no-running-heads", help="Don't detect running heads", dest="running_heads", default=True, action="store_false")
    arg_parser.add_argument("-cpl, --cells-per-line", help="Number of cells per line", dest="cells_per_line", default=40, type=int)
    arg_parser.add_argument("-lpp, --lines-per-page", help="Number of lines per page", dest="lines_per_page", default=25, type=int)
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()
    page_layout = PageLayout(
        braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
        print_page_number=PageNumberPosition.TOP_RIGHT,
        cells_per_line=args.cells_per_line,
        lines_per_page=args.lines_per_page,
    )
    brf = ""
    with open(args.brf, "r", encoding="utf-8") as in_file:
        brf = in_file.read()
    output_text = parse(brf, create_brf2ebrf_parser(page_layout=page_layout, detect_running_heads=args.running_heads))
    with open(args.output_file, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


if __name__ == "__main__":
    main()
