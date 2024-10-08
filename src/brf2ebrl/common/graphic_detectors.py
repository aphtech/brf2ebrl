#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detector for Graphics"" currently for PDF"""
import logging
import os
import sys

import re
from pypdf import PdfWriter, PdfReader

from brf2ebrl.common.detectors import _ASCII_TO_UNICODE_DICT
from brf2ebrl.parser import DetectionState, DetectionResult, Detector


def create_images_references(
    brf_path: str, output_path: str, images_path: str
) -> dict[str, str]:
    """Creates the PDF files and the references dictionary. Returns the Reference dictionary"""
    _braille_page_re = re.compile(r"([a-zA-Z]*#+[a-zA-z]*)$")
    _references = {}
    ebrf_folder = os.path.split(output_path)[0]
    in_filename_base = os.path.split(brf_path)[1].split(".")[0]

    if os.path.exists(ebrf_folder) and not os.path.isdir(ebrf_folder):
        logging.error("Can not create %s file already exists.", ebrf_folder)
        sys.exit()

    if not os.path.exists(ebrf_folder):
        try:
            os.makedirs(os.path.join(ebrf_folder, "images"))
        except OSError:
            logging.error("Failed to create '%s'.", ebrf_folder)
            sys.exit()

    images_files = (
        [
            os.path.join(images_path, s)
            for s in os.listdir(images_path)
            if re.match(f"{in_filename_base}.*\\.pdf", s, re.IGNORECASE)
        ]
        if images_path and os.path.isdir(images_path)
        else [images_path]
    )
    images_files = [x for x in images_files if x and os.path.exists(x)]

    if not images_files:
        logging.error("No images path or folder found %s", images_path)
        return {}

    # visitor code for the pdf parser

    def visitor_body(text, tm):
        y = tm[5]
        if y < 50 and text.strip(" \n\r\f"):
            text = text.strip("_:")
            return [text.strip(" \n\r\f")]
        return []

    def write_pdf(bp_page_number: str, work_path: str, pdf_filename: str, pdf_page):
        bp_page_trans = bp_page_number.strip().upper().translate(_ASCII_TO_UNICODE_DICT)

        if bp_page_trans in _references:
            _references[bp_page_trans].append(pdf_filename)
        else:
            _references[bp_page_trans] = [pdf_filename]

        output = PdfWriter()
        output.add_page(pdf_page)
        with open(os.path.join(work_path, pdf_filename), "wb") as output_stream:
            output.write(output_stream)

    for image_file in images_files:
        with open(image_file, "rb") as input_file:
            inputpdf = PdfReader(input_file)
            left_page = False
            for page_number, _ in enumerate(inputpdf.pages):
                parts = []
                inputpdf.pages[page_number].extract_text(
                    visitor_text=lambda t, cm, tm, fd, fs: parts.extend(
                        visitor_body(t, tm)
                    )
                )
                braille_page_number = "\n".join(parts)
                parts = braille_page_number.strip(" \n\r\f%").split()
                if parts and _braille_page_re.match(parts[-1]):
                    braille_page_number = parts[-1].strip()
                    if left_page:
                        write_pdf(
                            braille_page_number,
                            ebrf_folder,
                            os.path.join(
                                "images",
                                f"{in_filename_base}_{braille_page_number.strip('#')}_l.pdf",
                            ),
                            inputpdf.pages[page_number - 1],
                        )
                    write_pdf(
                        braille_page_number,
                        ebrf_folder,
                        os.path.join(
                            "images",
                            f"{in_filename_base}_{braille_page_number.strip('#')}.pdf",
                        ),
                        inputpdf.pages[page_number],
                    )
                    left_page = False
                else:
                    left_page = True

        if _references:
            break
    # logging.info(f" dictionary {_references}")
    # logging.info(f" size of dictionary {len(_references)}")
    return _references


def create_pdf_graphic_detector(
    brf_path: str, output_path: str, images_path: str
) -> Detector | None:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
    * argument:
    * filename None if no image file or folder
    *Returns:
    * DetectionResult,
    """

    # image references
    _images_references = create_images_references(brf_path, output_path, images_path)
    if not _images_references:
        return None

    # auto generated page text
    _auto_gen = (
        "\u2801\u2825\u281e\u2815\u2800\u281b\u2811"
        + "\u281d\u2811\u2817\u2801\u281e\u2811\u2800\u2820\u2820\u280f\u2819\u280b\u2800"
    )
    _pdf_text = "\u2820\u2820\u280f\u2819\u280b\u2800\u280f\u2801\u281b\u2811\u2800"

    # regular expression matching braille page and one for search
    _detect_braille_page_re = re.compile("(<\\?braille-page [\u2801-\u28ff]+\\?>)")
    _search_blank_re = re.compile("(?:<\\?blank-line\\?>\n){3,}")

    def detect_pdf(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        new_cursor = cursor
        start_page = end_page = 0
        href = ""
        if line := _detect_braille_page_re.match(text[new_cursor:]):
            new_cursor += line.end()
            start_page = new_cursor
            braille_page = line.group(1).split()[1].split("?")[0].strip()
            if braille_page in _images_references:
                if end_page := _detect_braille_page_re.match(text[new_cursor:]):
                    end_page = new_cursor + end_page.start()
                else:
                    end_page = len(text)
                if search_blank := _search_blank_re.search(text[start_page:end_page]):
                    end_page = new_cursor + search_blank.start()
                    new_cursor += search_blank.end()
                # the for loop takes care of left and right
                for file_ref in _images_references[braille_page]:
                    href += (
                        f'<p><a href="{file_ref}" '
                        + f' alt="{_auto_gen}{braille_page}"> '
                        + f"{_pdf_text}{braille_page}</a></p>"
                    )
                del _images_references[braille_page]
        return (
            DetectionResult(
                new_cursor, state, 0.9, f"{output_text}{text[cursor:end_page]}{href}"
            )
            if href
            else None
        )

    return detect_pdf
