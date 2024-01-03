#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from brf2ebrf.common.detectors import convert_blank_line_to_pi
from brf2ebrf.parser import DetectionResult


def test_convert_blank_line_to_pi():
    brf = "TE/ TEXT\n\n"
    expected_brf = "TE/ TEXT\n<?blank-line?>"
    actual = convert_blank_line_to_pi(brf, 8, {}, "TE/ TEXT")
    expected = DetectionResult(10, {}, 1.0, expected_brf)
    assert actual == expected
