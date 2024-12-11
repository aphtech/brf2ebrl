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
from collections import Counter, deque
from dataclasses import dataclass
from datetime import date, datetime, UTC
from mimetypes import MimeTypes
from pathlib import Path
from typing import Sequence, AnyStr
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

import lxml.html
from lxml import etree
from lxml.builder import ElementMaker

from brf2ebrl.common import PageLayout
from brf2ebrl.parser import Parser
from brf2ebrl.utils.ebrl import create_navigation_html, PageRef, HeadingRef
from brf2ebrl.utils.opf import PACKAGE, METADATA, MANIFEST, SPINE, ITEM, ITEMREF, CREATOR, FORMAT, DATE, IDENTIFIER, \
    LANGUAGE, TITLE, META

_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


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
_OPF_NAME = "package.opf"


def _create_container_xml(opf_name: str):
    e = ElementMaker(namespace="urn:oasis:names:tc:opendocument:xmlns:container", nsmap={None: "urn:oasis:names:tc:opendocument:xmlns:container"})
    container = e.container({"version": "1.0"},
        e.rootfiles(
            e.rootfile({"full-path": opf_name, "media-type": "application/oebps-package+xml"})
        )
    )
    return etree.tostring(container, xml_declaration=True, encoding="UTF-8", pretty_print=True)

@dataclass(frozen=True)
class OpfFileEntry:
    media_type: str
    in_spine: bool
    tactile_graphic: bool = False
    is_nav_document: bool = False

def _create_opf_str(file_entries: dict[str, OpfFileEntry]) -> bytes:
    files_list = [(f"file{i}", n, d.media_type, d.in_spine, d.is_nav_document) for i,(n,(d)) in enumerate(file_entries.items())]
    graphic_types = " ".join(sorted(Counter(_MIMETYPES.guess_extension(d.media_type)[1:] for n,d in file_entries.items() if d.tactile_graphic), key=lambda item: item[1], reverse=True))
    opf = PACKAGE(
        {"unique-identifier": "bookid", "version": "3.0"},
        METADATA(
            CREATOR("-"),
            FORMAT("eBraille 1.0"),
            DATE(date.today().isoformat()),
            IDENTIFIER(str(uuid4())),
            LANGUAGE("en-Brai"),
            TITLE("-"),
            META({"property": "dcterms:dateCopyrighted"}, date.fromtimestamp(0).isoformat()),
            META({"property": "dcterms:modified"}, datetime.now(UTC).strftime("%Y-%m-%dT%H:%M%SZ")),
            META({"property": "a11y:brailleSystem"}, "UEB"),
            META({"property": "a11y:cellType"}, "6"),
            META({"property": "a11y:completeTranscription"}, "true"),
            META({"property": "a11y:dateTranscribed"}, date.fromtimestamp(0).isoformat()),
            META({"property": "a11y:producer"}, "-"),
            *([META({"property": "a11y:tactileGraphics"}, "false")] if not graphic_types else [META({"property": "a11y:tactileGraphics"}, "true"), META({"property": "a11y:graphicType"}, graphic_types)])
        ),
        MANIFEST(*[ITEM({"id": i, "href": n, "media-type": t, **({"properties": "nav"} if nav else {})}) for i,n,t,_,nav in files_list]),
        SPINE(*[ITEMREF({"idref": i}) for i,_,_,s,_ in files_list if s])
    )
    return etree.tostring(opf, xml_declaration=True, pretty_print=True, encoding="UTF-8")


class EBrlZippedBundler(Bundler):
    def __init__(self, name: str):
        self._files: dict[str, OpfFileEntry] = {}
        self._zipfile = ZipFile(name, 'w', compression=ZIP_DEFLATED)
        self._zipfile.writestr("mimetype", b"application/epub+zip", compress_type=ZIP_STORED)
    def _create_navigation_html(self, opf_name: str) -> str:
        page_refs = []
        headings = deque()
        vols = [k for k,v in self._files.items() if v.in_spine]
        detected_title = None
        for vol_name in vols:
            with self._zipfile.open(vol_name) as f:
                root = lxml.html.parse(f, parser=lxml.html.xhtml_parser).getroot()
                if detected_title is None:
                    detected_title = next((x.text_content for x in root.body.iter(tag=["li", *_HEADING_TAGS, "p"])), "")
                for element in root.iter():
                    if element.tag in _HEADING_TAGS:
                        heading_id = element.get("id")
                        headings.append(
                            HeadingRef(href=f"{vol_name}#{heading_id}", heading_braille=element.text_content, level=(
                                    _HEADING_TAGS.index(element.tag) + 1)))
                    elif element.tag == "span" and element.get("role") == "doc-pagebreak":
                        page_id = element.get("id")
                        page_refs.append(
                            PageRef(href=f"{vol_name}#{page_id}", page_num_braille=element.text_content(), title=""))
        return create_navigation_html(opf_name=opf_name, page_refs=page_refs, heading_refs=headings, braille_title=detected_title)
    def _add_to_files(self, name, add_to_spine, tactile_graphic: bool, is_nav_document: bool, media_type: str|None = None):
        def get_media_type():
            yield media_type
            yield _MIMETYPES.guess_type(name)[0]
            yield "application/octet-stream"
        media_type = next(m for m in get_media_type() if m is not None)
        self._files[name] = OpfFileEntry(media_type=media_type,
                                         in_spine=add_to_spine, tactile_graphic=tactile_graphic, is_nav_document=is_nav_document)
    def write_file(self, name: str, filename: str, add_to_spine: bool, tactile_graphic: bool = False, is_nav_document: bool = False, media_type: str|None = None):
        arch_name = Path(name).as_posix()
        self._zipfile.write(filename, arch_name)
        self._add_to_files(arch_name, add_to_spine, tactile_graphic=tactile_graphic, is_nav_document=is_nav_document, media_type=media_type)
    def write_str(self, name: str, data: AnyStr, add_to_spine: bool, tactile_graphic: bool = False, is_nav_document: bool = False, media_type: str|None = None):
        arch_name = Path(name).as_posix()
        self._zipfile.writestr(arch_name, data)
        self._add_to_files(arch_name, add_to_spine, tactile_graphic, is_nav_document=is_nav_document, media_type=media_type)
    def write_image(self, name: str, filename: str):
        self.write_file(f"ebraille/{name}", filename, False, tactile_graphic=True)
    def write_volume(self, name: str, data: AnyStr):
        self.write_str(f"ebraille/{name}", data, True, media_type="application/xhtml+xml")
    def close(self):
        try:
            self.write_str("index.html", self._create_navigation_html(_OPF_NAME), True, is_nav_document=True, media_type="application/xhtml+xml")
            self._zipfile.writestr(_OPF_NAME, _create_opf_str(self._files))
            self._zipfile.writestr("META-INF/container.xml", _create_container_xml(_OPF_NAME))
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
