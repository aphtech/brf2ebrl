#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from brf2ebrl.common.selectors import most_confident_detector
from brf2ebrl.parser import DetectionResult


def test_select_most_confident_detector():
    detectors = [lambda text, cursor, state, output_text: DetectionResult(cursor + 4, state, 0.2, output_text + "d"), lambda text, cursor, state, output_text: DetectionResult(cursor + 1, state, 0.9, output_text + "a"), lambda text, cursor, state, output_text: DetectionResult(cursor + 2, state, 0.6, output_text + "b"), lambda text, cursor, state, output_text: DetectionResult(cursor + 3, state, 0.3, output_text + "c")]
    assert most_confident_detector("TEST BRF", 0, {}, "", detectors) == DetectionResult(1, {}, 0.9, "a")