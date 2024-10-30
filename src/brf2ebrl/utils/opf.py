#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Utilities for working with OPF"""
from lxml.builder import ElementMaker

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"

_E = ElementMaker(namespace=OPF_NAMESPACE, nsmap={None: OPF_NAMESPACE})
PACKAGE = _E.package
METADATA = _E.metadata
MANIFEST = _E.manifest
ITEM = _E.item
SPINE = _E.spine
ITEMREF = _E.itemref
