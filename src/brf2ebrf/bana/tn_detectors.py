#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Detectors for transcriber notes according to BANA formats"""
from brf2ebrf.parser import DetectionState


def tn_indicators_block_matcher(brl: str, state: DetectionState) -> (str | None, DetectionState):
    if brl.startswith("\u2808\u2828\u2823") and brl.endswith("\u2808\u2828\u281c"):
        return f"<div class=\"tn\">{brl}</div>", state
    return None, state
