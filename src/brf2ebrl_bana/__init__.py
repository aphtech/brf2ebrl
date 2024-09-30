#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""BANA specific components for processing BRF."""

from typing import Sequence

from brf2ebrl.common import PageLayout
from brf2ebrl.common.block_detectors import create_centered_detector, create_cell_heading, create_paragraph_detector, \
    create_table_detector, create_list_detector, detect_pre, create_block_paragraph_detector
from brf2ebrl.common.box_line_detectors import remove_box_lines_processing_instructions, tag_boxlines
from brf2ebrl.common.detectors import detect_and_pass_processing_instructions, \
    create_running_head_detector, braille_page_counter_detector, convert_blank_line_to_pi, xhtml_fixup_detector, \
    translate_ascii_to_unicode_braille
from brf2ebrl.common.emphasis_detectors import tag_emphasis
from brf2ebrl.common.graphic_detectors import create_pdf_graphic_detector
from brf2ebrl.common.page_numbers import create_ebrf_print_page_tags
from brf2ebrl.common.selectors import most_confident_detector
from brf2ebrl.parser import detector_parser, Parser
from brf2ebrl.plugin import create_plugin
from brf2ebrl_bana.pages import create_braille_page_detector, \
    create_print_page_detector
from brf2ebrl_bana.tn_detectors import tn_indicators_block_matcher, \
    tag_inline_tn, tag_symbols_list_tn


def create_brf2ebrl_parser(
        page_layout: PageLayout = PageLayout(),
        brf_path: str = "",
        output_path: str = "",
        images_path: str = "",
        detect_running_heads: bool = True,
) -> Sequence[Parser]:
    return [
        x
        for x in [
            # Convert to unicode pass
            Parser(
                "Convert to unicode Braille",
                translate_ascii_to_unicode_braille
            ),
            # Detect Braille pages pass
            detector_parser(
                "Detect Braille pages",
                {"start_braille_page": True, "page_count": 1},
                [
                    create_braille_page_detector(
                        page_layout=page_layout,
                        separator="\u2800" * 3,
                        format_output=lambda pc, pn: f"<?braille-page {pn}?>\n{pc}",
                    ),
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            ),
            detector_parser(
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
            detector_parser(
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
            Parser(
                "Remove form feeds",
                lambda text, check_cancellation: text.replace("\f", "")
            ),
            # Detect blank lines pass
            detector_parser(
                "Detect blank lines",
                {},
                [convert_blank_line_to_pi, detect_and_pass_processing_instructions],
                most_confident_detector,
            ),
            # convert box lines pass
            Parser(
                "Convert box lines to div tags",
                tag_boxlines
            ),
            # Detect blocks pass
            detector_parser(
                "Detect blocks",
                {},
                [
                    create_centered_detector(page_layout.cells_per_line, 3, "h1"),
                    create_cell_heading(6, "h3"),
                    create_cell_heading(4, "h2"),
                    create_paragraph_detector(6, 4, tn_indicators_block_matcher, confidence=0.95),
                    create_paragraph_detector(2, 0),
                    create_block_paragraph_detector(),
                    create_table_detector(),  # might add arguments later
                    create_list_detector(0, 2),
                    detect_pre,
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            ),
            # remove box line processing instructions
            detector_parser(
                "Remove  box lines processing instructions",
                {},
                [remove_box_lines_processing_instructions],
                most_confident_detector,
            ),
            Parser(
                "Detecting inline TNs",
                tag_inline_tn
            ),
            Parser(
                "Detect TN symbols lists",
                tag_symbols_list_tn
            ),
            # convert Emphasis
            Parser(
                "Convert Emphasis",
                tag_emphasis
            ),
            # PDF Graphics
            create_image_detection_parser_pass(brf_path, images_path, output_path),
            # Convert print page numbers to ebrf tags
            detector_parser(
                "Print page numbers to ebrf",
                {},
                [create_ebrf_print_page_tags()],
                most_confident_detector,
            ),
            # Make complete HTML5 pass
            detector_parser(
                "Make complete XML",
                {},
                [
                    xhtml_fixup_detector
                ],
                most_confident_detector,
            ),
        ]
        if x is not None
    ]


PLUGIN = create_plugin(plugin_id="BANA", name="Convert BANA BRF to eBraille", brf_parser_factory=create_brf2ebrl_parser,
                       file_mapper=lambda input_file, index: f"vol{index}.html")


def create_image_detection_parser_pass(brf_path, images_path, output_path):
    if images_path and (image_detector := create_pdf_graphic_detector(brf_path, output_path, images_path)):
        return detector_parser(
            "Convert PDF to single files and links",
            {},
            [image_detector],
            most_confident_detector,
        )
    else:
        return None
