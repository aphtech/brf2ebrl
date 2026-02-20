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
from typing import Any, Callable, List, Set

import pdfplumber
import pypdf

from brf2ebrl.common import PageLayout, PageNumberPosition
from brf2ebrl.common.detectors import _ASCII_TO_UNICODE_DICT
from brf2ebrl.parser import ParserContext, NotifyLevel

# Import improved page number detection from pdfpl.py
PRINT_PAGE_RE = re.compile(r"""
^
(?:[;"])?                     # repeat / omit marker (optional)
(?:[pt])?                     # p or t prefix (optional)

(?:                           # main page expression - at least one component required
    (?:[a-z]{1,2}             # continuation letters (required if present)
        (?:,,[ivxlcdm]+)?     # roman numerals (optional with continuation)
        (?:\#[a-j]+)?         # numeric print page (optional with continuation)
        (?:,[a-z])?           # optional suffix letter
    )|
    (?:,,[ivxlcdm]+           # OR roman numerals (required if present)
        (?:\#[a-j]+)?         # numeric print page (optional with roman)
        (?:,[a-z])?           # optional suffix letter
    )|
    (?:\#[a-j]+               # OR numeric print page (required if present)
        (?:,[a-z])?           # optional suffix letter
    )|
    (?:,[a-z])                # OR just suffix letter (required if present)
)

(?:                           # optional page ranges (MULTIPLE ranges allowed)
    -
    (?:                       # range end - same structure as main
        (?:[a-z]{1,2}
            (?:,,[ivxlcdm]+)?
            (?:\#[a-j]+)?     # This should match #ha in #hj-#ha
            (?:,[a-z])?
        )|
        (?:,,[ivxlcdm]+
            (?:\#[a-j]+)?
            (?:,[a-z])?
        )|
        (?:\#[a-j]+           # This should match #ha in #hj-#ha
            (?:,[a-z])?
        )|
        (?:,[a-z])
    )
)*
$
""", re.VERBOSE | re.IGNORECASE)

# Much more flexible regex for catching patterns we might miss like #hj-#ha
FLEXIBLE_PAGE_RE = re.compile(r"""
^
(?:[;"])?                     # optional markers
(?:[pt])?                     # optional prefix
(?:
    [a-z]{1,4}|               # letters (up to 4)
    ,,[ivxlcdm]+|             # roman numerals
    \#[a-z0-9]+|              # print pages - more flexible
    ,[a-z]|                   # suffix letters
    [0-9]+                    # plain numbers
)
(?:
    [-]                       # dash for ranges
    (?:
        [a-z]{1,4}|           # letters (up to 4)
        ,,[ivxlcdm]+|         # roman numerals
        \#[a-z0-9]+|          # print pages - more flexible
        ,[a-z]|               # suffix letters
        [0-9]+                # plain numbers
    )
)*
$
""", re.VERBOSE | re.IGNORECASE)

# Very permissive regex for debugging - catches almost anything that could be a page number
DEBUG_PAGE_RE = re.compile(r"^[a-z0-9#,;\"pt-]{1,20}$", re.IGNORECASE)

# Braille PPN detection regex
BRAILLE_PPN_RE = re.compile(r"<\?braille-ppn ([\u2801-\u28ff]+)\?>")

# Reusable braille mapping for Unicode <-> ASCII conversions
ASCII_CHARS = (" A1B'K2L@CIF/MSP\"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:"
               "4\\0Z7(_?W]#Y)=\"")
UNICODE_CHARS = "".join(chr(x) for x in range(0x2800, 0x2840))
UNICODE_TO_ASCII = {
    unicode_char: ascii_char
    for ascii_char, unicode_char in zip(ASCII_CHARS, UNICODE_CHARS)
}

# Regex patterns for braille page detection within text
DETECT_BRAILLE_PPN_RE = re.compile(r"(<\?braille-ppn [\u2801-\u28ff]+\?>)")
SEARCH_BLANK_RE = re.compile(r"(?:<\?blank-line\?>\n){3,}")
SEARCH_SINGLE_BLANK_RE = re.compile(r"(?:<\?blank-line\?>\n)")

# Auto generated page text constants
AUTO_GEN_TEXT = (
    "\u2801\u2825\u281e\u2815\u2800\u281b\u2811"
    "\u281d\u2811\u2817\u2801\u281e\u2811\u2800\u2820\u2820\u280f\u2819\u280b\u2800"
)
PDF_TEXT = "\u2820\u2820\u280f\u2819\u280b\u2800\u280f\u2801\u281b\u2811\u2800"

_STATE = {
    "references": {},
    "pdf_cache": {},  # Cache for PDF processing to avoid recreating on subsequent runs
    "braille_ppns_cache": None,
    "current_volume_path": None,
}


def reset_pdf_detector_cache():
    """Reset all caches for the PDF detector - useful for testing or when processing new files"""
    _STATE["references"].clear()
    _STATE["pdf_cache"].clear()
    _STATE["braille_ppns_cache"] = None
    _STATE["current_volume_path"] = None
    logging.info("PDF detector cache has been reset")


def extract_braille_ppns_from_text(text: str) -> Set[str]:
    """
    Extract all braille page numbers from text using regex pattern.
    Pattern: <?braille-ppn (<number>)?>

    Args:
        text: The full text to search for braille PPNs

    Returns:
        Set of braille page numbers found in the text
    """
    # Always re-extract PPNs for new volumes since each volume may have different PPNs
    # Pattern to match the existing format: <?braille-ppn [unicode braille]?>
    # This aligns with the existing detector pattern
    matches = BRAILLE_PPN_RE.findall(text)

    for match in matches:
        # Convert to ASCII using the proper mapping
        ascii_version = ''
        for char in match:
            if char in UNICODE_TO_ASCII:
                ascii_version += UNICODE_TO_ASCII[char]
            else:
                ascii_version += '?'  # Mark unmappable characters

    # Only log braille PPN count for volumes with issues
    _STATE["braille_ppns_cache"] = set(matches)
    if not _STATE["braille_ppns_cache"]:
        logging.warning("No braille PPNs found in text - "
                       "PDF validation will accept all pages")

    return _STATE["braille_ppns_cache"]



def generate_ppn_variations(ppn: str) -> List[str]:
    """
    Generate variations for PPNs with dash handling.
    For example, #HJ-HA should also test for #HJ-#HA and vice versa.

    Args:
        ppn: The page number to create variations for (in ASCII format)

    Returns:
        List of variations to test
    """
    variations = [ppn]
    ppn_lower = ppn.lower()

    if '-' in ppn_lower:
        # If format is #HJ-HA, also try #HJ-#HA
        if '#' in ppn_lower and ppn_lower.count('#') == ppn_lower.count('-'):
            dash_pos = ppn_lower.find('-')
            if 0 < dash_pos < len(ppn_lower) - 1:
                after_dash = ppn_lower[dash_pos + 1:]
                if not after_dash.startswith('#'):
                    variation_with_hash = (
                        ppn_lower[:dash_pos + 1] + '#' + after_dash)
                    variations.append(variation_with_hash)

        # If format is #HJ-#HA, also try #HJ-HA
        if ppn_lower.count('#') > 1:
            dash_pos = ppn_lower.find('-')
            if 0 < dash_pos < len(ppn_lower) - 2:
                after_dash = ppn_lower[dash_pos + 1:]
                if after_dash.startswith('#'):
                    variation_without_hash = (
                        ppn_lower[:dash_pos + 1] + after_dash[1:])
                    variations.append(variation_without_hash)

    return variations


def extract_text_blocks_from_pdf(page) -> List[str]:
    """
    Extract text blocks from PDF page using pypdfplumber.

    Args:
        page: pdfplumber page object

    Returns:
        List of text strings from the page blocks
    """
    text_blocks = []

    try:
        # Use pdfplumber's extract_words to get all text blocks
        words = page.extract_words()

        # Extract just the text content from each word/block
        for word in words:
            word_text = word['text'].strip()
            text_blocks.append(word_text)

        # Also try to extract full text and split by lines as backup
        full_text = page.extract_text()
        if full_text:
            for line in full_text.split('\n'):
                line = line.strip()
                if line and line not in text_blocks:
                    text_blocks.append(line)

    except OSError as e:
        logging.warning("Could not extract text blocks: %s", e)

    return text_blocks


def _normalize_ppn_text(value: str) -> str:
    return value.strip().lower()


def _unicode_braille_to_ascii(ppn: str) -> str:
    ascii_ppn = ''
    for char in ppn:
        if char in UNICODE_TO_ASCII:
            ascii_ppn += UNICODE_TO_ASCII[char]
    return ascii_ppn


def _build_ppn_variation_map(braille_ppns_list: List[str]) -> dict[str, str]:
    variation_map: dict[str, str] = {}
    for original_ppn in braille_ppns_list:
        ascii_ppn = _unicode_braille_to_ascii(original_ppn)
        for variation in generate_ppn_variations(ascii_ppn):
            variation_map[_normalize_ppn_text(variation)] = original_ppn
    return variation_map


def _expected_print_position(page_layout: PageLayout, page_count: int) -> PageNumberPosition:
    return (
        page_layout.odd_print_page_number
        if page_count % 2
        else page_layout.even_print_page_number
    )


def _matches_horizontal_zone(
    x0: float,
    x1: float,
    page_width: float,
    expected_position: PageNumberPosition,
) -> bool:
    if expected_position == PageNumberPosition.NONE:
        return True

    right_threshold = page_width * 0.58
    left_threshold = page_width * 0.42

    if expected_position.is_right():
        return x0 >= right_threshold
    if expected_position.is_left():
        return x1 <= left_threshold
    return True


def _collect_page_word_lines(page) -> list[dict[str, Any]]:
    words = page.extract_words()
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w.get("top", 0.0), w.get("x0", 0.0)))
    lines: list[dict[str, Any]] = []
    tolerance = 3.0

    for word in sorted_words:
        text = word.get("text", "").strip()
        if not text:
            continue

        top = float(word.get("top", 0.0))
        x0 = float(word.get("x0", 0.0))
        x1 = float(word.get("x1", x0))

        if not lines or abs(top - lines[-1]["top_ref"]) > tolerance:
            lines.append({
                "top_ref": top,
                "min_top": top,
                "max_bottom": float(word.get("bottom", top)),
                "words": [{"text": text, "x0": x0, "x1": x1, "top": top}],
            })
        else:
            line = lines[-1]
            line["min_top"] = min(line["min_top"], top)
            line["max_bottom"] = max(line["max_bottom"], float(word.get("bottom", top)))
            line["words"].append({"text": text, "x0": x0, "x1": x1, "top": top})

    for line in lines:
        line["words"].sort(key=lambda w: w["x0"])

    return lines


def _find_matching_ppn_in_positioned_words(
    page,
    braille_ppns_list: List[str],
    page_layout: PageLayout,
    page_count: int,
) -> str | None:
    if not braille_ppns_list:
        return None

    variation_map = _build_ppn_variation_map(braille_ppns_list)
    if not variation_map:
        return None

    lines = _collect_page_word_lines(page)
    if not lines:
        return None

    expected_position = _expected_print_position(page_layout, page_count)
    page_width = float(page.width or 1.0)
    page_height = float(page.height or 1.0)

    lines_per_page = max(page_layout.lines_per_page, 1)
    strict_header_lines = 3
    extended_header_lines = min(max(6, strict_header_lines), lines_per_page)
    strict_header_y = page_height * (strict_header_lines / lines_per_page)
    extended_header_y = page_height * (extended_header_lines / lines_per_page)

    candidates: list[tuple[int, str]] = []
    for line in lines:
        top = float(line["min_top"])
        if expected_position.is_top() and top > extended_header_y:
            continue
        if expected_position.is_bottom() and top < (page_height - extended_header_y):
            continue

        words = line["words"]
        if not words:
            continue

        rightmost = max(words, key=lambda w: w["x1"])
        leftmost = min(words, key=lambda w: w["x0"])

        for word in words:
            normalized = _normalize_ppn_text(word["text"])
            matched_ppn = variation_map.get(normalized)
            if not matched_ppn:
                continue

            score = 100
            x0 = float(word["x0"])
            x1 = float(word["x1"])

            if not _matches_horizontal_zone(x0, x1, page_width, expected_position):
                continue

            if expected_position.is_top():
                if top <= strict_header_y:
                    score += 20
                elif top <= extended_header_y:
                    score += 5
                else:
                    score -= 35
            elif expected_position.is_bottom():
                bottom_threshold = page_height - strict_header_y
                extended_bottom_threshold = page_height - extended_header_y
                if top >= bottom_threshold:
                    score += 20
                elif top >= extended_bottom_threshold:
                    score += 5
                else:
                    score -= 35

            if expected_position.is_right() and word is rightmost:
                score += 10
            if expected_position.is_left() and word is leftmost:
                score += 10

            if len(words) > 1:
                score -= 6

            candidates.append((score, matched_ppn))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_ppn = candidates[0]
    return best_ppn if best_score >= 60 else None


def find_matching_ppn_in_blocks(text_blocks: List[str],
                                braille_ppns_list: List[str]) -> str | None:
    """
    Find a matching PPN by searching through text blocks against PPNs in reverse order.

    Args:
        text_blocks: List of text blocks from the PDF
        braille_ppns_list: List of known braille PPNs (will search in reverse order)

    Returns:
        Matching braille PPN string or None if not found
    """
    if not text_blocks or not braille_ppns_list:
        return None

    variation_map = _build_ppn_variation_map(braille_ppns_list)

    # Search PPNs in reverse order (last to first)
    for block_text in text_blocks:
        block_text_clean = _normalize_ppn_text(block_text)

        if block_text_clean in variation_map:
            return variation_map[block_text_clean]

        for candidate_variation, original_ppn in variation_map.items():
            if candidate_variation in block_text_clean:
                return original_ppn

    return None


def is_valid_page_number_candidate(text: str) -> bool:
    """
    Validate if a text string is a reasonable page number candidate.
    Filters out obvious false positives before further processing.

    Args:
        text: Text to validate

    Returns:
        True if it could be a page number
    """
    if not text or len(text.strip()) == 0:
        return False

    text_clean = text.strip().lower()

    # Exclude obvious non-page-number words
    common_words = {
        'in', 'on', 'of', 'at', 'to', 'for', 'the', 'a', 'an', 'is', 'it', 'be', 'as',
        'and', 'or', 'but', 'not', 'with', 'from', 'by', 'up', 'out', 'if', 'about',
        'page', 'chapter', 'section', 'figure', 'table', 'part', 'unit', 'this', 'that',
        'they', 'them', 'their', 'there', 'then', 'than', 'when', 'where', 'what', 'who',
        'how', 'why', 'can', 'may', 'will', 'would', 'should', 'could', 'must', 'shall',
        'do', 'does', 'did', 'have', 'has', 'had', 'was', 'were', 'are', 'am', 'been',
        'being', 'give', 'given', 'go', 'went', 'gone', 'see', 'saw', 'seen',
        'know', 'knew', 'known', 'think', 'thought', 'look', 'looked', 'find', 'found',
        'take', 'taken', 'took', 'make', 'made', 'come', 'came', 'work', 'worked', 'use',
        'used', 'say', 'said', 'tell', 'told', 'ask', 'asked', 'try', 'tried'
    }

    if text_clean in common_words:
        return False

    # Exclude very long strings (probably not page numbers)
    if len(text_clean) > 20:
        return False

    # Exclude strings that are all punctuation
    if text_clean and all(not c.isalnum() for c in text_clean):
        return False

    # Exclude obvious article/document structure words
    structure_words = {
        'introduction', 'conclusion', 'summary', 'abstract', 'preface', 'foreword',
        'acknowledgments', 'bibliography', 'references', 'index', 'appendix',
        'contents', 'glossary', 'notes', 'copyright', 'title', 'subtitle',
        'heading', 'header', 'footer', 'margin', 'paragraph', 'line', 'text'
    }

    if any(word in text_clean for word in structure_words):
        return False

    return True



def extract_page_number_from_pdf(
    pdf_path: str,
    braille_ppns_list: List[str],
    page_layout: PageLayout,
    page_count: int,
) -> str | None:
    """
    Extract page number from a single PDF using direct PPN matching.

    Args:
        pdf_path: Path to the single-page PDF
        braille_ppns_list: List of known braille PPNs to match against

    Returns:
        Matching braille PPN or None if not found
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                page = pdf.pages[0]  # Single page PDF
                matching_ppn = _find_matching_ppn_in_positioned_words(
                    page,
                    braille_ppns_list,
                    page_layout,
                    page_count,
                )
                if matching_ppn:
                    return matching_ppn

                text_blocks = extract_text_blocks_from_pdf(page)
                return find_matching_ppn_in_blocks(text_blocks, braille_ppns_list)
    except OSError as e:
        logging.warning("Error extracting page number from %s: %s", pdf_path, e)
    return None


def _ensure_ebrf_folder(ebrf_folder: str) -> None:
    if os.path.exists(ebrf_folder) and not os.path.isdir(ebrf_folder):
        logging.error("Can not create %s file already exists.", ebrf_folder)
        sys.exit()

    if not os.path.exists(ebrf_folder):
        try:
            os.makedirs(os.path.join(ebrf_folder, "images"))
        except OSError:
            logging.error("Failed to create '%s'.", ebrf_folder)
            sys.exit()


def _collect_image_files(images_path: str | None, in_filename_base: str) -> list[str]:
    def _normalize_for_length_match(name: str) -> str:
        normalized = re.sub(r"[^a-z0-9]", "", name.lower())
        for suffix in ("graphics", "graphic", "images", "image", "pdf"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        return normalized

    def _strip_volume_leading_zeros(normalized: str) -> str:
        return re.sub(r"([vs])0+(\d)", r"\1\2", normalized)

    def _is_prefix_match(brf_base: str, pdf_base: str) -> bool:
        brf_clean = brf_base.strip().casefold()
        pdf_clean = pdf_base.strip().casefold()
        if brf_clean and pdf_clean.startswith(brf_clean):
            return True

        brf_norm = _normalize_for_length_match(brf_base)
        pdf_norm = _normalize_for_length_match(pdf_base)
        if brf_norm and pdf_norm.startswith(brf_norm):
            return True

        return False

    def _build_brf_prefixes(brf_base: str) -> list[str]:
        normalized = _normalize_for_length_match(brf_base)
        prefixes = [normalized] if normalized else []

        if normalized:
            stripped = _strip_volume_leading_zeros(normalized)
            if stripped and stripped != normalized:
                prefixes.append(stripped)

        tokens = [t for t in re.split(r"[^a-z0-9]+", brf_base.lower()) if t]
        if "00" in tokens:
            tokens_wo_zeros = [t for t in tokens if t != "00"]
            if tokens_wo_zeros:
                prefixes.append("".join(tokens_wo_zeros))

        return list(dict.fromkeys(prefixes))

    if images_path and os.path.isdir(images_path):
        strict_re = re.compile(
            f"{re.escape(in_filename_base)}.*\\.pdf",
            re.IGNORECASE,
        )
        strict_matches = [
            os.path.join(images_path, s)
            for s in os.listdir(images_path)
            if strict_re.match(s)
        ]

        if strict_matches:
            return [x for x in strict_matches if x and os.path.exists(x)]

        brf_prefixes = _build_brf_prefixes(in_filename_base)
        length_matches = []
        for filename in os.listdir(images_path):
            if not re.search(r"\.pdf$", filename, re.IGNORECASE):
                continue

            pdf_base = os.path.splitext(filename)[0]
            for brf_norm in brf_prefixes:
                if brf_norm and _is_prefix_match(brf_norm, pdf_base):
                    length_matches.append(os.path.join(images_path, filename))
                    break

        return [x for x in length_matches if x and os.path.exists(x)]

    return [x for x in [images_path] if x and os.path.exists(x)]


def _split_pdf_to_pages(
    image_file: str,
    full_subdir_path: str,
    pdf_subdir: str,
) -> list[dict[str, str | int]]:
    with open(image_file, 'rb') as pdf_file:
        pdf_reader = pypdf.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)

        logging.info("Processing PDF %s with %d pages", image_file, total_pages)

        split_pdf_paths = []
        pdf_counter = 1
        for page_num in range(total_pages):
            pdf_filename = f"{pdf_counter}.pdf"
            pdf_path_full = os.path.join(full_subdir_path, pdf_filename)

            pdf_writer = pypdf.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num])

            with open(pdf_path_full, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)

            split_pdf_paths.append({
                'full_path': pdf_path_full,
                'relative_path': os.path.join("images", pdf_subdir, pdf_filename),
                'pdf_counter': pdf_counter,
                'page_num': page_num
            })
            pdf_counter += 1

        return split_pdf_paths


def _match_split_pages(
    split_pdf_paths: list[dict[str, str | int]],
    braille_ppns_list: list[str],
    image_file: str,
    page_layout: PageLayout,
) -> tuple[int, int]:
    processed_pages = 0
    matched_pages = 0

    for split_info in split_pdf_paths:
        processed_pages += 1

        matching_ppn = extract_page_number_from_pdf(
            split_info['full_path'],
            braille_ppns_list,
            page_layout,
            int(split_info['pdf_counter']),
        )

        if matching_ppn:
            bp_page_trans = matching_ppn.strip().upper().translate(
                _ASCII_TO_UNICODE_DICT)
            if bp_page_trans in _STATE["references"]:
                _STATE["references"][bp_page_trans].append(
                    split_info['relative_path'])
            else:
                _STATE["references"][bp_page_trans] = [
                    split_info['relative_path']]

            matched_pages += 1
        else:
            logging.warning(
                "✗ PDF %s.pdf from %s: No matching PPN found",
                split_info['pdf_counter'], image_file)

    return processed_pages, matched_pages


def _process_image_file(
    image_file: str,
    ebrf_folder: str,
    braille_ppns_list: list[str],
    page_layout: PageLayout,
) -> tuple[int, int]:
    """
    Split a single image PDF into pages and match pages to braille PPNs.
    Returns (pages_processed, pages_matched).
    """
    # Create subdirectory for this source PDF to prevent overwrites
    pdf_subdir = os.path.splitext(os.path.basename(image_file))[0]
    full_subdir_path = os.path.join(ebrf_folder, "images", pdf_subdir)
    os.makedirs(full_subdir_path, exist_ok=True)

    try:
        split_pdf_paths = _split_pdf_to_pages(
            image_file, full_subdir_path, pdf_subdir)
        return _match_split_pages(
            split_pdf_paths, braille_ppns_list, image_file, page_layout)
    except OSError as e:
        logging.error("Error processing %s: %s", image_file, e)
        return 0, 0


def _log_processing_summary(
    in_filename_base: str,
    processed_pages: int,
    matched_pages: int,
    braille_ppns: Set[str],
) -> None:
    logging.info("Processing complete for volume %s:", in_filename_base)
    logging.info("  - Total PDF pages processed: %d", processed_pages)
    logging.info("  - Pages successfully matched: %d", matched_pages)
    logging.info("  - Pages not matched: %d", processed_pages - matched_pages)
    logging.info("  - Available braille PPNs: %d", len(braille_ppns))

    if processed_pages - matched_pages > 0:
        match_rate = (matched_pages / processed_pages) * 100
        logging.warning("Match rate: %.1f%% - %d pages did not match any braille PPNs",
                       match_rate, processed_pages - matched_pages)


def _get_reference_key(brf_page: str, references: dict[str, str]) -> str:
    """
    Get the appropriate key for a braille page from the references dictionary.
    Handles cases where the page might have prefix indicators.
    """
    if brf_page in references:
        return brf_page

    # Handle pages with prefix indicators (split by \u2824)
    brf_pages = brf_page.split("\u2824")
    if len(brf_pages) > 1:
        return brf_pages[1]
    return brf_pages[0]


def _prepare_volume_references(
    text: str,
    brf_path: str,
    output_path: str,
    images_path: str,
    page_layout: PageLayout,
    parser_context: ParserContext,
) -> bool:
    if _STATE["current_volume_path"] == brf_path:
        return True

    if _STATE["current_volume_path"] is not None:
        _STATE["references"].clear()
        _STATE["braille_ppns_cache"] = None

    _STATE["current_volume_path"] = brf_path

    braille_ppns = extract_braille_ppns_from_text(text)

    if not braille_ppns:
        logging.warning("No braille PPNs found in text - "
                      "cannot validate PDF pages")
        parser_context.notify(
            NotifyLevel.WARN,
            lambda: "No braille page numbers found in text for PDF validation"
        )
        return False

    _STATE["references"] = create_images_references(
        brf_path, output_path, images_path, braille_ppns, page_layout)

    if not _STATE["references"]:
        logging.warning("No valid PDF references created for volume %s",
                      brf_path)
        return False

    return True


def _extract_braille_page(line_match: re.Match) -> str:
    return line_match.group(1).split()[1].split("?")[0].strip()


def _consume_page_text(
    text: str,
    start_page: int,
    new_cursor: int,
) -> tuple[str, int]:
    if end_page := DETECT_BRAILLE_PPN_RE.search(text, new_cursor):
        end_page = end_page.start()
    else:
        end_page = len(text)

    if search_blank := SEARCH_BLANK_RE.search(text[start_page:end_page]):
        end_page = new_cursor + search_blank.start()
        new_cursor += search_blank.end()
    elif search_blank := SEARCH_SINGLE_BLANK_RE.search(text[start_page:end_page]):
        end_page = new_cursor + search_blank.start()
        new_cursor += search_blank.end()

    page_text = text[start_page:end_page]

    if search_blank := SEARCH_BLANK_RE.search(text[start_page:end_page]):
        end_page = new_cursor + search_blank.start()
        new_cursor += search_blank.end()

    return page_text, new_cursor


def _build_pdf_object_tags(braille_page: str) -> str:
    object_text = "<?blank-line?>\n"
    for file_ref in _STATE["references"][braille_page]:
        object_text += (
            f'<object data="{Path(file_ref).as_posix()}" '
            f'type="application/pdf" height="250" width="100" '
            f'aria-label="{AUTO_GEN_TEXT}{braille_page}"> '
            f'<p>{PDF_TEXT} {braille_page}</p></object>'
        )
    object_text += "<?blank-line?>\n"
    return object_text


def create_images_references(
    brf_path: str,
    output_path: str,
    images_path: str,
    braille_ppns: Set[str],
    page_layout: PageLayout = PageLayout(),
) -> dict[str, str]:
    """
    Creates the PDF files and the references dictionary using simplified PPN matching.

    This function processes PDF files and creates individual page PDFs, then attempts
    to match each page with known braille page numbers (PPNs).

    Args:
        brf_path: Path to the BRF file being processed
        output_path: Output directory path
        images_path: Path to the images/PDF files to process
        braille_ppns: Set of known braille page numbers

    Returns:
        Dictionary mapping braille PPNs to their corresponding PDF file paths
    """
    # Check if we've already processed this combination
    cache_key = f"{brf_path}_{images_path}_{page_layout}"
    if cache_key in _STATE["pdf_cache"]:
        return _STATE["pdf_cache"][cache_key]

    ebrf_folder = os.path.split(output_path)[0]
    in_filename_base = os.path.split(brf_path)[1].split(".")[0]

    _ensure_ebrf_folder(ebrf_folder)

    images_files = _collect_image_files(images_path, in_filename_base)

    if not images_files:
        logging.error("No images path or folder found %s", images_path)
        return {}

    # Convert braille PPNs set to list for reverse iteration
    braille_ppns_list = list(braille_ppns)

    processed_pages = 0
    matched_pages = 0

    for image_file in images_files:
        pages_processed, pages_matched = _process_image_file(
            image_file, ebrf_folder, braille_ppns_list, page_layout)
        processed_pages += pages_processed
        matched_pages += pages_matched

    # Log processing summary
    _log_processing_summary(
        in_filename_base, processed_pages, matched_pages, braille_ppns)

    # Cache the results
    _STATE["pdf_cache"][cache_key] = _STATE["references"]
    return _STATE["references"]


def create_pdf_graphic_detector(
    brf_path: str,
    output_path: str,
    images_path: str,
    page_layout: PageLayout = PageLayout(),
) -> Callable[[str, ParserContext], str] | None:
    """
    Creates a detector for finding graphic page numbers and matching with PDF pages.

    Args:
        brf_path: Path to the BRF file being processed
        output_path: Output path for the processed files
        images_path: Path to images folder or None if no images

    Returns:
        Parser function for detecting and processing PDF graphics, or None if no images
    """

    # Reset cache when detector is created (indicates new processing run)
    if _STATE["current_volume_path"] != brf_path:
        logging.info("New detector created for %s, resetting volume tracking",
                    brf_path)
        reset_pdf_detector_cache()

    def detect_pdf(text: str, parser_context: ParserContext) -> str:
        """
        Detect and process PDF graphics within the text.
        This inner function handles the actual detection and replacement logic.
        """
        if not _prepare_volume_references(
            text, brf_path, output_path, images_path, page_layout, parser_context
        ):
            return text

        # Process the text and create objects
        result_text = ""
        new_cursor = 0
        while line := DETECT_BRAILLE_PPN_RE.search(text, new_cursor):
            start_page = line.end()
            result_text += text[new_cursor:start_page]
            new_cursor = start_page
            braille_page = _extract_braille_page(line)
            braille_page = _get_reference_key(braille_page, _STATE["references"])
            if braille_page in _STATE["references"]:
                page_text, new_cursor = _consume_page_text(
                    text, start_page, new_cursor)
                result_text += page_text
                result_text += _build_pdf_object_tags(braille_page)
                del _STATE["references"][braille_page]

        return f"{result_text}{text[new_cursor:]}"

    return detect_pdf
