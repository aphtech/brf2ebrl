#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Script to convert a ASCII BRF into unicode Braille."""
import argparse

from brf2ebrl.common.detectors import convert_ascii_to_unicode_braille_bulk
from brf2ebrl.common.selectors import most_confident_detector
from brf2ebrl.parser import parse, detector_parser


def main():
    arg_parser = argparse.ArgumentParser(
        description="Converts a BRF to unicode Braille"
    )
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()
    brf = ""
    with open(args.brf, "r", encoding="utf-8") as in_file:
        brf = in_file.read()
    output_text = parse(
        brf,
        [
            detector_parser(
                "Unicode Braille", {}, [convert_ascii_to_unicode_braille_bulk], most_confident_detector
            )
        ],
    )
    with open(args.output_file, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


if __name__ == "__main__":
    main()
