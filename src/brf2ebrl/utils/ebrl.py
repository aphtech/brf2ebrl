#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for working with eBraille format."""
import lxml.html
from lxml.html.builder import HTML, HEAD, BODY, ATTR, META, LINK, TITLE


def XMLNS(uri: str, prefix=None) -> dict[str, str]:
    name = f"xmlns:{prefix}" if prefix else "xmlns"
    return {name: uri}

def XML_LANG(lang: str) -> dict[str, str]:
    return {"xml:lang": lang}

def create_navigation_html(title: str = "-", opf_name: str = "package.opf") -> str:
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
        BODY()
    )
    return lxml.html.tostring(root, pretty_print=True, method="xml", doctype="<!DOCTYPE html>")