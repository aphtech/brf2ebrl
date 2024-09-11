#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Module for converting BRF to eBRF"""

import os
import shutil
from tempfile import TemporaryDirectory
from typing import Iterable, Callable

from brf2ebrl.common import PageLayout
from brf2ebrl.parser import detector_parser, parse
from brf2ebrl.plugin import Plugin, EBrlZippedBundler

__version__ = "0.1.0"

def convert(selected_plugin: Plugin, input_brf_list: Iterable[str], input_images: str, output_ebrf: str,
            detect_running_heads: bool, page_layout: PageLayout, is_cancelled: Callable[[], bool],
            progress_callback: Callable[[int, float], None]):
    with EBrlZippedBundler(output_ebrf) as out_bundle:
        with TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
            for index, brf in enumerate(input_brf_list):
                temp_file = os.path.join(temp_dir, selected_plugin.file_mapper(brf, index))
                selected_parser = selected_plugin.create_brf_parser(
                    page_layout=page_layout,
                    detect_running_heads=detect_running_heads,
                    brf_path=brf,
                    output_path=temp_file,
                    images_path=input_images
                )
                parser_steps = len(selected_parser)
                convert_brf2ebrl(brf, temp_file, selected_parser,
                                 progress_callback=lambda x: progress_callback(index, x / parser_steps),
                                 is_cancelled=is_cancelled)
            for root, dirs, files in os.walk(temp_dir):
                arch_path = os.path.relpath(root, start=temp_dir)
                for f in files:
                    arch_name = os.path.join(arch_path, f)
                    out_bundle.write_file(arch_name, os.path.join(root, f))


def bundle_as_zip(input_dir, out_file):
    with TemporaryDirectory() as out_temp_dir:
        temp_ebrf = shutil.make_archive(os.path.join(out_temp_dir, "output_ebrf"), "zip", input_dir)
        with open(temp_ebrf, "rb") as temp_ebrf_file:
            shutil.copyfileobj(temp_ebrf_file, out_file)


def convert_brf2ebrl(input_brf: str, output_ebrf: str, brf_parser: Iterable[detector_parser],
                     progress_callback: Callable[[int], None] = lambda x: None,
                     is_cancelled: Callable[[], bool] = lambda: False):
    brf = ""
    with open(input_brf, "r", encoding="utf-8") as in_file:
        brf += in_file.read()
    output_text = parse(
        brf,
        brf_parser, progress_callback=progress_callback, is_cancelled=is_cancelled
    )
    with open(output_ebrf, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)
