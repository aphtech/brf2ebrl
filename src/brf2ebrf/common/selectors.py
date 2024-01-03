#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Some common selectors for brf2ebrf."""
from collections.abc import Iterable

from brf2ebrf.parser import Detector, DetectionResult, DetectionState


def most_confident_detector(text: str, cursor: int, state: DetectionState, output_text: str,
                            detectors: Iterable[Detector]) -> DetectionResult:
    """Selects the detector reporting the highest confidence level."""
    return max(filter(lambda x: x is not None, map(lambda x: x(text, cursor, state, output_text), detectors)), key=lambda d: d.confidence, default=DetectionResult(cursor + 1, state, 0.0, output_text + text[cursor]))
