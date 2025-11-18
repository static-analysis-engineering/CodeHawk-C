# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
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
"""Definition of a struct/union."""

from typing import cast, List, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDeclarationsRecord

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CAttributes import CAttributes
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CFieldInfo import CFieldInfo
    from chc.app.CGlobalDeclarations import CGlobalDeclarations
    from chc.app.CVisitor import CVisitor


class CCompInfo(CDeclarationsRecord):
    """Struct/union definition.

    * tags[0]: cname                 ('?' for global struct)

    * args[0]: ckey                  (-1 for global struct)
    * args[1]: isstruct
    * args[2]: iattr                 (-1 for global struct)
    * args[3..]: field indices
    """

    def __init__(
        self, decls: "CDeclarations", ixval: IT.IndexedTableValue
    ) -> None:
        CDeclarationsRecord.__init__(self, decls, ixval)

    @property
    def fields(self) -> List["CFieldInfo"]:
        return [self.decls.get_fieldinfo(i) for i in self.args[3:]]

    @property
    def fieldcount(self) -> int:
        return len(self.fields)

    @property
    def fieldnames(self) -> List[str]:
        return [f.fname for f in self.fields]

    @property
    def is_struct(self) -> bool:
        return self.args[1] == 1

    @property
    def cattr(self) -> "CAttributes":
        return self.dictionary.get_attributes(self.args[2])

    @property
    def ckey(self) -> int:
        ckey = int(self.args[0])
        return ckey if ckey >= 0 else self.index

    @property
    def size(self) -> int:
        return sum([f.size for f in self.fields])

    @property
    def name(self) -> str:
        if self.tags[0] == "?":
            name = list(
                cast("CGlobalDeclarations",
                     self.decls).compinfo_names[self.ckey])[0]
        else:
            name = self.tags[0]
        return name

    @property
    def field_strings(self) -> str:
        return ":".join([f.fname for f in self.fields])

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_compinfo(self)

    def __str__(self) -> str:
        lines = []
        lines.append("struct " + self.name)
        offset = 0
        for f in self.fields:
            lines.append((" " * 25) + str(offset).rjust(4) + "  " + str(f))
            offset += f.size
        return "\n".join(lines)
