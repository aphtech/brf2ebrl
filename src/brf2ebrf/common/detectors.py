"""Some detectors common t multiple Braille codes/standards."""
import re

from brf2ebrf.parser import DetectionResult, DetectionState

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)


def convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Convert the entire BRF into unicode Braille in a single step."""
    return DetectionResult(len(text), state, 1.0, output_text + text[cursor:].translate(_ASCII_TO_UNICODE_DICT))


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Convert oly th next character to unicode Braille."""
    return DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor].translate(_ASCII_TO_UNICODE_DICT))


def detect_and_pass_processing_instructions(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Detect and pass through processing instructions"""
    if text.startswith("<?", cursor):
        end_of_pi = text.find("?>", cursor) + 2
        if end_of_pi >= 4:
            return DetectionResult(end_of_pi, state, confidence=0.9, text=output_text + text[cursor:end_of_pi])
    return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])

def convert_blank_line_to_pi(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Convert blank braille lines into pi for later use if needed"""
    if text.startswith("\n\n", cursor) or text.startswith("\f\n", cursor):
        return DetectionResult(cursor+1,state, confidence=1.0, text=output_text + "\n<?blank-line?>")
    return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])

def convert_unknown_to_pre(
    text: str, cursor: int, state: DetectionState, output_text: str
) -> DetectionResult:
    """Create pre sections out of undetected blocks"""
    result = re.search("\n|<.*?>.*?</.*?>|<\?.*?\?>|<.*?/>|$",text[cursor:])
    if result != None  :
        pre=""
        if text[cursor:cursor+result.start()]:
            pre=f"<pre>{text[cursor:cursor+result.start()]}</pre>"
        return DetectionResult(cursor+result.end(), state, confidence=0.4, text=f"{output_text}{pre}{result.group()}")
    return DetectionResult(cursor+1, state, confidence=0.0, text=output_text + text[cursor])
