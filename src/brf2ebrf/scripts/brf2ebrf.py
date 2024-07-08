#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Script to convert BRF into eBRF."""
import argparse
import os
import logging
import sys
from collections.abc import Iterable, Callable

from brf2ebrf_bana import create_brf2ebrf_parser
from brf2ebrf.common import PageNumberPosition, PageLayout

from brf2ebrf.parser import parse, ParserPass


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
