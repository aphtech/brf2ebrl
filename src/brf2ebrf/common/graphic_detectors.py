"""Detector for Graphics"" currently for PDF"""
import regex as re
from collections.abc import Iterable
import logging
import sys
import os
from PyPDF2 import PdfWriter, PdfReader

from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def create_images_references(filename_path: str, images_path: str) -> dict:
    """Creates the PDF files and the references dictionary. Returns the Reference dictionary"""
    _braille_page_re = re.compile(r"([a-zA-Z]*#+[a-zA-z]*)$")
    _references = {}
    in_folder, in_filename_base = os.path.split(filename_path)
    if not in_folder or not os.path.isdir(in_folder):
        output_folder = os.getcwd()
    output_folder = os.path.join(in_folder, "images")

    if os.path.exists(output_folder) and not os.path.isdir(output_folder):
        logging.error("Can not create {output_folder} file already exists.")
        sys.exit()

    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except:
            logging.error(f"Failed to create '{output_folder}'.")
            sys.exit()

    in_filename_base = in_filename_base.split(".")[0]
    if images_path and os.path.isdir(images_path):
        _files = [
            os.path.join(images_path, s)
            for s in os.listdir(images_path)
            if re.match(f"{in_filename_base}.*\.pdf", s, re.IGNORECASE)
        ]
        if _files:
            images_path = _files[0]
        else:
            images_path = ""
    if not images_path or (images_path and not os.path.exists(images_path)):
        logging.error(f"No images path or folder found {images_path}")
        sys.exit()
    # visitor code for the pdf parser
    _parts = []

    def visitor_body(text, cm, tm, fontDict, fontSize):
        y = tm[5]
        if y < 50 and text.strip(" \n\r\l\f"):
            text = text.strip("_:")
            parts.append(text.strip(" \n\r\l\f"))

    def write_pdf(bp_page_number, pdf_filename, pdf_page):
        logging.info(f"page: {bp_page_number} pdf_file ref {pdf_filename}")
        if bp_page_number in _references.keys():
            _references[bp_page_number].append(pdf_filename)
        else:
            _references[bp_page_number] = [pdf_filename]

        output = PdfWriter()
        output.add_page(pdf_page)
        with open(pdf_filename, "wb") as outputStream:
            output.write(outputStream)

    logging.info("log 3")
    inputpdf = PdfReader(open(images_path, "rb"))
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
                    f"{output_folder}/{in_filename_base}_{braille_page_number.strip('#')}_l.pdf",
                    inputpdf.pages[page_number - 1],
                )
            write_pdf(
                braille_page_number,
                f"{output_folder}/{in_filename_base}_{braille_page_number.strip('#')}.pdf",
                inputpdf.pages[page_number],
            )
            left_page = False
        else:
            left_page = True
    return _references


def create_pdf_graphic_detector(brf_filename: str, images_path: str) -> Detector:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
    * argument:
    * filename None if no image file or folder
    *Returns:
    * DetectionResult,
    """

    # image references
    _images_references = create_images_references(brf_filename, images_path)

    # regular expression matching blanks then a braile page number.
    _blank_lines = "(?:(\n<\\?blank-line\\?>))+"
    _braille_page_re = re.compile(f"{_blank_lines}(<\\?braille-page.*\\?>)")

    def detect_pdf(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        if cursor % 80000 == 0:
            print(f"Cursor: {cursor} {_images_references}")
        return None

    return detect_pdf
