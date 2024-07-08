#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""BANA specific components for processing BRF."""

from typing import Sequence

from brf2ebrf.common import PageLayout
from brf2ebrf.common.block_detectors import create_centered_detector, create_cell_heading, create_paragraph_detector, \
    create_table_detector, create_list_detector, detect_pre
from brf2ebrf.common.box_line_detectors import convert_box_lines, remove_box_lines_processing_instructions
from brf2ebrf.common.detectors import convert_ascii_to_unicode_braille_bulk, detect_and_pass_processing_instructions, \
    create_running_head_detector, braille_page_counter_detector, convert_blank_line_to_pi, xhtml_fixup_detector
from brf2ebrf.common.emphasis_detectors import convert_emphasis
from brf2ebrf.common.graphic_detectors import create_pdf_graphic_detector
from brf2ebrf.common.page_numbers import create_ebrf_print_page_tags
from brf2ebrf.common.selectors import most_confident_detector
from brf2ebrf.parser import DetectionResult, ParserPass
from brf2ebrf_bana.pages import create_braille_page_detector, \
    create_print_page_detector
from brf2ebrf_bana.tn_detectors import tn_indicators_block_matcher, detect_inline_tn, detect_symbols_list_tn

PLUGIN_ID = "BANA"
PLUGIN_NAME = "BANA"


def create_brf2ebrf_parser(
        page_layout: PageLayout = PageLayout(),
        brf_path: str = "",
        output_path: str = "",
        images_path: str = "",
        detect_running_heads: bool = True,
) -> Sequence[ParserPass]:
    return [
        x
        for x in [
            # Convert to unicode pass
            ParserPass(
                "Convert to unicode Braille",
                {},
                [convert_ascii_to_unicode_braille_bulk],
                most_confident_detector,
            ),
            # Detect Braille pages pass
            ParserPass(
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
            ParserPass(
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
            ParserPass(
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
            ParserPass(
                "Remove form feeds",
                {},
                [
                    lambda t, c, s, o: DetectionResult(
                        len(t), s, 1.0, o + t[c:].replace("\f", "")
                    )
                ],
                most_confident_detector,
            ),
            # Detect blank lines pass
            ParserPass(
                "Detect blank lines",
                {},
                [convert_blank_line_to_pi, detect_and_pass_processing_instructions],
                most_confident_detector,
            ),
            # convert box lines pass
            ParserPass(
                "Convert box lines to div tags",
                {},
                [convert_box_lines],
                most_confident_detector,
            ),
            # Detect blocks pass
            ParserPass(
                "Detect blocks",
                {},
                [
                    create_centered_detector(page_layout.cells_per_line, 3, "h1"),
                    create_cell_heading(6, "h3"),
                    create_cell_heading(4, "h2"),
                    create_paragraph_detector(6, 4, tn_indicators_block_matcher, confidence=0.95),
                    create_paragraph_detector(2, 0),
                    create_table_detector(),  # might add arguments later
                    create_list_detector(0, 2),
                    detect_pre,
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            ),
            # remove box line processing instructions
            ParserPass(
                "Remove  box lines processing instructions",
                {},
                [remove_box_lines_processing_instructions],
                most_confident_detector,
            ),
            ParserPass(
                "Detecting inline TNs",
                {},
                [detect_inline_tn],
                most_confident_detector
            ),
            ParserPass(
                "Detect TN symbols lists",
                {},
                [detect_symbols_list_tn],
                most_confident_detector
            ),
            # convert Emphasis
            ParserPass(
                "Convert Emphasis",
                {},
                [convert_emphasis],
                most_confident_detector,
            ),
            # PDF Graphics
            create_image_detection_parser_pass(brf_path, images_path, output_path),
            # Convert print page numbers to ebrf tags
            ParserPass(
                "Print page numbers to ebrf",
                {},
                [create_ebrf_print_page_tags()],
                most_confident_detector,
            ),
            # Make complete XHTML pass
            ParserPass(
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


def create_image_detection_parser_pass(brf_path, images_path, output_path):
    if images_path and (image_detector := create_pdf_graphic_detector(brf_path, output_path, images_path)):
        return ParserPass(
            "Convert PDF to single files and links",
            {},
            [image_detector],
            most_confident_detector,
        )
    else:
        return None
