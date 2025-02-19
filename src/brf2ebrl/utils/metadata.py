#  Copyright (c) 2025. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Classes for metadata in eBraille"""
import datetime
from typing import Any, Callable
from uuid import uuid4

from lxml.etree import Element

from brf2ebrl.utils.opf import TITLE, IDENTIFIER, DATE, CREATOR, FORMAT, LANGUAGE


class MetadataItem:
    def __init__(self, name: str, value: Any, xml_func: Callable[[Any], Element]):
        self._name = name
        self._value = value
        self._xml_func = xml_func
    @property
    def name(self) -> str:
        return self._name
    @property
    def value(self) -> Any:
        return self._value
    @value.setter
    def value(self, new_value: Any):
        self._value = new_value
    def to_xml(self) -> Element:
        return self._xml_func(self.value)

class Title(MetadataItem):
    def __init__(self, value: Any):
        super().__init__("Title", value, TITLE)

class Identifier(MetadataItem):
    def __init__(self, value: Any):
        super().__init__("Identifier", value, IDENTIFIER)

def _date_value_to_xml(value: Any) -> Element:
    match value:
        case datetime.date:
            return DATE(value.isoformat())
        case _:
            return DATE(str(value))

class Date(MetadataItem):
    def __init__(self, value: Any):
        super().__init__("Date", value, _date_value_to_xml)

class Creator(MetadataItem):
    def __init__(self, value: Any):
        super().__init__("Creator", value, CREATOR)

class Format(MetadataItem):
    def __init__(self, value: Any = "eBraille 1.0"):
        super().__init__("Format", value, FORMAT)

class Language(MetadataItem):
    def __init__(self, value: Any = "en-Brai"):
        super().__init__("Language", value, LANGUAGE)

DEFAULT_METADATA = [Creator("-"),
          Format("eBraille 1.0"),
          Date(datetime.date.today().isoformat()),
          Identifier(str(uuid4())),
          Language("en-Brai"),
          Title("-")]