"""Detector for Graphics"" currently for PDF"""
import re
from collections.abc import Iterable
import logging
import sys
import os
from PyPDF2 import PdfWriter, PdfReader

from brf2ebrf.parser import DetectionState, DetectionResult, Detector


def create_images_references(filename_path: str, images_path: str) -> dict:
    """Creates the PDF files and the references dictionary. Returns the Reference dictionary"""
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
            if re.match(f"{output_filename}.*\.pdf", s, re.IGNORECASE)
        ]
        if _files:
            images_path = _files[0]
        else:
            images_path = ""
    if not images_path or (images_path and not os.path.exists(images_path)):
        logging.error(f"No images path or folder found {images_path}")
        sys.exit()

    #visitor code for the pdf parser
    _parts = []
def visitor_body(text, cm, tm, fontDict, fontSize):
    y = tm[5]
    if y <50 and text.strip(' \n\r\l\f'):
        text = text.strip('_:')
        parts.append(text.strip(' \n\r\l\f'))
    
    def write_pdf(base_filename,bp_page_number,pdf_page,left = False):
    fuck
        output = PdfWriter()
        output.add_page(pdf_page
        with open (f"{base_filename}.pdf","wb") as outputStream:
            output.write(outputStream)
    
    
    inputpdf = PdfReader(open(filename_path,"rb"))
    left_page = False
    while page_number in range(len(inputpdf.pages)):
        parts=[]
        inputpdf.pages[page_number].extract_text(visitor_text=visitor_body)
        braille_page_number  = "\n".join(parts)
        parts = braille_page_number.strip(' \n\r\l\f%').split()
        if parts and _braille_page_re.match(parts[-1]):
            braille_page_number =  parts[-1].strip()
            if left_page:
                write_pdf(braille_page_number,f"{output_folder}_{in_filename_base}_l",inputpdf.pages[page_number-1])
            write_pdf(braille_page_number,f"{output_folder}_{in_filename_base}",inputpdf.pages[page_number])
            left_page = False
        else:
            left_page = True 
    return _references


def create_pdf_graphic_detector(file_paths: list) -> Detector:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
    * argument:
    * filename None if no image file or folder
    *Returns:
    * DetectionResult,
    """
    _images_references = create_images_references(file_paths[0], file_paths[1])

    def detect_pdf(
        text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        if cursor % 10000 == 0:
            _images_references["a"] = "one"
            print(f"Cursor: {cursor} {_images_references}")
            return None

    return detect_pdf
