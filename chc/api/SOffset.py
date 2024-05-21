# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2023 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
"""Object representation of sumtype s_offset_t."""

from typing import Dict, List, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

from chc.api.InterfaceDictionaryRecord import (
    InterfaceDictionaryRecord, ifdregistry)

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.ApiParameter import ApiParameter


class SOffset(InterfaceDictionaryRecord):
    """Base class for s_term offset."""

    def __init__(
        self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, ifd, ixval)

    @property
    def is_nooffset(self) -> bool:
        return False

    @property
    def is_field(self) -> bool:
        return False

    @property
    def is_index(self) -> bool:
        return False

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        raise Exception("Should be implemented by a subclass")

    def __str__(self) -> str:
        return "s-offset-" + self.tags[0]


@ifdregistry.register_tag("no", SOffset)
class STArgNoOffset(SOffset):
    """No Offset."""

    def __init__(
        self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        SOffset.__init__(self, ifd, ixval)

    @property
    def is_no_offset(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        return None

    def __str__(self) -> str:
        return ""


@ifdregistry.register_tag("fo", SOffset)
class STArgFieldOffset(SOffset):
    """Field offset in an s_term.

    tags[1]: field name
    args[0]: index of sub-offset in interface dictionary
    """

    def __init__(
        self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        SOffset.__init__(self, ifd, ixval)

    @property
    def field(self) -> str:
        return self.tags[1]

    @property
    def offset(self) -> SOffset:
        return self.ifd.get_s_offset(int(self.args[0]))

    @property
    def is_field(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        fnode = ET.Element("field")
        fnode.set("name", self.field)
        offnode = self.offset.get_mathml_node(signature)
        if offnode is not None:
            fnode.append(offnode)
        return fnode

    def __str__(self) -> str:
        return "." + self.field + str(self.offset)


@ifdregistry.register_tag("io", SOffset)
class STArgIndexOffset(SOffset):
    """Index offset in an s_term.

    tags[1]: array index in string form
    args[0]: index of sub-offset in interface dictionary
    """

    def __init__(
        self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        SOffset.__init__(self, cd, ixval)

    @property
    def index(self) -> int:
        return int(self.tags[1])

    @property
    def offset(self) -> SOffset:
        return self.ifd.get_s_offset(int(self.args[0]))

    @property
    def is_index(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        inode = ET.Element("index")
        inode.set("i", str(self.index))
        offnode = self.offset.get_mathml_node(signature)
        if offnode is not None:
            inode.append(offnode)
        return inode

    def __str__(self) -> str:
        return "[" + str(self.index) + "]" + str(self.offset)
