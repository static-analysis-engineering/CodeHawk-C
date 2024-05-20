# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs
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
"""Variable definition."""

from typing import cast, List, Optional, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, CDeclarationsRecord

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CInitInfo import CInitInfo
    from chc.app.CLocation import CLocation
    from chc.app.CTyp import CTyp


class CVarInfo(CDeclarationsRecord):
    """Local or global variable.

    * tags[0]: vname
    * tags[1]: vstorage  ('?' for global variable, 'o_gvid' for opaque variable)

    * args[0]: vid       (-1 for global variable)
    * args[1]: vtype
    * args[2]: vattr     (-1 for global variable) (TODO: add global attributes)
    * args[3]: vglob
    * args[4]: vinline
    * args[5]: vdecl     (-1 for global variable) (TODO: add global locations)
    * args[6]: vaddrof
    * args[7]: vparam
    * args[8]: vinit     (optional)

    """

    def __init__(self, cdecls: "CDeclarations", ixval: IT.IndexedTableValue
    ) -> None:
        CDeclarationsRecord.__init__(self, cdecls, ixval)

    @property
    def vname(self) -> str:
        return self.tags[0]

    @property
    def vtype(self) -> "CTyp":
        return self.dictionary.get_typ(self.args[1])

    @property
    def is_global(self) -> bool:
        return self.vglob

    @property
    def vglob(self) -> bool:
        return self.args[3] == 1

    @property
    def is_inline(self) -> bool:
        return self.vinline

    @property
    def vinline(self) -> bool:
        return self.args[4] == 1

    @property
    def vdecl(self) -> Optional["CLocation"]:
        if self.args[5] >= 0:
            return self.decls.get_location(self.args[5])
        else:
            return None

    @property
    def vaddrof(self) -> bool:
        return self.args[6] == 1

    @property
    def vparam(self) -> int:
        return self.args[7]

    @property
    def is_param(self) -> bool:
        return self.args[7] > 0

    @property
    def vinit(self) -> Optional["CInitInfo"]:
        if len(self.args) >  8:
            return self.decls.get_initinfo(self.args[8])
        else:
            return None

    @property
    def vid(self) -> int:
        """Returns the CIL vid for file vinfos and the index for global vinfos."""

        vid = self.args[0]
        return vid if vid >= 0 else self.index

    @property
    def real_vid(self) -> int:
        return self.args[0]

    @property
    def vstorage(self) -> str:
        if len(self.tags) > 1:
            return self.tags[1]
        vid = self.vid
        if vid in self.decls.varinfo_storage_classes:
            stclasses = self.decls.varinfo_storage_classes[vid]
            if len(stclasses) > 1:
                chklogger.logger.warning(
                    "Multiple storage classes found for vinfo: %s", self.vname)
                return list(stclasses)[0]
            if len(stclasses) == 0:
                chklogger.logger.warning(
                    "No storage classes found for vinfo: %s", self.vname)
                return "n"
            else:
                return list(self.decls.varinfo_storage_classes[vid])[0]
        return "n"

    @property
    def initializer(self) -> "CInitInfo":
        if self.vinit is not None:
            return self.vinit
        else:
            raise UF.CHCError(
                "Varinfo " + self.vname + " does not have an initializer")

    def has_initializer(self) -> bool:
        return self.vinit is not None

    def has_location(self) -> bool:
        return self.vdecl is not None

    @property
    def line(self) -> int:
        if self.vdecl is not None:
            return self.vdecl.line
        else:
            raise UF.CHCError(
                "Varinfo "
                + self.vname + " does not have a declaration location")

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
