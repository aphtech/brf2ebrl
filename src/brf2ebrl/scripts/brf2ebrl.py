#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Script to convert BRF into eBRF."""
import argparse
import logging
import os

from brf2ebrl import convert_brf2ebrf
from brf2ebrl.common import PageNumberPosition, PageLayout
from brf2ebrl.plugin import find_plugins

DISCOVERED_PARSER_PLUGINS = find_plugins()


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

    parser_plugin = [plugin for plugin in parser_modules if plugin.id == args.parser_plugin]
    if not parser_plugin:
        arg_parser.exit(status=-2, message="Parser not found")

    input_brf = args.brf
    if not input_brf:
        logging.error("No input Brf to be converted.")
        arg_parser.print_help()
        arg_parser.exit()

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
        odd_braille_page_number=PageNumberPosition.BOTTOM_RIGHT,
        odd_print_page_number=PageNumberPosition.TOP_RIGHT,
        cells_per_line=args.cells_per_line,
        lines_per_page=args.lines_per_page,
    )
    running_heads = args.running_heads
    parser = parser_plugin[0].create_brf_parser(
        page_layout=page_layout,
        detect_running_heads=running_heads,
        brf_path=input_brf,
        output_path=output_ebrf,
        images_path=input_images,
    )
    convert_brf2ebrf(input_brf, output_ebrf, parser)


if __name__ == "__main__":
    main()
