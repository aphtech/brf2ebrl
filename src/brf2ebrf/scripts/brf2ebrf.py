"""Script to convert BRF into eBRF."""
import argparse
import os
import logging
import sys
from collections.abc import Iterable, Callable, Sequence

from brf2ebrf.bana import create_braille_page_detector, create_print_page_detector
from brf2ebrf.common import PageNumberPosition, PageLayout
from brf2ebrf.common.graphic_detectors import create_pdf_graphic_detector
from brf2ebrf.common.box_line_detectors import convert_box_lines, remove_box_lines_processing_instructions
from brf2ebrf.common.emphasis_detectors import convert_emphasis

from brf2ebrf.common.block_detectors import (
tn_indicators_block_matcher,
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
    create_running_head_detector,
    braille_page_counter_detector,
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
        brf_path: str = "",
        output_path: str = "",
        images_path: str = "",
        detect_running_heads: bool = True,
) -> Sequence[ParserPass]:
    return [
        x
        for x in [
            # Convert to unicode pass
            ParserPass(
                "Convert to unicode Braille",
                {},
                [convert_ascii_to_unicode_braille_bulk],
                most_confident_detector,
            ),
            # Detect Braille pages pass
            ParserPass(
                "Detect Braille pages",
                {"start_braille_page": True, "page_count": 1},
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
                "Detect print pages",
                {"page_count": 1},
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
                "Detect running head",
                {},
                [
                    create_running_head_detector(3),
                    braille_page_counter_detector,
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            )
            if detect_running_heads
            else None,
            # Remove form feeds pass.
            ParserPass(
                "Remove form feeds",
                {},
                [
                    lambda t, c, s, o: DetectionResult(
                        len(t), s, 1.0, o + t[c:].replace("\f", "\n")
                    )
                ],
                most_confident_detector,
            ),
            # Detect blank lines pass
            ParserPass(
                "Detect blank lines",
                {},
                [convert_blank_line_to_pi, detect_and_pass_processing_instructions],
                most_confident_detector,
            ),
            # convert box lines pass
            ParserPass(
                "Convert box lines to div tags",
                {},
                [convert_box_lines],
                most_confident_detector,
            ),
            # Detect blocks pass
            ParserPass(
                "Detect blocks",
                {},
                [
                    create_centered_detector(page_layout.cells_per_line, 3, "h1"),
                    create_cell_heading(6, "h3"),
                    create_cell_heading(4, "h2"),
                    create_paragraph_detector(6,4, tn_indicators_block_matcher, confidence=0.95),
                    create_paragraph_detector(2, 0),
                    create_table_detector(),  # might add arguments later
                    create_list_detector(0, 2),
                    detect_pre,
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            ),
# remove box line processing instructions
            ParserPass(
                "Remove  box lines processing instructions",
                {},
                [remove_box_lines_processing_instructions],
                most_confident_detector,
            ),
# convert Emphasis
            ParserPass(
                "Convert Emphasis",
                {},
                [convert_emphasis],
                most_confident_detector,
            ),
            # PDF Graphics
            create_image_detection_parser_pass(brf_path, images_path, output_path),
            # Convert print page numbers to ebrf tags
            ParserPass(
                "Print page numbers to ebrf",
                {},
                [create_ebrf_print_page_tags()],
                most_confident_detector,
            ),
            # Make complete XHTML pass
            ParserPass(
                "Make complete XML",
                {},
                [
                    lambda t, c, s, o: DetectionResult(
                        len(t), s, 1.0, f"{o}{_XHTML_HEADER}{t[c:]}{_XHTML_FOOTER}"
                    )
                ],
                most_confident_detector,
            ),
        ]
        if x is not None
    ]


def create_image_detection_parser_pass(brf_path, images_path, output_path):
    if images_path and (image_detector := create_pdf_graphic_detector(brf_path, output_path, images_path)):
        return ParserPass(
            "Convert PDF to single files and links",
            {},
            [image_detector],
            most_confident_detector,
        )
    else:
        return None


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(asctime)s:%(module)s:%(message)s"
    )
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to eBRF")
    arg_parser.add_argument(
        "--no-running-heads",
        help="Don't detect running heads",
        dest="running_heads",
        default=True,
        action="store_false",
    )
    arg_parser.add_argument(
        "-cpl, --cells-per-line",
        help="Number of cells per line",
        dest="cells_per_line",
        default=40,
        type=int,
    )
    arg_parser.add_argument(
        "-lpp, --lines-per-page",
        help="Number of lines per page",
        dest="lines_per_page",
        default=25,
        type=int,
    )
    arg_parser.add_argument(
        "-i", "--images", type=str, help="The images folder or file."
    )
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()

    input_brf = args.brf
    if not input_brf:
        logging.error("No input Brf to be converted.")
        arg_parser.print_help()
        sys.exit()

    output_ebrf = args.output_file
    output_file_path = os.path.split(output_ebrf)[0]
    if not os.path.exists(output_file_path) and not os.path.isdir(output_file_path):
        try:
            os.makedirs(output_file_path)
        except OSError:
            logging.error(f"Failled to create output path {output_file_path}")
            sys.exit()

    input_images = args.images
    if input_images and not os.path.exists(input_images):
        logging.error(f"{input_images} is not a filename or folder.")
        arg_parser.print_help()
        sys.exit()

    page_layout = PageLayout(
        odd_braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
        odd_print_page_number=PageNumberPosition.TOP_RIGHT,
        cells_per_line=args.cells_per_line,
        lines_per_page=args.lines_per_page,
    )
    running_heads = args.running_heads
    parser = create_brf2ebrf_parser(
        page_layout=page_layout,
        detect_running_heads=running_heads,
        brf_path=input_brf,
        output_path=output_ebrf,
        images_path=input_images,
    )
    convert_brf2ebrf(input_brf, output_ebrf, parser)


def convert_brf2ebrf(input_brf: str, output_ebrf: str, parser: Iterable[ParserPass],
                     progress_callback: Callable[[int], None] = lambda x: None,
                     is_cancelled: Callable[[], bool] = lambda: False):
    brf = ""
    with open(input_brf, "r", encoding="utf-8") as in_file:
        brf += in_file.read()
    output_text = parse(
        brf,
        parser, progress_callback=progress_callback, is_cancelled=is_cancelled
    )
    with open(output_ebrf, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


if __name__ == "__main__":
    main()
