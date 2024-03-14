#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detector for Graphics"" currently for PDF"""
import logging
import os
import sys

import regex as re
from PyPDF2 import PdfWriter, PdfReader

from brf2ebrf.common.detectors import _ASCII_TO_UNICODE_DICT
from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def create_images_references(brf_path: str, output_path: str, images_path: str) -> dict:
    """Creates the PDF files and the references dictionary. Returns the Reference dictionary"""
    _braille_page_re = re.compile(r"([a-zA-Z]*#+[a-zA-z]*)$")
    _references = {}
    ebrf_folder = os.path.split(output_path)[0]
    in_filename_base = os.path.split(brf_path)[1].split(".")[0]

    if os.path.exists(ebrf_folder) and not os.path.isdir(ebrf_folder):
        logging.error("Can not create {ebrf_folder} file already exists.")
        sys.exit()

    if not os.path.exists(ebrf_folder):
        try:
            os.makedirs(os.path.join(ebrf_folder, "images"))
        except:
            logging.error(f"Failed to create '{ebrf_folder}'.")
            sys.exit()

    images_files = [
        os.path.join(images_path, s)
        for s in os.listdir(images_path)
        if re.match(f"{in_filename_base}.*\.pdf", s, re.IGNORECASE)
    ] if images_path and os.path.isdir(images_path) else [images_path]
    images_files = [x for x in images_files if x and os.path.exists(x)]

    if not images_files:
        logging.error(f"No images path or folder found {images_path}")
        return {}

    # visitor code for the pdf parser
    parts = []

    def visitor_body(text, cm, tm, fontDict, fontSize):
        y = tm[5]
        if y < 50 and text.strip(" \n\r\l\f"):
            text = text.strip("_:")
            parts.append(text.strip(" \n\r\l\f"))

    def write_pdf(bp_page_number, work_path, pdf_filename, pdf_page):
        bp_page_trans = bp_page_number.strip().upper().translate(_ASCII_TO_UNICODE_DICT)

        if bp_page_trans in _references.keys():
            _references[bp_page_trans].append(pdf_filename)
        else:
            _references[bp_page_trans] = [pdf_filename]

        output = PdfWriter()
        output.add_page(pdf_page)
        with open(os.path.join(work_path, pdf_filename), "wb") as outputStream:
            output.write(outputStream)

    for image_file in images_files:
        inputpdf = PdfReader(open(image_file, "rb"))
        left_page = False
        for page_number in range(len(inputpdf.pages)):
            parts = []
            inputpdf.pages[page_number].extract_text(visitor_text=visitor_body)
            braille_page_number = "\n".join(parts)
            parts = braille_page_number.strip(" \n\r\l\f%").split()
            if parts and _braille_page_re.match(parts[-1]):
                braille_page_number = parts[-1].strip()
                if left_page:
                    write_pdf(
                        braille_page_number,
                        ebrf_folder,
                        os.path.join("images", f"{in_filename_base}_{braille_page_number.strip('#')}_l.pdf"),
                        inputpdf.pages[page_number - 1],
                    )
                write_pdf(
                    braille_page_number,
                    ebrf_folder,
                    os.path.join("images", f"{in_filename_base}_{braille_page_number.strip('#')}.pdf"),
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


def create_pdf_graphic_detector(brf_path: str, output_path: str, images_path: str) -> Detector | None:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
    * argument:
    * filename None if no image file or folder
    *Returns:
    * DetectionResult,
    """

    # image references
    _images_references = create_images_references(brf_path, output_path, images_path)
    if _images_references == {}:
        return None

    # auto generated page text
    _auto_gen = "\u2801\u2825\u281e\u2815\u2800\u281b\u2811\u281d\u2811\u2817\u2801\u281e\u2811\u2800\u2820\u2820\u280f\u2819\u280b\u2800"
    _pdf_text = "\u2820\u2820\u280f\u2819\u280b\u2800\u280f\u2801\u281b\u2811\u2800"

    # regular expression matching blanks then a braile page number.
    _blank_lines = "(?:(\n<\\?blank-line\\?>))+"
    _braille_page_re = re.compile(f"{_blank_lines}(<\\?braille-page.*?\\?>)")

    def detect_pdf(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        new_cursor = cursor
        if line := _braille_page_re.match(text[new_cursor:]):
            braille_page = line.group(2).split()[1].split("?")[0].strip()
            href = ""
            if braille_page in _images_references:
                # the for loop takes care of left and right
                for file_ref in _images_references[braille_page]:
                    href += (
                            f'<p><a href="{file_ref}" '
                            + f' alt="{_auto_gen}{braille_page}"> '
                            + f"{_pdf_text}{braille_page}</a></p>"
                    )
                del _images_references[braille_page]
            new_cursor += line.end()
            return (
                DetectionResult(
                    new_cursor, state, 0.9, f"{output_text}{href}{line.group(2)}"
                )
                if href
                else None
            )

    return detect_pdf
