from brf2ebrf.parser import DetectionResult

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)



def convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    return DetectionResult(len(text), state, 1.0, output_text + text[cursor:].translate(_ASCII_TO_UNICODE_DICT))


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    return DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor].translate(_ASCII_TO_UNICODE_DICT))