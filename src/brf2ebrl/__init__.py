#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Module for converting BRF to eBRF"""

import os
from tempfile import TemporaryDirectory
from typing import Iterable, Callable
import zipfile

from brf2ebrl.common import PageLayout
from brf2ebrl.parser import detector_parser, parse, ParserContext, ParserException
from brf2ebrl.plugin import Plugin, EBrlZippedBundler

__version__ = "0.1.0"


def convert(selected_plugin: Plugin, input_brf_list: Iterable[str], output_ebrf: str,
            progress_callback: Callable[[int, float], None] = lambda x,y: None, parser_passes: int|None =None, parser_context: ParserContext = ParserContext()):
    with selected_plugin.create_bundler(output_ebrf, **parser_context.options) as out_bundle:
        with TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
            for index, brf in enumerate(expand_all_files(input_brf_list)):
                out_name = selected_plugin.file_mapper(brf, index)
                temp_file = os.path.join(temp_dir, out_name)
                selected_parser = selected_plugin.create_brf_parser(
                    brf_path=brf,
                    output_path=temp_file,
                    **parser_context.options
                )[:parser_passes]
                parser_steps = len(selected_parser)
                try:
                    out_bundle.write_volume(out_name, convert_brf2ebrl_str(brf, selected_parser,
                                         progress_callback=lambda x: progress_callback(index, x / parser_steps),
                                         parser_context = parser_context))
                except ParserException as e:
                    out_bundle.write_str(f"errors/{out_name}", e.text, False)
                    e.file_name = brf
                    e.add_note(f"Problem processing file {brf}, text is in bundle in file errors/{out_name}")
                    raise
            for root, dirs, files in os.walk(temp_dir):
                arch_path = os.path.relpath(root, start=temp_dir)
                for f in files:
                    arch_name = os.path.join(arch_path, f)
                    out_bundle.write_image(arch_name, os.path.join(root, f))


def convert_brf2ebrl(input_brf: str, output_ebrf: str, brf_parser: Iterable[detector_parser],
                     progress_callback: Callable[[int], None] = lambda x: None,
                     parser_context: ParserContext = ParserContext()):
    output_text = convert_brf2ebrl_str(input_brf, brf_parser, progress_callback, parser_context)
    with open(output_ebrf, "w", encoding="utf-8") as out_file:
        out_file.write(output_text)


def convert_brf2ebrl_str(input_brf: str, brf_parser: Iterable[detector_parser],
                         progress_callback: Callable[[int], None] = lambda x: None,
                         parser_context: ParserContext = ParserContext()) -> str:
    with open(input_brf, "r", encoding="utf-8") as in_file:
        brf = in_file.read()
        return parse(
            brf,
            brf_parser, progress_callback=progress_callback, parser_context=parser_context
        )

def expand_all_files(filenames):
    "Allows directory and zip files to be included in input"
    for filename in filenames:
        if os.path.isdir(filename):
            # Assume we want everything under that directory
            # including all subdirectories (recursive call)
            yield from expand_all_files(
                filename+os.sep+f for f in
                sorted(os.listdir(filename),key=lambda x: x.lower()))
        elif filename.lower().endswith(".zip"):
            # Assume we want everything inside that zip file
            # (unpack to temporary directory)
            with TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                yield from expand_all_files([temp_dir])
                # and now temp_dir is deleted, which is OK as
                # the caller processes each file immediately
                # after the yield: don't need to keep it longer
        else: yield filename
