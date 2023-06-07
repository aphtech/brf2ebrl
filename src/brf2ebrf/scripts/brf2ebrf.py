"""Script to convert BRF into eBRF."""
import argparse

from brf2ebrf.bana import create_braille_page_detector, PageLayout, PageNumberPosition
from brf2ebrf.common.detectors import convert_ascii_to_unicode_braille_bulk, detect_and_pass_processing_instructions, convert_blank_line_to_pi, convert_unknown_to_pre
from brf2ebrf.common.selectors import most_confident_detector
from brf2ebrf.parser import parse, ParserPass

xhtml_header = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/strict.dtd">
<html xmlns="http://www.w3.org/TR/xhtml1/strict" >
<body>
"""

xhtml_footer= """
</body>
</html>
"""
def main():
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to eBRF")
    arg_parser.add_argument("brf", help="The BRF to convert")
    arg_parser.add_argument("output_file", help="The output file name")
    args = arg_parser.parse_args()
    brf = ""
    with open(args.brf, "r", encoding="utf-8") as in_file:
        brf = in_file.read()
    output_text = parse(brf, [ParserPass({}, [convert_ascii_to_unicode_braille_bulk], most_confident_detector),
                              ParserPass({"StartBraillePage":True}, [create_braille_page_detector(
                                  page_layout=PageLayout(braille_page_number=PageNumberPosition.BOTTOM_RIGHT), separator="\u2800"*3,
                                  format_output=lambda pc, pn: f"<?braille-page {pn}?>{pc}"),
                                                              detect_and_pass_processing_instructions],
                                         most_confident_detector),
                              ParserPass({}, [convert_blank_line_to_pi, detect_and_pass_processing_instructions], most_confident_detector),
                              ParserPass({}, [convert_unknown_to_pre], most_confident_detector)
                              ])
    with open(args.output_file, "w", encoding="utf-8") as out_file:
        out_file.write(f"{xhtml_header}{output_text}{xhtml_footer}")


if __name__ == "__main__":
    main()
