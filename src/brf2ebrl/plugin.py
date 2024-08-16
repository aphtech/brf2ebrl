#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Module used when defining a plugin."""
import importlib
import os
import pkgutil
from abc import abstractmethod, ABC
from typing import Sequence

from brf2ebrl.common import PageLayout
from brf2ebrl.parser import Parser


def find_plugins():
    return {
        k: v.PLUGIN
        for k, v in {
            name: importlib.import_module(name)
            for finder, name, ispkg in pkgutil.iter_modules()
            if name.startswith("brf2ebrl_")
        }.items()
        if hasattr(v, "PLUGIN") and isinstance(v.PLUGIN, Plugin)
    }


class Plugin(ABC):
    """Base class for plugins to convert a BRF to eBraille."""

    def __init__(self, plugin_id: str, name: str):
        self._id = plugin_id
        self._name = name

    @property
    def id(self) -> str:
        """A unique identifier for the plugin"""
        return self._id

    @property
    def name(self) -> str:
        """A name which will be displayed to users"""
        return self._name

    @abstractmethod
    def create_brf_parser(
            self,
            page_layout: PageLayout = PageLayout(),
            brf_path: str = "",
            output_path: str = "",
            images_path: str = "",
            detect_running_heads: bool = True,
            *args,
            **kwargs
    ) -> Sequence[Parser]:
        """Create the parser for converting BRFs into another format"""
        return []

    @abstractmethod
    def file_mapper(self, input_file: str, index: int, *args, **kwargs) -> str:
        """Maps the input file name to the output file name."""
        return os.path.basename(input_file)


class _DelegatingPluginImpl(Plugin):
    def __init__(self, plugin_id: str, name: str, brf_parser_factory, file_mapper):
        super().__init__(plugin_id, name)
        self._brf_parser_factory = brf_parser_factory
        self._file_mapper = file_mapper

    def create_brf_parser(
            self,
            page_layout: PageLayout = PageLayout(),
            brf_path: str = "",
            output_path: str = "",
            images_path: str = "",
            detect_running_heads: bool = True,
            *args,
            **kwargs
    ) -> Sequence[Parser]:
        return self._brf_parser_factory(page_layout=page_layout, brf_path=brf_path, output_path=output_path,
                                        images_path=images_path, detect_running_heads=detect_running_heads, *args,
                                        **kwargs)

    def file_mapper(self, input_file: str, index: int, *args, **kwargs) -> str:
        return self._file_mapper(input_file=input_file, index=index, *args, **kwargs)


def create_plugin(plugin_id: str, name: str, brf_parser_factory,
                  file_mapper=lambda f, i: os.path.basename(f)) -> Plugin:
    """Create a plugin by providing the information required"""
    return _DelegatingPluginImpl(plugin_id, name, brf_parser_factory=brf_parser_factory, file_mapper=file_mapper)
