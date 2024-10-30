#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for working with OPF"""
from lxml.builder import ElementMaker

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"

_OPF = ElementMaker(namespace=OPF_NAMESPACE, nsmap={None: OPF_NAMESPACE, "dc": DC_NAMESPACE})
_DC = ElementMaker(namespace=DC_NAMESPACE, nsmap={None: OPF_NAMESPACE, "dc": DC_NAMESPACE})
PACKAGE = _OPF.package
METADATA = _OPF.metadata
CREATOR = _DC.creator
FORMAT = _DC.format
MANIFEST = _OPF.manifest
ITEM = _OPF.item
SPINE = _OPF.spine
ITEMREF = _OPF.itemref
