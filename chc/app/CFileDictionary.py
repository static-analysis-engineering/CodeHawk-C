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
"""Dictionary of types and expressions at the file level."""

import xml.etree.ElementTree as ET

from typing import Any, cast, Dict, List, TYPE_CHECKING

from chc.app.CCompInfo import CCompInfo
from chc.app.CExp import (CExp, CExpLval)
from chc.app.CLHost import CLHost, CLHostVar
from chc.app.CLval import CLval
from chc.app.COffset import COffset
from chc.app.IndexManager import FileKeyReference

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

from chc.app.CDictionary import CDictionary

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.IndexManager import IndexManager


class CKeyLookupError(Exception):
    def __init__(self, thisfid: object, tgtfid: object, ckey: object) -> None:
        self.thisfid = thisfid
        self.tgtfid = tgtfid
        self.ckey = ckey

    def __str__(self) -> str:
        return (
            "Unable to find corresponding compinfo key for "
            + str(self.ckey)
            + " from file "
            + str(self.tgtfid)
            + " in file "
            + str(self.thisfid)
        )


class CFileDictionary(CDictionary):
    """Handles indexing of variables across different files (with distinct vid).

    All other indexing is handled by the superclass.
    """

    def __init__(self, cfile: "CFile", xnode: ET.Element)  -> None:
        CDictionary.__init__(self)
        self._cfile = cfile
        self._initialize(xnode)

    @property
    def is_global(self) -> bool:
        return False

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    @property
    def indexmanager(self) -> "IndexManager":
        return self.capp.indexmanager

    @property
    def decls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    def _initialize(self, xnode: ET.Element, force: bool = False) -> None:
        CDictionary.initialize(self, xnode, force)

    def index_compinfo_key(self, compinfo: CCompInfo, _: object) -> int:
        cfid = compinfo.decls.cfile.index
        fid = self.cfile.index
        ckey = compinfo.ckey
        if not (cfid == fid):
            fileckey = FileKeyReference(cfid, ckey)
            tgtkey = self.indexmanager.convert_ckey(fileckey, fid)
            if tgtkey is None:
                raise LookupError(
                    "Index_compinfo: Unable to find key for "
                    + str(ckey)
                    + " from file "
                    + str(cfid)
                    + " in file "
                    + str(fid)
                )
            else:
                return tgtkey
        else:
            return ckey

    def convert_ckey(self, ckey: int, fid: int = -1) -> int:
        if fid == -1:
            return ckey
        thisfid = self.cfile.index
        if not (thisfid == fid):
            fileckey = FileKeyReference(fid, ckey)
            tgtkey = self.indexmanager.convert_ckey(fileckey, thisfid)
            if tgtkey is None:
                raise CKeyLookupError(thisfid, fid, ckey)
            else:
                return tgtkey
        else:
            return ckey


    def index_lhost_offset(self, lhost: int, offset: int) -> int:
        args = [lhost, offset]

        def f(index: int, tags: List[str], args: List[int]) -> CLval:
            itv = IT.IndexedTableValue(index, tags, args)
            return CLval(self, itv)

        return self.lval_table.add_tags_args([], args, f)

    def mk_lval_exp(self, lval: int) -> int:
        args = [lval]
        tags = ["lval"]

        def f(index, key):
            return CE.CExpLval(self, index, tags, args)

        return self.exp_table.add(IT.get_key(tags, args), f)

    def index_exp(
            self, e: CExp, subst: Dict[int, CExp] = {}, fid: int = -1) -> int:

        if not e.is_lval:
            return CDictionary.index_exp(self, e, subst, fid)

        e = cast(CExpLval, e)
        lhost = e.lval.lhost

        if not lhost.is_var:
            return CDictionary.index_exp(self, e, subst, fid)
    
        lhost = cast(CLHostVar, lhost)
        if not lhost.vid in subst:
            return CDictionary.index_exp(self, e, subst, fid)

        # if lhost.is_var and lhost.vid in subst:
        if e.lval.offset.has_offset():
            if e.lval.offset.is_field:
                paroffset = e.lval.offset
                newsubst = subst.copy()
                newsubst.pop(lhost.vid)
                iargexp = self.index_exp(subst[lhost.vid], newsubst, fid)
                argexp = self.get_exp(iargexp)
                if argexp.is_lval:
                    argexp = cast(CExpLval, argexp)
                    arghost = argexp.lval.lhost
                    if argexp.lval.offset.has_offset():
                        argoffset = argexp.lval.offset
                        raise Exception(
                            "Unexpected offset in substitution argument: "
                            + str(argexp)
                            + "; offset: "
                            + str(argoffset)
                        )
                    iarghost = self.index_lhost(arghost, newsubst, fid)
                    iargoffset = self.index_offset(paroffset, fid)
                    iarglval = self.index_lhost_offset(iarghost, iargoffset)
                    return self.mk_lval_exp(iarglval)
                else:
                    raise Exception(
                        "Unexpected type in substition argument (not an lval): "
                        + str(argexp)
                    )
            else:
                raise Exception(
                    "Unexpected offset in exp to be substituted: " + str(e)
                )

        # avoid re-substitution for recursive functions
        newsubst = subst.copy()
        newsubst.pop(lhost.vid)
        return self.index_exp(subst[lhost.vid], newsubst, fid)
