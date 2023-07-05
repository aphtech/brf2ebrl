"""Script to convert a ASCII BRF into unicode Braille."""
import argparse

from brf2ebrf.common.detectors import convert_ascii_to_unicode_braille_bulk
from brf2ebrf.common.selectors import most_confident_detector
from brf2ebrf.parser import parse, ParserPass


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
            ParserPass(
                {}, [convert_ascii_to_unicode_braille_bulk], most_confident_detector
            )
        ],
    )
    with open(args.output_file, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


if __name__ == "__main__":
    main()
