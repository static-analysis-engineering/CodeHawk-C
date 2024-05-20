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
"""Cross references between variable and struct definitions in different files."""

import xml.etree.ElementTree as ET

from typing import Dict, Optional, TYPE_CHECKING

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CFile import CFile


class CGXrefs:

    def __init__(self, cfile: "CFile", xnode: Optional[ET.Element]) -> None:
        self._xnode = xnode
        self._cfile = cfile
        self._compkeys: Optional[Dict[int, int]] = None  # local id -> global id
        self._varinfos: Optional[Dict[int, int]] = None  # local id -> global id

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def compkeys(self) -> Dict[int, int]:
        if self._compkeys is None:
            self._compkeys = {}
            if self._xnode is not None:
                xcompxrefs = self._xnode.find("compinfo-xrefs")
                if xcompxrefs is not None:
                    for c in xcompxrefs.findall("cxref"):
                        xckey = c.get("ckey")
                        xgckey = c.get("gckey")
                        if xckey is None or xgckey is None:
                            raise UF.CHCError(
                                "compinfo-xrefs: ckey or gckey not found")
                        self._compkeys[int(xckey)] = int(xgckey)
        return self._compkeys

    @property
    def varinfos(self) -> Dict[int, int]:
        if self._varinfos is None:
            self._varinfos = {}
            if self._xnode is not None:
                xvarxrefs = self._xnode.find("varinfo-xrefs")
                if xvarxrefs is not None:
                    for v in xvarxrefs.findall("vxref"):
                        xvid = v.get("vid")
                        xgvid = v.get("gvid")
                        if xvid is None or xgvid is None:
                            raise UF.CHCError(
                                "varinfo-xrefs: vid or gvid not found")
                        self._varinfos[int(xvid)] = int(xgvid)
        return self._varinfos

    def get_globalkey(self, localkey: int) -> int:
        if localkey in self.compkeys:
            return self.compkeys[localkey]
        return localkey

    def getglobalvid(self, localvid: int) -> int:
        if localvid in self.varinfos:
            return self.varinfos[localvid]
        return localvid
