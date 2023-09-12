"""Detector for Graphics"" currently for PDF"""
import re
from collections.abc import Iterable
import logging
import os
from PyPDF2 import PdfWriter, PdfReader

from brf2ebrf.parser import DetectionState, DetectionResult, Detector

def create_images_references (filename_path,images_path):

    return []

def create_pdf_graphic_detector(filename:str) -> Detector:
    """Creates a detector for finding graphic page numbers and matching with PDF pages
        * argument:
        * filename None if no image file or folder
        *Returns:
        * DetectionResult,
    """
    _filename =filename
    def detect_pdf(
            text: str, cursor: int, state: DetectionState, output_text: str
    ) -> DetectionResult | None:
        return None

    return detect_pdf
