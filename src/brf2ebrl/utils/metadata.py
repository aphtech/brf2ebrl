#  Copyright (c) 2025. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Classes for metadata in eBraille"""
import datetime
from typing import Any, Callable, Iterable
from uuid import uuid4

from lxml.etree import Element

from brf2ebrl.utils.opf import TITLE, IDENTIFIER, DATE, CREATOR, LANGUAGE, BRAILLE_SYSTEM, A11Y_PRODUCER, \
    DATE_TRANSCRIBED, DATE_COPYRIGHTED


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
    def __init__(self, value: Any="-"):
        super().__init__("Title", value, TITLE)

class Identifier(MetadataItem):
    def __init__(self, value: Any=None):
        super().__init__("Identifier", value if value else str(uuid4()), IDENTIFIER)

class AbstractDate(MetadataItem):
    def __init__(self, name: str, value: Any, to_xml_func: Callable[[Any], Element]):
        super().__init__(name, value if value else datetime.date.today(), lambda x: to_xml_func(self.value_to_str(x)))
    def value_to_str(self, value: Any) -> str:
        match value:
            case datetime.date:
                return value.isoformat()
            case _:
                return str(value)

class Date(AbstractDate):
    def __init__(self, value: Any=None):
        super().__init__("Date", value, DATE)

class DateCopyrighted(AbstractDate):
    def __init__(self, value: Any=datetime.datetime.fromtimestamp(0)):
        super().__init__("Copyrighted", value, DATE_COPYRIGHTED)

class DateTranscribed(AbstractDate):
    def __init__(self, value: Any=datetime.datetime.fromtimestamp(0)):
        super().__init__("Transcribed", value, DATE_TRANSCRIBED)

class Creator(MetadataItem):
    def __init__(self, value: Any="-"):
        super().__init__("Creator", value, CREATOR)

class Language(MetadataItem):
    def __init__(self, value: Any = "en-Brai"):
        super().__init__("Language", value, LANGUAGE)

class BrailleSystem(MetadataItem):
    def __init__(self, value: str="UEB"):
        super().__init__("Braille system",  value, BRAILLE_SYSTEM)

class Producer(MetadataItem):
    def __init__(self, value: str="-"):
        super().__init__("Producer", value, A11Y_PRODUCER)

DEFAULT_METADATA = [
    Creator(),
    Identifier(),
    Language(),
    Title(),
    DateCopyrighted(),
    DateTranscribed(),
    BrailleSystem(),
    Producer()
]

def ensure_default_metadata(data: Iterable[MetadataItem]) -> Iterable[MetadataItem]:
    return list(data) + [d for d in DEFAULT_METADATA if not any(isinstance(v, type(d)) for v in data)]
