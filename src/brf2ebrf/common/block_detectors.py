"""Detectors for blocks"""
from brf2ebrf.parser import DetectionState, DetectionResult


def detect_pre(text: str, cursor: int, state: DetectionState, output_text: str) -> DetectionResult:
    """Detects preformatted Braille"""
    brl = ""
    for c in text[cursor:]:
        if ord(c) in range(0x2800, 0x2900):
            brl += c
        else:
            break
    return DetectionResult(cursor + len(brl), state, 0.4, f"{output_text}<pre>{brl}</pre>") if brl else DetectionResult(cursor + 1, state, 0.0, output_text + text[cursor])
