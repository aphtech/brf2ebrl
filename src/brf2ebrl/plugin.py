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
from dataclasses import dataclass
from mimetypes import MimeTypes
from typing import Sequence, AnyStr
from xml.etree import ElementTree
from xml.etree.ElementTree import QName, Element
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

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


class Bundler(ABC):
    """Base class for bundlers"""
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    @abstractmethod
    def write_file(self, name: str, filename: str, add_to_spine: bool):
        """Write an existing file to the bundle."""
        pass
    @abstractmethod
    def write_str(self, name: str, data: AnyStr, add_to_spine: bool):
        """Write a file containing the content to the bundle."""
        pass
    def write_image(self, name: str, filename: str):
        """Write an image file to the bundle"""
        self.write_file(name, filename, False)
    def write_volume(self, name: str, data: AnyStr):
        """Write a volume to the bundle."""
        self.write_str(name, data, True)
    @abstractmethod
    def close(self):
        """Close the bundle."""
        pass


_MIMETYPES = MimeTypes()
_OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
_OPF_NAME = "package.opf"
_CONTAINER_XML_template = """<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
    <rootfiles>
        <rootfile full-path="%s" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""

def _create_opf_str() -> bytes:
    root = Element(str(QName(_OPF_NAMESPACE, tag="package")), attrib={str(QName(_OPF_NAMESPACE, tag="version")): "3.0", str(QName(_OPF_NAMESPACE, tag="unique-identifier")): "bookid"})
    metadata = Element(str(QName(_OPF_NAMESPACE, tag="metadata")))
    root.append(metadata)
    manifest = Element(str(QName(_OPF_NAMESPACE, "manifest")))
    root.append(manifest)
    spine = Element(str(QName(_OPF_NAMESPACE, "spine")))
    root.append(spine)
    ElementTree.indent(root)
    return ElementTree.tostring(root, xml_declaration=True, encoding="UTF-8", default_namespace=_OPF_NAMESPACE)

class EBrlZippedBundler(Bundler):
    def __init__(self, name: str):
        self._zipfile = ZipFile(name, 'w', compression=ZIP_DEFLATED)
        self._zipfile.writestr("mimetype", b"application/epub+zip", compress_type=ZIP_STORED)
    def write_file(self, name: str, filename: str, add_to_spine: bool):
        self._zipfile.write(filename, name)
    def write_str(self, name: str, data: AnyStr, add_to_spine: bool):
        self._zipfile.writestr(name, data)
    def write_image(self, name: str, filename: str):
        self.write_file(f"ebraille/{name}", filename, False)
    def write_volume(self, name: str, data: AnyStr):
        self.write_str(f"ebraille/{name}", data, True)
    def close(self):
        try:
            self._zipfile.writestr(_OPF_NAME, _create_opf_str())
            self._zipfile.writestr("META-INF/container.xml", _CONTAINER_XML_template.format(_OPF_NAME))
        finally:
            self._zipfile.close()


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
    @abstractmethod
    def create_bundler(self, output_file: str) -> Bundler:
        """Creates a bundler for bundling the output"""
        pass


class _DelegatingPluginImpl(Plugin):
    def __init__(self, plugin_id: str, name: str, brf_parser_factory, file_mapper, bundler_factory):
        super().__init__(plugin_id, name)
        self._brf_parser_factory = brf_parser_factory
        self._file_mapper = file_mapper
        self._bundler_factory = bundler_factory

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
    def create_bundler(self, output_file: str) -> Bundler:
        return self._bundler_factory(output_file)


def create_plugin(plugin_id: str, name: str, brf_parser_factory,
                  file_mapper=lambda f, i: os.path.basename(f), bundler_factory=lambda x: EBrlZippedBundler(x)) -> Plugin:
    """Create a plugin by providing the information required"""
    return _DelegatingPluginImpl(plugin_id, name, brf_parser_factory=brf_parser_factory, file_mapper=file_mapper, bundler_factory=bundler_factory)
