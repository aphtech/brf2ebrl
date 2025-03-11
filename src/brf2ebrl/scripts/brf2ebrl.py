#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Script to convert BRF into eBRF."""
import argparse
import logging
import os
from dataclasses import dataclass
from glob import glob

from brf2ebrl import convert, ParserContext
from brf2ebrl.common import PageNumberPosition, PageLayout
from brf2ebrl.parser import EBrailleParserOptions
from brf2ebrl.plugin import find_plugins

DISCOVERED_PARSER_PLUGINS = find_plugins()

@dataclass(frozen=True)
class PageStandard:
    name: str
    obpn: PageNumberPosition
    ebpn: PageNumberPosition
    oppn: PageNumberPosition
    eppn: PageNumberPosition

PAGE_LAYOUT_STANDARDS = [
    PageStandard(name="interpoint", obpn=PageNumberPosition.BOTTOM_RIGHT, ebpn=PageNumberPosition.NONE, oppn=PageNumberPosition.TOP_RIGHT, eppn=PageNumberPosition.TOP_RIGHT),
    PageStandard(name="single-side", obpn=PageNumberPosition.BOTTOM_RIGHT, ebpn=PageNumberPosition.BOTTOM_RIGHT, oppn=PageNumberPosition.TOP_RIGHT, eppn=PageNumberPosition.TOP_RIGHT)
]

class _ListPluginsAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        available_plugins_msg = "Available parser plugins:\n"
        available_plugins_msg += "\n".join(
            [f"  {plugin.id} - {plugin.name}" for plugin in DISCOVERED_PARSER_PLUGINS.values()])
        print(available_plugins_msg)
        parser.exit()


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:%(asctime)s:%(module)s:%(message)s"
    )
    parser_modules = [plugin for plugin in DISCOVERED_PARSER_PLUGINS.values()]
    default_plugin_id: str = parser_modules[0].id
    arg_parser = argparse.ArgumentParser(description="Converts a BRF to eBraille")
    arg_parser.add_argument("--logging", default="INFO", help="Set the logging level, should be one of the standard Python logging levels.")
    arg_parser.add_argument("--list-parsers", action=_ListPluginsAction, help="List parser plugins and exit")
    arg_parser.add_argument("--parser", dest="parser_plugin", default=default_plugin_id,
                            help="Specify the parser plugin")
    arg_parser.add_argument(
        "--no-running-heads",
        help="Don't detect running heads",
        dest="running_heads",
        default=True,
        action="store_false",
    )
    arg_parser.add_argument(
        "-pl, --page-layout",
        help="The page layout standard used for detecting page numbers",
        dest="page_layout",
        type=str,
        default=PAGE_LAYOUT_STANDARDS[0].name
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
    debug_args = arg_parser.add_argument_group(title="Debug options")
    debug_args.add_argument("-pp", "--parser-passes", type=int, default=None, help="Only run number of parser passes.")
    arg_parser.add_argument("-o", "--output", dest="output_file", help="The output file name", required=True)
    arg_parser.add_argument("brfs", help="The input BRFs to convert", nargs="+")
    args = arg_parser.parse_args()

    try:
        logging.root.setLevel(args.logging)
    except ValueError:
        logging.warning(f"Unable to set logging level to {args.logging}, using {logging.getLevelName(logging.root.level)} instead.")
    parser_plugin = [plugin for plugin in parser_modules if plugin.id == args.parser_plugin]
    if not parser_plugin:
        arg_parser.exit(status=-2, message="Parser not found")

    page_standard_name = args.page_layout
    page_standard = [x for x in PAGE_LAYOUT_STANDARDS if x.name == page_standard_name]
    if not page_standard:
        arg_parser.exit(status=-3, message=f"Standard not found, available standards: {', '.join(x.name for x in PAGE_LAYOUT_STANDARDS)}")
    page_standard = page_standard[0]

    input_brf = args.brfs
    if not input_brf:
        logging.error("No input Brf to be converted.")
        arg_parser.print_help()
        arg_parser.exit()
    else:
        input_brf = [x for f in input_brf for x in sorted(glob(f), key=lambda x: x.lower())]

    output_ebrf = args.output_file
    output_file_path = os.path.split(output_ebrf)[0]
    if not os.path.exists(output_file_path) and not os.path.isdir(output_file_path):
        try:
            os.makedirs(output_file_path)
        except OSError:
            logging.error(f"Failled to create output path {output_file_path}")
            arg_parser.exit()

    input_images = args.images
    if input_images and not os.path.exists(input_images):
        logging.error(f"{input_images} is not a filename or folder.")
        arg_parser.print_help()
        arg_parser.exit()

    page_layout = PageLayout(
        odd_braille_page_number=page_standard.obpn,
        even_braille_page_number=page_standard.ebpn,
        odd_print_page_number=page_standard.oppn,
        even_print_page_number=page_standard.eppn,
        cells_per_line=args.cells_per_line,
        lines_per_page=args.lines_per_page,
    )
    running_heads = args.running_heads
    notifications = []
    parser_options = {EBrailleParserOptions.page_layout: page_layout, EBrailleParserOptions.images_path: input_images, EBrailleParserOptions.detect_running_heads: running_heads}
    convert(parser_plugin[0], input_brf_list=input_brf, output_ebrf=output_ebrf, input_images=input_images, detect_running_heads=running_heads, page_layout=page_layout, parser_passes=args.parser_passes, parser_context=ParserContext(notify=lambda l,s: notifications.append(f"{logging.getLevelName(l)}: {s()}"), options=parser_options))
    if notifications:
        print("Problems detected whilst converting:")
        print("\n".join(notifications))


if __name__ == "__main__":
    main()
