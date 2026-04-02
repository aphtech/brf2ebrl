#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""NFB specific parser"""
import string
from typing import Sequence

from brf2ebrl import PageLayout
from brf2ebrl.common.block_detectors import create_centered_detector, create_cell_heading, create_paragraph_detector, \
    bp_indicators_block_matcher, create_toc_detector, create_list_detector, create_table_detector, detect_pre
from brf2ebrl.common.box_line_detectors import tag_boxlines, remove_box_lines_processing_instructions
from brf2ebrl.common.detectors import translate_ascii_to_unicode_braille, detect_and_pass_processing_instructions, \
    combine_detectors, braille_page_counter_detector, create_running_head_detector, \
    convert_blank_lines_to_processing_instructions, xhtml_fixup_detector
from brf2ebrl.common.emphasis_detectors import tag_emphasis
from brf2ebrl.common.graphic_detectors import create_pdf_graphic_detector
from brf2ebrl.common.page_numbers import create_ebrf_print_page_tags
from brf2ebrl.common.selectors import most_confident_detector
from brf2ebrl.parser import Parser, detector_parser
from brf2ebrl.plugin import create_plugin
from brf2ebrl_bana import create_braille_page_detector, create_print_page_detector, tn_indicators_block_matcher, \
    tag_inline_tn, tag_symbols_list_tn


def create_brf2ebrl_parser(
        page_layout: PageLayout = PageLayout(),
        brf_path: str = "",
        output_path: str = "",
        images_path: str = "",
        detect_running_heads: bool = True,
        *args,
        **kwargs
) -> Sequence[Parser]:
    return [
        x
        for x in [
            Parser(
                "Ensure only valid BRF ASCII, eg. control characters",
                lambda x,_: "".join(c for c in x if c in string.printable)
            ),
            Parser(
                "Transform to uppercase ASCII",
                lambda x,_: x.upper()
            ),
            # Convert to Unicode pass
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
                    combine_detectors([braille_page_counter_detector, create_running_head_detector(3)]),
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            )
            if detect_running_heads
            else None,
            # Remove form feeds pass.
            Parser(
                "Remove form feeds",
                lambda text, _: text.replace("\f", "")
            ),
            # Detect blank lines pass
            Parser(
                "Detect blank lines",
                convert_blank_lines_to_processing_instructions
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
                    create_paragraph_detector(
                        first_line_indent=6,
                        run_over=4,
                        layout=page_layout,
                        indicator_matcher=tn_indicators_block_matcher,
                        confidence=0.95,
                    ),
                    create_paragraph_detector(
                        first_line_indent=2,
                        run_over=0,
                        layout=page_layout,
                        confidence=0.9,
                    ),
                    create_toc_detector(page_layout.cells_per_line),
                    create_list_detector(page_layout.cells_per_line),
                    create_table_detector(),  # might add arguments later
                    detect_pre,
                    detect_and_pass_processing_instructions,
                ],
                most_confident_detector,
            ),
            # remove box line processing instructions
            Parser(
                "Remove  box lines processing instructions",
                remove_box_lines_processing_instructions
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
            create_image_detection_parser_pass(brf_path, images_path, output_path, page_layout),
            # Convert print page numbers to ebrf tags
            detector_parser(
                "Print page numbers to ebrf",
                {},
                [create_ebrf_print_page_tags()],
                most_confident_detector,
            ),
            # Make complete HTML5 pass
            Parser(
                "Make complete XML",
                xhtml_fixup_detector
            ),
            Parser(
                "Make processing instructions comments, eBraille is HTML5 and so processing instructions not valid.",
                lambda x,_: x.replace("<?", "<!--").replace("?>", "-->")
            ),
            Parser(
                "Convert u+2800 to regular space as per ebraille standard",
                lambda x,_: x.replace("\u2800", " ")
            )
        ]
        if x is not None
    ]


PLUGIN = create_plugin(plugin_id="NFB", name="Convert NFB BRF to eBraille", brf_parser_factory=create_brf2ebrl_parser,
                       file_mapper=lambda input_file, index: f"vol{index}.html")


def create_image_detection_parser_pass(brf_path, images_path, output_path, page_layout: PageLayout) -> Parser | None:
    if images_path and (image_detector := create_pdf_graphic_detector(brf_path, output_path, images_path, page_layout)):
        return Parser(
            "Convert PDF to single files and links",
            image_detector
        )
    else:
        return None
