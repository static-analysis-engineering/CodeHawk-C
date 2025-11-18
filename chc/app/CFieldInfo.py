# ------------------------------------------------------------------------------
# CodeHawk C Analyze
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2025 Aarno Labs LLC
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
"""Type and layout of a struct or union field."""

from typing import cast, List, Optional, TYPE_CHECKING

import chc.util.IndexedTable as IT

from chc.app.CDictionaryRecord import CDeclarationsRecord

if TYPE_CHECKING:
    from chc.app.CAttributes import CAttributes
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CLocation import CLocation
    from chc.app.CTyp import CTyp
    from chc.app.CVisitor import CVisitor


class CFieldInfo(CDeclarationsRecord):
    """Definition of a struct field.

    * tags[0] fname

    * args[0]: fcomp.ckey  (-1 for global structs)
    * args[1]: ftype
    * args[2]: fbitfield
    * args[3]: fattr       (-1 for global structs)
    * args[4]: floc        (-1 for global structs)
    """

    def __init__(
            self, cdecls: "CDeclarations", ixval: IT.IndexedTableValue) -> None:
        CDeclarationsRecord.__init__(self, cdecls, ixval)

    @property
    def fname(self) -> str:
        return self.tags[0]

    @property
    def ftype(self) -> "CTyp":
        return self.dictionary.get_typ(self.args[1])

    @property
    def bitfield(self) -> int:
        return self.args[2]

    @property
    def size(self) -> int:
        return self.ftype.size

    @property
    def location(self) -> Optional["CLocation"]:
        if self.args[4] >= 0:
            return cast(
                "CFileDeclarations", self.decls).get_location(self.args[4])
        return None

    @property
    def attributes(self) -> Optional["CAttributes"]:
        if self.args[3] >= 0:
            return self.dictionary.get_attributes(self.args[3])
        return None

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_fieldinfo(self)

    def __str__(self) -> str:
        return self.fname + ":" + str(self.ftype)
