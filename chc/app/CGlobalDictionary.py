# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
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
"""Dictionary of global entities across files."""

import xml.etree.ElementTree as ET

from typing import List, Optional, Tuple, TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
import chc.app.CTyp as CT

from chc.app.CDictionary import CDictionary
from chc.app.IndexManager import VarReference, CKeyReference

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CGlobalDeclarations import CGlobalDeclarations, VarReference
    from chc.app.CVarInfo import CVarInfo


class CGlobalDictionary(CDictionary):

    def __init__(self, capp: "CApplication", xnode: Optional[ET.Element]) -> None:
        CDictionary.__init__(self)
        self._capp = capp
        self._initialize(xnode)

    @property
    def is_global(self) -> bool:
        return True

    @property
    def cfile(self) -> "CFile":
        raise UF.CHCError("Global dictionary is not associated with a file")

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def decls(self) -> "CGlobalDeclarations":
        return self.capp.declarations

    def index_compinfo_key(self, compinfo, fid) -> int:
        chklogger.logger.info(
            "Index compinfo key %s for fid %d", compinfo.name, fid)
        return self.decls.index_compinfo_key(compinfo, fid)

    def index_varinfo_vid(self, vid: int, fid: int) -> int:
        varref = VarReference(fid, vid)
        gvid = self.decls.index_varinfo_vid(varref)
        if gvid is None:
            raise UF.CHError(
                f"Unable to create global index for variable ({vid}, {fid})")
        else:
            return gvid

    def index_funarg(self, funarg: CT.CFunArg) -> int:
        tags = ["arg"]
        args = [self.index_typ(funarg.typ)]

        def f(index: int, tags: List[str], args: List[int]) -> CT.CFunArg:
            itv = IT.IndexedTableValue(index, tags, args)
            return CT.CFunArg(self, itv)

        return self.funarg_table.add_tags_args(tags, args, f)

    def _initialize(self, xnode: Optional[ET.Element]) -> None:
        if xnode is None:
            return
        CDictionary.initialize(self, xnode)
