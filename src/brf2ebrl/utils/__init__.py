#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Useful utility functions"""
import re
from collections.abc import Iterable
from importlib.resources.abc import Traversable

_TAG_NAME_PATTERN = "[_a-zA-Z][-_.a-zA-Z0-9]*"
_ELEMENT_TAG_RE = re.compile(
    f"(<(?P<start_tag_name>{_TAG_NAME_PATTERN})\\s*(/>)?)|(</(?P<end_tag_name>{_TAG_NAME_PATTERN})>)")


def find_end_of_element(text: str, start: int = 0) -> int:
    """Finds the index of the end of the element or -1 if not found."""
    cursor = start
    tags = []
    while m := _ELEMENT_TAG_RE.search(text, cursor):
        cursor = m.end()
        if m.group().endswith("/>"):
            continue
        else:
            if m.group().startswith("</"):
                if len(tags) == 0 or tags.pop() != m.group("end_tag_name"):
                    cursor = -1
                    tags.clear()
            else:
                tags.append(m.group("start_tag_name"))
        if len(tags) == 0:
            break
    return cursor if len(tags) == 0 else -1

def list_sub_paths(path: Traversable) -> Iterable[tuple[list[str], Traversable]]:
    return [([path.name], path)] if not path.is_dir() else [([path.name] + l, p) for i in path.iterdir() for l, p in list_sub_paths(i)]