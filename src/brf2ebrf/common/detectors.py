"""Some detectors common t multiple Braille codes/standards."""
import re
from brf2ebrf.parser import DetectionResult

_ASCII_TO_UNICODE_DICT = str.maketrans(
    r""" A1B'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\0Z7(_?W]#Y)=""",
    "".join([chr(x) for x in range(0x2800, 0x2840)])
)


def convert_ascii_to_unicode_braille_bulk(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    """Convert the entire BRF into unicode Braille in a single step."""
    return DetectionResult(len(text), state, 1.0, output_text + text[cursor:].translate(_ASCII_TO_UNICODE_DICT))


def convert_ascii_to_unicode_braille(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    """Convert oly th next character to unicode Braille."""
    return DetectionResult(cursor + 1, state, 1.0, output_text + text[cursor].translate(_ASCII_TO_UNICODE_DICT))


def detect_and_pass_processing_instructions(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    """Detect and pass through processing instructions"""

    if text.startswith("<?", cursor):
        end_of_pi = text.find("?>", cursor) + 2
        if end_of_pi >= 4:
            return DetectionResult(end_of_pi, state, confidence=0.9, text=output_text + text[cursor:end_of_pi])
    return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])

def convert_blank_line_to_pi(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    """Convert blank braille lines into pi for later use if needed"""
    if cursor == 0 and  text[cursor]=="\n":
        return DetectionResult(cursor+1,state, confidence=1.0, text=output_text + "<?blank-line?>")
    if text.startswith("\n\n", cursor) or text.startswith("\f\n", cursor):
        return DetectionResult(cursor+1,state, confidence=1.0, text=output_text + "<?blank-line?>")
    return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])

def detect_and_pass_XML(text: str, cursor: int, state: str, output_text: str) -> DetectionResult:
    """Detect and pass through pre-processed xml for use with pre pass"""

    #singlton
    result = re.search("<.*?>", text[cursor:])
    if result  and result.group().endswith("/>") or result  and result.group().endswith("?>"):
        return DetectionResult(cursor+result.end(), state, confidence=0.9, text=output_text + text[cursor:cursor+result.end()])
    xml_nodes =[]        
    start_tag = re.search("<.*?>",text[cursor:])
    if start_tag and start_tag.start()==0:
        search_cursor = cursor+start_tag.end()
        end_tag= re.search("<.*?>",text[search_cursor:])
        if end_tag is None:
            return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])
        if end_tag.group().startswith("</"):
            return DetectionResult(cursor+start_tag.end()+end_tag.end(), state, confidence=0.9, text=output_text + text[cursor:cursor+start_tag.end()+end_tag.end()])
        end_cursor = cursor + start_tag.end()
        xml_nodes.append(start_tag)
        tag=True
        while  tag and xml_nodes:
            tag= re.search("<.*?>",text[end_cursor:])
            if tag is None:
                continue
            #singlton
            if tag.group().startswith("</"):
                xml_nodes.pop()
            else:
                if not tag.group().endswith("/>") and  not tag.group().endswith("?>"):
                    xml_nodes.append(tag)
            end_cursor  += tag.end()
        if not xml_nodes:
            return DetectionResult(end_cursor, state, confidence=0.9, text=output_text + text[cursor:end_cursor])
    return DetectionResult(cursor + 1, state, confidence=0.0, text=output_text + text[cursor])

        
def convert_unknown_to_pre(
    text: str, cursor: int, state: str, output_text: str
) -> DetectionResult:
    """Converts all non-consumed elements and wraps them in pre tags"""
    result = re.search("\n|<|$",text[cursor:])
    if result:
        return DetectionResult(cursor+result.start(), state, confidence=0.4, text=f"{output_text}<pre>{text[cursor:cursor+result.start()]}</pre>")
    return DetectionResult(cursor+1, state, confidence=0.0, text=output_text + text[cursor])
