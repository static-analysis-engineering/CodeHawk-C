# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2023 Henny B. Sipma
# Copyright (c) 2024      Aarno Labs LLC
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
"""Global definitions in a c-file.

These definitions are obtained from the file <filename>_cfile.xml.
"""

from dataclasses import dataclass

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CEnumInfo import CEnumInfo
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CInitInfo import CInitInfo
    from chc.app.CLocation import CLocation
    from chc.app.CTyp import CTyp
    from chc.app.CTypeInfo import CTypeInfo
    from chc.app.CVarInfo import CVarInfo


@dataclass
class CGCompTag:
    """Definition of a struct."""

    location: "CLocation"
    compinfo: "CCompInfo"

    @property
    def name(self) -> str:
        return self.compinfo.name

    @property
    def ckey(self) -> int:
        return self.compinfo.ckey

    @property
    def is_struct(self) -> bool:
        return self.compinfo.is_struct

    def __str__(self) -> str:
        if self.is_struct:
            return f"struct {self.name} (ckey: {self.ckey})"
        else:
            return f"union {self.name} (ckey: {self.ckey})"


@dataclass
class CGEnumTag:
    """Definition of an enum."""

    location: "CLocation"
    enuminfo: "CEnumInfo"


@dataclass
class CGFunction:
    """Function declaration."""

    location: "CLocation"
    varinfo: "CVarInfo"

    @property
    def vname(self) -> str:
        return self.varinfo.vname

    @property
    def vtype(self) -> "CTyp":
        return self.varinfo.vtype

    @property
    def line(self) -> int:
        return self.varinfo.line

    def __str__(self) -> str:
        return f"{self.vname}: {self.vtype}"


@dataclass
class CGType:
    """Type definition that associates a name with a type."""

    location: "CLocation"
    typeinfo: "CTypeInfo"


@dataclass
class CGVarDecl:
    """Global variable declaration."""

    location: "CLocation"
    varinfo: "CVarInfo"

    @property
    def vname(self) -> str:
        return self.varinfo.vname


@dataclass
class CGVarDef:
    """Global variable definition (in this file)."""

    location: "CLocation"
    varinfo: "CVarInfo"
    initializer: Optional["CInitInfo"]

    @property
    def vname(self) -> str:
        return self.varinfo.vname

    def has_initializer(self) -> bool:
        return self.initializer is not None

    def __str__(self) -> str:
        if self.initializer is not None:
            return f"{self.varinfo} = {self.initializer}"
        else:
            return f"{self.varinfo}"


class CFileGlobals:

    def __init__(self, cfile: "CFile", xnode: ET.Element) -> None:
        self._cfile = cfile
        self._xnode = xnode

        self._gcomptagdefs: Optional[Dict[int, CGCompTag]] = None
        self._gcomptagdecls: Optional[Dict[int, CGCompTag]] = None
        self._genumtagdecls: Optional[Dict[str, CGEnumTag]] = None
        self._genumtagdefs: Optional[Dict[str, CGEnumTag]] = None
        self._gfunctions: Optional[Dict[int, CGFunction]] = None
        self._gtypes: Optional[Dict[str, CGType]] = None
        self._gvardecls: Optional[Dict[int, CGVarDecl]] = None
        self._gvardefs: Optional[Dict[int, CGVarDef]] = None

        self._globalcompinfockeys: Optional[Dict[int, "CCompInfo"]] = None
        self._globalvarinfonames: Optional[Dict[str, "CVarInfo"]] = None
        self._globalvarinfovids: Optional[Dict[int, "CVarInfo"]] = None

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def declarations(self) -> "CFileDeclarations":
        return self.cfile.declarations

    def expand(self, name: str) -> "CTyp":
        if name in self.gtypes:
            return self.gtypes[name].typeinfo.type.expand()
        else:
            raise UF.CHCError(f"No type definition found for {name}")

    @property
    def functioncount(self) -> int:
        return len(self.gfunctions)

    @property
    def gcomptagdecls(self) -> Dict[int, CGCompTag]:
        if self._gcomptagdecls is None:
            self._gcomptagdecls = {}
            xgc = self._xnode.find("global-comptag-declarations")
            if xgc is not None:
                for xc in xgc.findall("gcomptagdecl"):
                    xicinfo = xc.get("icinfo")
                    xiloc = xc.get("iloc")
                    if xicinfo is not None and xiloc is not None:
                        cinfo = self.declarations.get_compinfo(int(xicinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        gcomp = CGCompTag(loc, cinfo)
                        self._gcomptagdecls[cinfo.ckey] = gcomp
                    else:
                        chklogger.logger.error(
                            "Invalid comptag definition record in %s",
                            self.cfile.name)
        return self._gcomptagdecls

    @property
    def gcomptagdefs(self) -> Dict[int, CGCompTag]:
        if self._gcomptagdefs is None:
            self._gcomptagdefs = {}
            xgc = self._xnode.find("global-comptag-definitions")
            if xgc is not None:
                for xc in xgc.findall("gcomptag"):
                    xicinfo = xc.get("icinfo")
                    xiloc = xc.get("iloc")
                    if xicinfo is not None and xiloc is not None:
                        cinfo = self.declarations.get_compinfo(int(xicinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        gcomp = CGCompTag(loc, cinfo)
                        self._gcomptagdefs[cinfo.ckey] = gcomp
                    else:
                        chklogger.logger.error(
                            "Invalid comptag definition record in %s",
                            self.cfile.name)
        return self._gcomptagdefs

    @property
    def genumtagdecls(self) -> Dict[str, CGEnumTag]:
        if self._genumtagdecls is None:
            self._genumtagdecls = {}
            xge = self._xnode.find("global-enumtag-declarations")
            if xge is not None:
                for xe in xge.findall("genumtagdecl"):
                    xieinfo = xe.get("ieinfo")
                    xiloc = xe.get("iloc")
                    if xieinfo is not None and xiloc is not None:
                        einfo = self.declarations.get_enuminfo(int(xieinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        genum = CGEnumTag(loc, einfo)
                        self._genumtagdecls[einfo.ename] = genum
                    else:
                        chklogger.logger.error(
                            "Invalid enum declaration record in %s",
                            self.cfile.name)
        return self._genumtagdecls

    @property
    def genumtagdefs(self) -> Dict[str, CGEnumTag]:
        if self._genumtagdefs is None:
            self._genumtagdefs = {}
            xge = self._xnode.find("global-enumtag-definitions")
            if xge is not None:
                for xe in xge.findall("genumtag"):
                    xieinfo = xe.get("ieinfo")
                    xiloc = xe.get("iloc")
                    if xieinfo is not None and xiloc is not None:
                        einfo = self.declarations.get_enuminfo(int(xieinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        genum = CGEnumTag(loc, einfo)
                        self._genumtagdefs[einfo.ename] = genum
                    else:
                        chklogger.logger.error(
                            "Invalid enum declaration record in %s",
                            self.cfile.name)
        return self._genumtagdefs

    @property
    def gfunctions(self) -> Dict[int, CGFunction]:
        if self._gfunctions is None:
            self._gfunctions = {}
            xgf = self._xnode.find("functions")
            if xgf is not None:
                for xf in xgf.findall("gfun"):
                    xivinfo = xf.get("ivinfo")
                    xiloc = xf.get("iloc")
                    if xivinfo is not None and xiloc is not None:
                        vinfo = self.declarations.get_varinfo(int(xivinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        gfun = CGFunction(loc, vinfo)
                        self._gfunctions[vinfo.vid] = gfun
                    else:
                        chklogger.logger.error(
                            "Invalid function declaration record in %s",
                            self.cfile.name)
        return self._gfunctions

    @property
    def gtypes(self) -> Dict[str, CGType]:
        if self._gtypes is None:
            self._gtypes = {}
            xgt = self._xnode.find("global-type-definitions")
            if xgt is not None:
                for xt in xgt.findall("gtype"):
                    xitinfo = xt.get("itinfo")
                    xiloc = xt.get("iloc")
                    if xitinfo is not None and xiloc is not None:
                        tinfo = self.declarations.get_typeinfo(int(xitinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        gtype = CGType(loc, tinfo)
                        self._gtypes[tinfo.name] = gtype
                    else:
                        chklogger.logger.error(
                            "Invalid type definition record in %s",
                            self.cfile.name)
        return self._gtypes

    @property
    def gvardecls(self) -> Dict[int, CGVarDecl]:
        if self._gvardecls is None:
            self._gvardecls = {}
            xgv = self._xnode.find("global-var-declarations")
            if xgv is not None:
                for xv in xgv.findall("gvardecl"):
                    xivinfo = xv.get("ivinfo")
                    xiloc = xv.get("iloc")
                    if xivinfo is not None and xiloc is not None:
                        vinfo = self.declarations.get_varinfo(int(xivinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        gvardecl = CGVarDecl(loc, vinfo)
                        self._gvardecls[vinfo.vid] = gvardecl
                    else:
                        chklogger.logger.error(
                            "Invalid variable declaration record in %s",
                            self.cfile.name)
        return self._gvardecls

    @property
    def gvardefs(self) -> Dict[int, CGVarDef]:
        if self._gvardefs is None:
            self._gvardefs = {}
            xgv = self._xnode.find("global-var-definitions")
            if xgv is not None:
                for xv in xgv.findall("gvar"):
                    xivinfo = xv.get("ivinfo")
                    xiloc = xv.get("iloc")
                    xiinit = xv.get("iinit")
                    if (
                            xivinfo is not None
                            and xiloc is not None):
                        vinfo = self.declarations.get_varinfo(int(xivinfo))
                        loc = self.declarations.get_location(int(xiloc))
                        vinit: Optional["CInitInfo"] = None
                        if xiinit is not None:
                            vinit = self.declarations.get_initinfo(int(xiinit))
                        gvar = CGVarDef(loc, vinfo, vinit)
                        self._gvardefs[vinfo.vid] = gvar
                    else:
                        chklogger.logger.error(
                            "Invalid variable definition record in %s",
                            self.cfile.name)
        return self._gvardefs

    @property
    def global_varinfo_names(self) -> Dict[str, "CVarInfo"]:
        if self._globalvarinfonames is None:
            self._globalvarinfonames = {}
            for vardef in self.gvardefs.values():
                self._globalvarinfonames[vardef.vname] = vardef.varinfo
            for vardecl in self.gvardecls.values():
                self._globalvarinfonames[vardecl.vname] = vardecl.varinfo
            for gfun in self.gfunctions.values():
                self._globalvarinfonames[gfun.vname] = gfun.varinfo
        return self._globalvarinfonames

    @property
    def global_varinfo_vids(self) -> Dict[int, "CVarInfo"]:
        if self._globalvarinfovids is None:
            self._globalvarinfovids = {}
            for (vid, vardef) in self.gvardefs.items():
                self._globalvarinfovids[vid] = vardef.varinfo
            for (vid, vardecl) in self.gvardecls.items():
                self._globalvarinfovids[vid] = vardecl.varinfo
            for (vid, gfun) in self.gfunctions.items():
                self._globalvarinfovids[vid] = gfun.varinfo
        return self._globalvarinfovids

    def get_global_varinfos(self) -> List["CVarInfo"]:
        return list(self.global_varinfo_vids.values())

    @property
    def global_compinfo_ckeys(self) -> Dict[int, "CCompInfo"]:
        if self._globalcompinfockeys is None:
            self._globalcompinfockeys = {}
            for (ckey, comptag) in self.gcomptagdefs.items():
                self._globalcompinfockeys[ckey] = comptag.compinfo
            for (ckey, comptag) in self.gcomptagdecls.items():
                self._globalcompinfockeys[ckey] = comptag.compinfo
        return self._globalcompinfockeys

    def get_compinfos(self) -> List["CCompInfo"]:
        result: List["CCompInfo"] = []
        for gcdef in self.gcomptagdefs.values():
            result.append(gcdef.compinfo)
        for gcdecl in self.gcomptagdecls.values():
            result.append(gcdecl.compinfo)
        return result
