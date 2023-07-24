"""Some detectors common to multiple Braille codes/standards."""
import re
from enum import Enum, auto

from brf2ebrf.parser import DetectionResult, DetectionState, Detector

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)


class BraillePageType(Enum):
    UNSET = 0
    T = auto()
    P = auto()
    NORMAL = auto()


def convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Convert the entire BRF into unicode Braille in a single step."""
    return DetectionResult(len(text), state, 1.0, output_text + text[cursor:].translate(_ASCII_TO_UNICODE_DICT))


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Convert only th next character to unicode Braille."""
    return DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor].translate(_ASCII_TO_UNICODE_DICT))


def detect_and_pass_processing_instructions(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    """Detect and pass through processing instructions"""
    if text.startswith("<?", cursor):
        end_of_pi = text.find("?>", cursor) + 2
        if end_of_pi >= 4:
            return DetectionResult(end_of_pi, state, confidence=0.9, text=output_text + text[cursor:end_of_pi])
    return None

def convert_blank_line_to_pi(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
    """Convert blank braille lines into pi for later use if needed"""
    if text.startswith("\n\n", cursor) or text.startswith("\f\n", cursor):
        return DetectionResult(cursor+1,state, confidence=1.0, text=output_text + "\n<?blank-line?>")
    return None


def create_running_head_detector(min_indent: int) -> Detector:
    """Create a detector for running heads."""
    min_indent_re = re.compile(f"(?P<braille_page_pi><\\?braille-page (?P<brl_page_num>[\u2800-\u28ff]*)\\?>)\u2800{{{min_indent},}}(?P<running_head>[\u2801-\u28ff][\u2800-\u28ff]*)[\n\f]")
    def detect_running_head(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult | None:
        if m := min_indent_re.match(text[cursor:]):
            braille_page_pi, brl_page_num, running_head = (m.group(x) for x in ["braille_page_pi", "brl_page_num", "running_head"])
            prev_braille_page_type = state.get("braille-page-type", BraillePageType.UNSET)
            braille_page_type = BraillePageType.T if brl_page_num.startswith("\u281e") else BraillePageType.P if brl_page_num.startswith("\u280f") else BraillePageType.NORMAL if brl_page_num else prev_braille_page_type
            return DetectionResult(cursor + m.end(), state, 1.0, f"{output_text}{braille_page_pi}<?running-head {running_head}?>")
        return None
    return detect_running_head
