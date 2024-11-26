#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for working with eBraille format."""
from collections.abc import Iterable
from dataclasses import dataclass

import lxml.html
from lxml.html.builder import HTML, HEAD, BODY, ATTR, META, LINK, TITLE, H2, OL, LI, A


def XMLNS(uri: str, prefix=None) -> dict[str, str]:
    name = f"xmlns:{prefix}" if prefix else "xmlns"
    return {name: uri}

def XML_LANG(lang: str) -> dict[str, str]:
    return {"xml:lang": lang}

def EPUB_TYPE(epub_type: str) -> dict[str, str]:
    return {"epub:type": epub_type}

def ARIA_LABEL(label: str) -> dict[str, str]:
    return {"aria-label": label}

NAV = lxml.html.builder.E.nav

@dataclass(frozen=True)
class PageRef:
    href: str
    title: str
    page_num_braille: str

def create_navigation_html(title: str = "-", page_refs: Iterable[PageRef] = (), opf_name: str = "package.opf") -> str:
    root = HTML(
        XMLNS("http://www.w3.org/1999/xhtml"),
        XMLNS("http://www.idpf.org/2007/ops", prefix="epub"),
        XML_LANG("en"),
        ATTR(lang="en"),
        HEAD(
            TITLE(title),
            META(
                charset="UTF-8"
            ),
            LINK(
                rel="publication",
                href=opf_name,
                type="application/oebps-package+xml"
            ),
        ),
        BODY(
            NAV(
                EPUB_TYPE("page-list"),
                ARIA_LABEL("Page list"),
                ATTR(role="doc-pagelist"),
                ATTR(hidden=""),
                H2("⠠⠇⠊⠌ ⠷ ⠏⠁⠛⠑⠎"),
                OL(
                    *[LI(A(ATTR(href=r.href), r.page_num_braille)) for r in page_refs]
                )
            )
        )
    )
    return lxml.html.tostring(root, pretty_print=True, method="xml", doctype="<!DOCTYPE html>")