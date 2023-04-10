# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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

from typing import cast, List, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDeclarationsRecord

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CAttributes import CAttributes
    from chc.app.CEnumItem import CEnumItem
    from chc.app.CFileDeclarations import CFileDeclarations


class CEnumInfo(CDeclarationsRecord):
    """Global enum definition."""

    def __init__(self, decls: "CFileDeclarations", ixval: IT.IndexedTableValue):
        CDeclarationsRecord.__init__(self, decls, ixval)

    @property
    def ename(self) -> str:
        return self.tags[0]

    @property
    def ikind(self) -> str:
        return self.tags[1]

    @property
    def eattr(self) -> "CAttributes":
        return self.dictionary.get_attributes(self.args[0])

    @property
    def eitems(self) -> List["CEnumItem"]:
        decls = cast("CFileDeclarations", self.decls)
        return [decls.get_enumitem(i) for i in self.args[1:]]

    def __str__(self) -> str:
        return self.ename + " (" + str(len(self.eitems)) + " items)"
