# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
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

if TYPE_CHECKING:
    from chc.app.CFileDeclarations import CFileDeclarations


class CEnumInfo(CDeclarationsRecord):
    """Global enum definition."""

    def __init__(self, decls: "CFileDeclarations", index: int, tags: List[str], args: List[int]):
        CDeclarationsRecord.__init__(self, decls, index, tags, args)
        self.ename = self.tags[0]
        self.ikind = self.tags[1]
        self.eattr = self.get_dictionary().get_attributes(args[0])
        self.eitems = [cast("CFileDeclarations", self.decls).get_enumitem(i) for i in self.args[1:]]

    def __str__(self) -> str:
        return self.ename + " (" + str(len(self.eitems)) + " items)"
