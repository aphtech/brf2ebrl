import json
from brf2ebrf.parser import DetectionResult


class PageDetector:
    def __call__(self, text: str, cursor: int, state: str, cells_per_line: int = 40, lines_per_page: int = 25) -> DetectionResult:
        if state == "StartBraillePage":
            end_of_page = text.find("\f", cursor)
            if end_of_page < 0:
                end_of_page = len(text)
            page_cmd = json.dumps({"BraillePage": {}})
            output = f"\ue000{page_cmd}\ue001{text[cursor:end_of_page]}"
            return DetectionResult(text=output, cursor=min(end_of_page + 1, len(text)), state=state, confidence=1.0)
        return DetectionResult("", cursor, state, 0.0)
