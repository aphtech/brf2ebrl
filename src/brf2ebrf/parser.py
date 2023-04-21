from dataclasses import dataclass

@dataclass
class DetectionResult:
    text: str
    cursor: int
    state: str
    confidence: float
