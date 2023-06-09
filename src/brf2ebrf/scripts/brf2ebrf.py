"""Script to convert BRF into eBRF."""
import argparse
from collections.abc import Iterable

from brf2ebrf.bana import create_braille_page_detector, PageLayout, PageNumberPosition
from brf2ebrf.common.block_detectors import detect_pre, create_cell_heading, create_centered_detector
from brf2ebrf.common.detectors import convert_ascii_to_unicode_braille_bulk, detect_and_pass_processing_instructions, \
    convert_blank_line_to_pi
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


def create_brf2ebrf_parser(page_layout: PageLayout = PageLayout()) -> Iterable[ParserPass]:
    return [
        # Convert to unicode pass
        ParserPass({}, [convert_ascii_to_unicode_braille_bulk], most_confident_detector),
        # Detect Braille pages pass
        ParserPass(
            {"StartBraillePage": True}, [
                create_braille_page_detector(
                    page_layout=page_layout,
                    separator="\u2800" * 3,
                    format_output=lambda pc, pn: f"<?braille-page {pn}?>{pc}"),
                detect_and_pass_processing_instructions
            ], most_confident_detector),
        # Remove form feeds pass.
        ParserPass({}, [
            lambda t, c, s, o: DetectionResult(c + 1, s, 1.0, o + t[c] if t[c] != "\f" else o)
        ], most_confident_detector),
        # Detect blank lines pass
        ParserPass({}, [convert_blank_line_to_pi, detect_and_pass_processing_instructions],
                   most_confident_detector),
        # Detect blocks pass
        ParserPass({}, [create_centered_detector(page_layout.cells_per_line, 3, "h1"), create_cell_heading(6, "h3"),
                        create_cell_heading(4, "h2"), detect_pre, detect_and_pass_processing_instructions],
                   most_confident_detector),
        # Make complete XHTML pass
        ParserPass({}, [
            lambda t, c, s, o: DetectionResult(len(t), s, 1.0, f"{o}{_XHTML_HEADER}{t[c:]}{_XHTML_FOOTER}")
        ], most_confident_detector)
    ]


def main():
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to eBRF")
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()
    page_layout = PageLayout(braille_page_number=PageNumberPosition.BOTTOM_RIGHT)
    brf = ""
    with open(args.brf, "r", encoding="utf-8") as in_file:
        brf = in_file.read()
    output_text = parse(brf, create_brf2ebrf_parser(page_layout))
    with open(args.output_file, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


if __name__ == "__main__":
    main()
