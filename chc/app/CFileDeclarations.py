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
"""Declarations at the file level."""

from typing import (
    Any,
    Callable,
    cast,
    Dict,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Tuple,
    TYPE_CHECKING)
import xml.etree.ElementTree as ET

from chc.app.CDictionaryRecord import CDeclarationsRecord
import chc.app.CInitInfo as CI

from chc.app.CDeclarations import CDeclarations

from chc.app.CFileGlobals import CGCompTag
from chc.app.CFileGlobals import CGEnumTag
from chc.app.CFileGlobals import CGFunction
from chc.app.CFileGlobals import CGType
from chc.app.CFileGlobals import CGVarDecl
from chc.app.CFileGlobals import CGVarDef

from chc.app.CLocation import CLocation
from chc.app.CCompInfo import CCompInfo
from chc.app.CEnumInfo import CEnumInfo
from chc.app.CEnumItem import CEnumItem
from chc.app.CFieldInfo import CFieldInfo
from chc.app.CVarInfo import CVarInfo
from chc.app.CTyp import CTyp
from chc.app.CTypeInfo import CTypeInfo

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue
import chc.util.StringIndexedTable as SI
import chc.util.xmlutil as UX

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary


def table_to_string(title: str, d: Dict[Any, Any], headerlen: int = 10) -> str:
    lines = []
    lines.append("\n" + title)
    for k in sorted(d):
        lines.append(str(k).rjust(headerlen) + "  " + str(d[k]))
    return "\n".join(lines)


def xfind_node(p: ET.Element, tag: str) -> ET.Element:
    return UF.xfind_node(p, tag, "CFileDeclarations")


def xget_attr(p: ET.Element, tag: str) -> str:
    return UF.xget_attr(p, tag, "CFileDeclarations")


def xget_int_attr(p: ET.Element, tag: str) -> int:
    return UF.xget_int_attr(p, tag, "CFileDeclarations")


class CFilename(CDeclarationsRecord):

    def __init__(self, decls: CDeclarations, ixval: IndexedTableValue):
        CDeclarationsRecord.__init__(self, decls, ixval)

    def get_filename(self) -> str:
        return self.tags[0]

    def __str__(self) -> str:
        return self.get_filename()


class CFileDeclarations(CDeclarations):
    """C File level definitions and declarations.

    This information is originally written by cchcil/cHCilWriteXml:
    write_xml_cfile based on cchcil/cHCilDeclarations.cildeclarations.

    Declarations are dependent on CFileDictionary
    """

    def __init__(self, cfile: "CFile", xnode: ET.Element) -> None:
        self._cfile = cfile

        # File definition dictionary
        self.initinfo_table = IndexedTable("initinfo-table")
        self.offset_init_table = IndexedTable("offset-init-table")
        self.typeinfo_table = IndexedTable("typeinfo-table")
        self.varinfo_table = IndexedTable("varinfo-table")
        self.fieldinfo_table = IndexedTable("fieldinfo-table")
        self.compinfo_table = IndexedTable("compinfo-table")
        self.enumitem_table = IndexedTable("enumitem-table")
        self.enuminfo_table = IndexedTable("enuminfo-table")
        self.location_table = IndexedTable("location-table")
        self.filename_table = SI.StringIndexedTable("filename-table")
        self.tables: List[IndexedTable] = [
            self.location_table,
            self.initinfo_table,
            self.offset_init_table,
            self.typeinfo_table,
            self.varinfo_table,
            self.fieldinfo_table,
            self.compinfo_table,
            self.enumitem_table,
            self.enuminfo_table]

        self._objmaps: Dict[
            str, Callable[[], Mapping[int, IndexedTableValue]]] = {
            "compinfo": self.get_compinfo_map,
            "enuminfo": self.get_enuminfo_map,
            "enumitem": self.get_enumitem_map,
            "fieldinfo": self.get_fieldinfo_map,
            "initinfo": self.get_initinfo_map,
            "location": self.get_location_map,
            "offsetinfo": self.get_offset_init_map,
            "typeinfo": self.get_typeinfo_map,
            "varinfo": self.get_varinfo_map}

        # self.string_table = SI.StringIndexedTable("string-table")
        self._initialize(xnode)

    @property
    def dictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    def make_opaque_global_varinfo(
            self, gvid: int, gname: str, gtypeix: int) -> int:
        tags = [gname, "o_" + str(gvid)]
        args = [-1, gtypeix, -1, 1, 0, -1, 1, 0]

        def f(index: int, tags: List[str], args: List[int]) -> CVarInfo:
            itv = IndexedTableValue(index, tags, args)
            return CVarInfo(self, itv)

        return self.varinfo_table.add_tags_args(tags, args, f)

    def get_compinfo_by_ckey(self, ckey: int) -> CCompInfo:
        return self.cfile.get_compinfo_by_ckey(ckey)

    def get_global_varinfos(self) -> List[CVarInfo]:
        return self.cfile.cfileglobals.get_global_varinfos()

    # ------------------ Retrieve items from file definitions dictionary -----

    def get_initinfo(self, ix: int) -> CI.CInitInfo:
        itv = self.initinfo_table.retrieve(ix)
        if itv.tags[0] == "single":
            return CI.CSingleInitInfo(self, itv)
        elif itv.tags[0] == "compound":
            return CI.CCompoundInitInfo(self, itv)
        else:
            raise UF.CHCError("initinfo tag: " + itv.tags[0] + " not recognized")

    def get_initinfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.initinfo_table.objectmap(self.get_initinfo)

    def get_offset_init(self, ix: int) -> CI.COffsetInitInfo:
        itv = self.offset_init_table.retrieve(ix)
        return CI.COffsetInitInfo(self, itv)

    def get_offset_init_map(self) -> Dict[int, IndexedTableValue]:
        return self.offset_init_table.objectmap(self.get_offset_init)

    def get_varinfo(self, ix: int) -> CVarInfo:
        itv = self.varinfo_table.retrieve(ix)
        return CVarInfo(self, itv)

    def get_varinfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.varinfo_table.objectmap(self.get_varinfo)

    def get_compinfo(self, ix: int) -> CCompInfo:
        itv = self.compinfo_table.retrieve(ix)
        return CCompInfo(self, itv)

    def get_compinfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.compinfo_table.objectmap(self.get_compinfo)

    def get_enumitem(self, ix: int) -> CEnumItem:
        itv = self.enumitem_table.retrieve(ix)
        return CEnumItem(self, itv)

    def get_enumitem_map(self) -> Dict[int, IndexedTableValue]:
        return self.enumitem_table.objectmap(self.get_enumitem)

    def get_enuminfo(self, ix: int) -> CEnumInfo:
        itv = self.enuminfo_table.retrieve(ix)
        return CEnumInfo(self, itv)

    def get_enuminfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.enuminfo_table.objectmap(self.get_enuminfo)

    def get_fieldinfo(self, ix: int) -> CFieldInfo:
        itv = self.fieldinfo_table.retrieve(ix)
        return CFieldInfo(self, itv)

    def get_fieldinfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.fieldinfo_table.objectmap(self.get_fieldinfo)

    def get_typeinfo(self, ix: int) -> CTypeInfo:
        itv = self.typeinfo_table.retrieve(ix)
        return CTypeInfo(self, itv)

    def get_typeinfo_map(self) -> Dict[int, IndexedTableValue]:
        return self.typeinfo_table.objectmap(self.get_typeinfo)

    def get_location(self, ix: int) -> CLocation:
        itv = self.location_table.retrieve(ix)
        return CLocation(self, itv)

    def get_location_map(self) -> Dict[int, IndexedTableValue]:
        return self.location_table.objectmap(self.get_location)

    def get_filename(self, ix: int) -> str:
        return self.filename_table.retrieve(ix)

    # ------------------- Provide read_xml service to file semantics files ---

    def read_xml_varinfo(
            self, xnode: ET.Element, tag: str = "ivinfo") -> CVarInfo:
        return self.get_varinfo(xget_int_attr(xnode, tag))

    def read_xml_location(
            self, xnode: ET.Element, tag: str = "iloc") -> CLocation:
        index = xget_int_attr(xnode, tag)
        if index == -1:
            args = [-1, -1, -1]
            itv = IndexedTableValue(-1, [], args)
            return CLocation(self, itv)
        return self.get_location(index)

    # -------------------- Index items by category ---------------------------

    def index_filename(self, name: str) -> int:
        return self.filename_table.add(name)

    def index_location(self, loc: CLocation) -> int:
        if (loc.line == -1) and (loc.byte == -1):
            return -1
        args = [self.index_filename(loc.file), loc.byte, loc.line]

        def f(index: int, tags: List[str], args: List[int]) -> CLocation:
            itv = IndexedTableValue(index, tags, args)
            return CLocation(self, itv)

        return self.location_table.add_tags_args([], args, f)

    # ---------------------- Provide write_xml service -----------------------

    def write_xml_location(
            self,
            xnode: ET.Element,
            loc: CLocation,
            tag: str = "iloc") -> None:
        xnode.set(tag, str(self.index_location(loc)))

    # assume that python never creates new varinfos
    def write_xml_varinfo(
            self,
            xnode: ET.Element,
            vinfo: CVarInfo,
            tag: str = "ivinfo") -> None:
        xnode.set(tag, str(vinfo.index))

    # ------------------- Miscellaneous other services -----------------------

    def expand(self, name: str) -> CTyp:
        return self.cfile.cfileglobals.expand(name)

    def get_max_line(self) -> int:
        findex = self.index_filename(self.cfile.name + ".c")
        maxline = 0
        # use the native representation, rather than the CLocation object
        for v in self.location_table.values():
            if v.args[0] == findex and v.args[2] > maxline:
                maxline = v.args[2]
        return maxline

    def get_code_line_count(self) -> int:
        findex = self.index_filename(self.cfile.name + ".c")
        count = 0
        # use the native representation, rather than the CLocation object
        for v in self.location_table.values():
            if v.args[0] == findex:
                count += 1
        return count

    # ---------------------------- Printing ----------------------------------

    def objectmap_to_string(self, name: str) -> str:
        if name in self._objmaps:
            objmap = self._objmaps[name]()
            lines: List[str] = []
            if len(objmap) == 0:
                lines.append(f"\nTable for {name} is empty\n")
            else:
                lines.append("index  value")
                lines.append("-" * 80)
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "    " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name + " does not correspond to a table")

    def __str__(self) -> str:
        lines: List[str] = []
        for t in self.tables:
            lines.append(str(t))
        return "\n".join(lines)

    # ------------------------ Saving ----------------------------------------

    def write_xml(self, node: ET.Element) -> None:
        dictnode = ET.Element("c-dictionary")
        self.dictionary.write_xml(dictnode)
        declsnode = ET.Element("c-declarations")

        def f(n: ET.Element, r: IndexedTableValue) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            declsnode.append(tnode)
        tnode = ET.Element(self.filename_table.name)
        self.filename_table.write_xml(tnode)
        declsnode.append(tnode)
        node.extend([dictnode, declsnode])

    # ---------------------- Initialization ----------------------------------

    def _initialize(
            self, xnode: ET.Element, force: bool = False
    ) -> None:
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.reset()
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError(
                    "Table " + t.name + " not found in file declarations")
        xstable = xnode.find(self.filename_table.name)
        if xstable is not None:
            self.filename_table.reset()
            self.filename_table.read_xml(xstable)
        else:
            raise UF.CHCError(
                "Filename table not found in file declarations")
