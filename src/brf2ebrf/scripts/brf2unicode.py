import argparse

from brf2ebrf.common_detectors import convert_ascii_to_unicode_braille_bulk
from brf2ebrf.common_selectors import most_confident_detector
from brf2ebrf.parser import parse, ParserPass


def main():
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to unicode Braille")
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()
    brf = ""
    with open(args.brf, "r") as f:
        for line in f.readlines():
            brf += line
    output_text = parse(brf, [ParserPass("Default", [convert_ascii_to_unicode_braille_bulk], most_confident_detector)])
    with open(args.output_file, "w") as f:
        f.write(output_text)


if __name__ == "__main__":
    main()
