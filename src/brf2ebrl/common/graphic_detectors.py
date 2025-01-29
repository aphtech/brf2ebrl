#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detector for Graphics"" currently for PDF"""
import logging
import os
import re
import sys
from pathlib import Path
from typing import Callable

from pypdf import PdfWriter, PdfReader

from brf2ebrl.common.detectors import _ASCII_TO_UNICODE_DICT
from brf2ebrl.parser import ParserContext, NotifyLevel

_page_number_pattern = re.compile(
    r"([A-Za-z]?,?[A-Za-z]?#[a-jA-J]+(?:-[A-Za-z]?,?[A-Za-z]#[A-Ja-j]+)?)$"
)
_braille_page_re = re.compile(r"([a-zA-Z]*#+[a-zA-z]*)$")
_references = {}


def create_images_references(
        brf_path: str, output_path: str, images_path: str
) -> dict[str, str]:
    """Creates the PDF files and the references dictionary. Returns the Reference dictionary"""
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

    def match_page_number(text: str) -> str:
        page_number_pattern = re.compile(
            r"([A-Za-z]?,?[A-Za-z]?#[a-jA-J]+(?:-[A-Za-z]?,?[A-Za-z]#[A-Ja-j]+)?)$"
        )
        lines = text.split("\n")

        for line in lines:
            match = page_number_pattern.search(line.strip())
            if match:
                return match.group(0)

        return ""

    def extract_page_number(page: str) -> str:
        text = page.extract_text(extraction_mode="layout")
        if text:
            page_number = match_page_number(text)
            return page_number
        return ""

    def write_pdf(bp_page_number: str, work_path: str, pdf_filename: str, pdf_page):
        bp_page_trans = bp_page_number.strip().upper().translate(_ASCII_TO_UNICODE_DICT)
        pdf_filename = pdf_filename.replace("#", "_")
        pdf_filename = pdf_filename.replace(",", "C")
        if bp_page_trans in _references:
            pdf_filename = pdf_filename.replace(
                ".pdf", f"_{len(_references[bp_page_trans]) + 1}.pdf"
            )
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
            for page_number, _ in enumerate(inputpdf.pages):
                page = inputpdf.pages[page_number]
                braille_page_number = extract_page_number(page)
                write_pdf(
                    braille_page_number,
                    ebrf_folder,
                    os.path.join(
                        "images",
                        f"{in_filename_base}_{braille_page_number.strip('#')}.pdf",
                    ),
                    inputpdf.pages[page_number],
                )

        if _references:
            break
    # logging.info(f" dictionary {_references}")
    # logging.info(f" size of dictionary {len(_references)}")
    return _references


def create_pdf_graphic_detector(
        brf_path: str, output_path: str, images_path: str
) -> Callable[[str, ParserContext], str] | None:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
    * argument:
    * filename None if no image file or folder
    *Returns:
    * Parser,
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
    _detect_braille_page_re = re.compile("(<\\?braille-ppn [\u2801-\u28ff]+\\?>)")
    _search_blank_re = re.compile("(?:<\\?blank-line\\?>\n){3,}")

    def get_key_for_page(brf_page: str, references: dict[str, str]) -> str:
        if brf_page in references:
            return brf_page

        brf_pages = brf_page.split("\u2824")
        if len(brf_pages) > 1:
            return brf_pages[1]
        return brf_pages[0]

    def detect_pdf(
            text: str, parser_context: ParserContext
    ) -> str:
        result_text = ""
        new_cursor = 0
        while line := _detect_braille_page_re.search(text, new_cursor):
            start_page = line.end()
            result_text += text[new_cursor:start_page]
            new_cursor = start_page
            braille_page = line.group(1).split()[1].split("?")[0].strip()
            braille_page = get_key_for_page(braille_page, _images_references)
            if braille_page in _images_references:
                if end_page := _detect_braille_page_re.search(text, new_cursor):
                    end_page = end_page.start()
                else:
                    end_page = len(text)
                if search_blank := _search_blank_re.search(text[start_page:end_page]):
                    end_page = new_cursor + search_blank.start()
                    new_cursor += search_blank.end()
                result_text += text[start_page:end_page]
                # the for loop takes care of multiple pages
                for file_ref in _images_references[braille_page]:
                    result_text += f'<object data="{Path(file_ref).as_posix()}" type="application/pdf" height="250" width="100" aria-label="{_auto_gen}{braille_page}"> <p>{_pdf_text} {braille_page}</p></object>'
                del _images_references[braille_page]

        if _images_references:
            unused_graphics = [x for x in _images_references.keys()]
            parser_context.notify(NotifyLevel.WARN, lambda: f"There were unused graphics for pages {unused_graphics}")

        return f"{result_text}{text[new_cursor:]}"

    return detect_pdf
