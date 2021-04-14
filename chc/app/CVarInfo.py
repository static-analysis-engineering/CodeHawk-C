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

from typing import List, TYPE_CHECKING

import chc.app.CDictionaryRecord as CD

if TYPE_CHECKING:
    from chc.app.CDeclarations import CDeclarations


class CVarInfo(CD.CDeclarationsRecord):
    """Global variable.

    tags:
        0: vname
        1: vstorage     ('?' for global variable, 'o_gvid' for opaque variable)

    args:
        0: vid          (-1 for global variable)
        1: vtype
        2: vattr        (-1 for global variable) (TODO: add global attributes)
        3: vglob
        4: vinline
        5: vdecl        (-1 for global variable) (TODO: add global locations)
        6: vaddrof
        7: vparam
        8: vinit        (optional)
    """

    def __init__(
        self,
        cdecls: "CDeclarations",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDeclarationsRecord.__init__(self, cdecls, index, tags, args)
        self.vname = tags[0]
        self.vtype = self.get_dictionary().get_typ(args[1])
        self.vglob = args[3] == 1
        self.vinline = args[4] == 1
        self.vdecl = (
            self.decls.get_location(self.args[5]) if not (self.args[5] == -1) else None
        )
        self.vaddrof = args[6] == 1
        self.vparam = args[7]
        self.vinit = (
            self.decls.get_initinfo(self.args[8]) if len(self.args) == 9 else None
        )

    def get_vid(self) -> int:
        vid = self.args[0]
        return vid if vid >= 0 else self.index

    def get_real_vid(self) -> int:
        return self.args[0]

    def get_vstorage(self):
        if len(self.tags) > 1:
            return self.tags[1]
        vid = self.get_vid()
        if vid in self.decls.varinfo_storage_classes:
            return self.decls.varinfo_storage_classes[vid]
        return "n"

    def get_initializer(self):
        return self.vinit

    def has_initializer(self):
        return self.vinit is not None

    def get_line(self):
        return self.vdecl.get_line()

    def __str__(self) -> str:
        return (
            self.vname
            + ":"
            + str(self.vtype)
            + "  "
            + str(self.vdecl)
            + " ("
            + str(self.args[0])
            + ")"
        )
