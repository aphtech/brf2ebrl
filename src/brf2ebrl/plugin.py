#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Module used when defining a plugin."""
from abc import abstractmethod, ABC
from typing import Sequence

from brf2ebrl.common import PageLayout
from brf2ebrl.parser import Parser


class Brf2EbrlPlugin(ABC):
    """Base class for plugins to convert a BRF to eBraille."""

    def __init__(self, plugin_id: str, name: str):
        self._id = plugin_id
        self._name = name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def create_brf2ebrl_parser(
            self,
            page_layout: PageLayout = PageLayout(),
            brf_path: str = "",
            output_path: str = "",
            images_path: str = "",
            detect_running_heads: bool = True,
            *args,
            **kwargs
    ) -> Sequence[Parser]:
        return []


class _Brf2EbrlPluginImpl(Brf2EbrlPlugin):
    def __init__(self, plugin_id: str, name: str, brf2ebrl_parser_factory):
        super().__init__(plugin_id, name)
        self._brf2ebrl_parser_factory = brf2ebrl_parser_factory

    def create_brf2ebrl_parser(
            self,
            page_layout: PageLayout = PageLayout(),
            brf_path: str = "",
            output_path: str = "",
            images_path: str = "",
            detect_running_heads: bool = True,
            *args,
            **kwargs
    ) -> Sequence[Parser]:
        return self._brf2ebrl_parser_factory(page_layout=page_layout, brf_path=brf_path, output_path=output_path,
                                             images_path=images_path, detect_running_heads=detect_running_heads, *args,
                                             **kwargs)


def create_brf2ebrl_plugin(plugin_id: str, name: str, brf2ebrl_parser_factory) -> Brf2EbrlPlugin:
    return _Brf2EbrlPluginImpl(plugin_id, name, brf2ebrl_parser_factory=brf2ebrl_parser_factory)
