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

from chc.app.CGCompTag import CGCompTag
from chc.app.CGEnumTag import CGEnumTag
from chc.app.CGFunction import CGFunction
from chc.app.CGType import CGType
from chc.app.CGVarDecl import CGVarDecl
from chc.app.CGVarDef import CGVarDef

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

    This information is originally written by cchcil/cHCilWriteXml: write_xml_cfile
    based on cchcil/cHCilDeclarations.cildeclarations.

    Declarations are dependent on CFileDictionary
    """

    def __init__(self, cfile: "CFile", xnode: ET.Element, xdefnode: ET.Element
    ) -> None:
        self._cfile = cfile
        # self._dictionary = self.cfile.dictionary
        # Basic types dictionary

        # File definitions and declarations
        self.gtypes: Dict[str, CGType] = {}  # name -> CGType
        self.gcomptagdefs: Dict[int, CGCompTag] = {}  # key -> CGCompTag
        self.gcomptagdecls: Dict[int, CGCompTag] = {}  # key -> CGCompTag
        self.gvardefs: Dict[int, CGVarDef] = {}  # vid -> CGVarDef
        self.gvardecls: Dict[int, CGVarDecl] = {}  # vid -> CGVarDecl
        self.genumtagdefs: Dict[str, CGEnumTag] = {}  # ename -> CGEnumTag
        self.genumtagdecls: Dict[str, CGEnumTag] = {}  # ename -> CGEnumTag
        self.gfunctions: Dict[int, CGFunction] = {}  # vid -> CGFunction

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
        self._objmaps: Dict[str, Callable[[], Mapping[int, IndexedTableValue]]] = {
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
        self._initialize(xnode, xdefnode)
        # for (key,g) in self.gcomptagdefs.items() + self.gcomptagdecls.items():
        #     print(str(key) + ': ' + g.get_name())

    @property
    def dictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    # Retrieve definitions and declarations

    def get_gfunction(self, vid: int) -> CGFunction:
        if vid in self.gfunctions:
            return self.gfunctions[vid]
        else:
            raise Exception("nothing in gfunctions for vid \"" + str(vid) + "\"")

    def make_opaque_global_varinfo(
            self, gvid: int, gname: str, gtypeix: int) -> int:
        tags = [gname, "o_" + str(gvid)]
        args = [-1, gtypeix, -1, 1, 0, -1, 1, 0]

        def f(index: int, tags: List[str], args: List[int]) -> CVarInfo:
            itv = IndexedTableValue(index, tags, args)
            return CVarInfo(self, itv)

        return self.varinfo_table.add_tags_args(tags, args, f)

    def get_globalvar_definitions(self) -> Iterable[CGVarDef]:
        return self.gvardefs.values()

    def get_global_functions(self) -> Iterable[CGFunction]:
        return self.gfunctions.values()

    def get_compinfos(self) -> List[CCompInfo]:
        comptags = (
            list(self.gcomptagdecls.values())
            + list(self.gcomptagdefs.values()))
        return [x.compinfo for x in comptags]

    def get_global_varinfos(self) -> List[CVarInfo]:
        result: List[CVarInfo] = []
        result.extend([x.varinfo for x in self.gvardefs.values()])
        result.extend([x.varinfo for x in self.gvardecls.values()])
        result.extend([x.varinfo for x in self.gfunctions.values()])
        return result

    def get_global_varinfo(self, vid: int) -> CVarInfo:
        if vid in self.gvardefs:
            return self.gvardefs[vid].varinfo
        if vid in self.gvardecls:
            return self.gvardecls[vid].varinfo
        if vid in self.gfunctions:
            return self.gfunctions[vid].varinfo
        else:
            raise UF.CHCError("No variable found with vid: " + str(vid))

    def get_global_varinfo_by_name(self, name: str) -> CVarInfo:
        gvarinfos = self.get_global_varinfos()
        for v in gvarinfos:
            if v.vname == name:
                return v
        raise UF.CHCError(
            "Global variable " + name + " not found in file " + self.cfile.name)

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
        if name in self.gtypes:
            return self.gtypes[name].typeinfo.type.expand()
        else:
            raise UF.CHCError("No type definition found for " + name)

    def get_struct(self, ckey: int) -> CCompInfo:
        if ckey in self.gcomptagdefs:
            return self.gcomptagdefs[ckey].compinfo
        elif ckey in self.gcomptagdecls:
            return self.gcomptagdecls[ckey].compinfo
        else:
            raise UF.CHCError(
                "No struct found with ckey: " + str(ckey))

    def get_structname(self, ckey: int) -> str:
        compinfo = self.get_struct(ckey)
        if compinfo is None:
            return "struct " + str(ckey)
        else:
            return compinfo.name

    def get_structkey(self, name: str) -> int:
        d: Dict[int, str] = {}
        r: Dict[str, int] = {}
        for (key, g) in (
                list(self.gcomptagdefs.items())
                + list(self.gcomptagdecls.items())):
            if key in d:
                if g.name == d[key]:
                    continue
                else:
                    print(
                        "Multiple names for key "
                        + str(key)
                        + ": "
                        + str(d[key])
                        + " and "
                        + g.name
                    )
            else:
                d[key] = g.name
                r[g.name] = key
        if name in r:
            return r[name]
        else:
            raise UF.CHCError("Structkey not found for " + name)

    def is_struct(self, ckey: int) -> bool:
        return self.get_struct(ckey).is_struct

    def get_function_count(self) -> int:
        return len(self.gfunctions)

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
            for (ix, obj) in objmap.items():
                lines.append(str(ix).rjust(3) + "  " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name +  " does not correspond to a table")

    def __str__(self) -> str:
        lines: List[str] = []
        for t in self.tables:
            lines.append(str(t))
        lines.append(table_to_string("Types", self.gtypes, headerlen=20))
        lines.append(table_to_string("Compinfo definitions", self.gcomptagdefs))
        lines.append(table_to_string("Compinfo declarations", self.gcomptagdecls))
        lines.append(table_to_string("Enuminfo definitions", self.genumtagdefs))
        lines.append(table_to_string("Enuminfo declarations", self.genumtagdecls))
        lines.append(table_to_string("Variable definitions", self.gvardefs))
        lines.append(table_to_string("Variable declarations", self.gvardecls))
        lines.append(table_to_string("Functions", self.gfunctions))
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
            self, xnode: ET.Element, xdefnode: ET.Element, force: bool = False
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
        '''
        # Initialize file definitions dictionary from _dictionary file
        self.dictionary.initialize(force)
        xnode = UF.get_cfile_dictionary_xnode(self.cfile.capp.path, self.cfile.name)
        if xnode is None:
            raise Exception("cfile xnode returned None")
        xnode = xnode.find("c-declarations")
        if xnode is not None:
            for (t, f) in self.dictionary_tables + self.string_tables:
                t.reset()
                f(xnode.find(t.name))

        # Initialize definitions and declarations from _cfile file
        xnode = UF.get_cfile_xnode(self.cfile.capp.path, self.cfile.name)
        if xnode is None:
            raise Exception("cfile xnode returned None")
        '''
        xtypedefs = xfind_node(xdefnode, "global-type-definitions")
        self._initialize_gtypes(xtypedefs)
        xcomptagdefs = xfind_node(xdefnode, "global-comptag-definitions")
        self._initialize_gcomptagdefs(xcomptagdefs)
        xcomptagdecls = xfind_node(xdefnode, "global-comptag-declarations")
        self._initialize_gcomptagdecls(xcomptagdecls)
        xenumtagdefs = xfind_node(xdefnode, "global-enumtag-definitions")
        self._initialize_genumtagdefs(xenumtagdefs)
        xenumtagdecls = xfind_node(xdefnode, "global-enumtag-declarations")
        self._initialize_genumtagdecls(xenumtagdecls)
        xvardefs = xfind_node(xdefnode, "global-var-definitions")
        self._initialize_gvardefs(xvardefs)
        xvardecls = xfind_node(xdefnode, "global-var-declarations")
        self._initialize_gvardecls(xvardecls)
        xfuns = xfind_node(xdefnode, "functions")
        self._initialize_gfunctions(xfuns)

    '''
    def _read_xml_initinfo_table(self, xnode):
        def get_value(node: ET.Element) -> CI.CInitInfoBase:
            rep = get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return initinfo_constructors[tag](args)

        self.initinfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_offset_init_table(self, xnode):
        def get_value(node: ET.Element) -> CI.COffsetInitInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CI.COffsetInitInfo(*args)

        self.offset_init_table.read_xml(xnode, "n", get_value)

    def _read_xml_typeinfo_table(self, xnode):
        def get_value(node: ET.Element) -> CTypeInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CTypeInfo(*args)

        self.typeinfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_varinfo_table(self, xnode):
        def get_value(node: ET.Element) -> CVarInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CVarInfo(*args)

        self.varinfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_fieldinfo_table(self, xnode):
        def get_value(node: ET.Element) -> CFieldInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CFieldInfo(*args)

        self.fieldinfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_compinfo_table(self, xnode):
        def get_value(node: ET.Element) -> CCompInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CCompInfo(*args)

        self.compinfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_enumitem_table(self, xnode):
        def get_value(node: ET.Element) -> CEnumItem:
            rep = get_rep(node)
            args = (self,) + rep
            return CEnumItem(*args)

        self.enumitem_table.read_xml(xnode, "n", get_value)

    def _read_xml_enuminfo_table(self, xnode):
        def get_value(node: ET.Element) -> CEnumInfo:
            rep = get_rep(node)
            args = (self,) + rep
            return CEnumInfo(*args)

        self.enuminfo_table.read_xml(xnode, "n", get_value)

    def _read_xml_location_table(self, xnode):
        def get_value(node: ET.Element) -> CLocation:
            rep = get_rep(node)
            args = (self,) + rep
            return CLocation(*args)

        self.location_table.read_xml(xnode, "n", get_value)

    def _read_xml_filename_table(self, xnode):
        self.filename_table.read_xml(xnode)
    '''

    def _initialize_gtypes(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gtype"):
            typeinfo = self.get_typeinfo(xget_int_attr(t, "itinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.gtypes[typeinfo.name] = CGType(typeinfo, location)

    def _initialize_gcomptagdefs(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gcomptag"):
            compinfo = self.get_compinfo(xget_int_attr(t, "icinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.gcomptagdefs[compinfo.ckey] = CGCompTag(compinfo, location)

    def _initialize_gcomptagdecls(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gcomptagdecl"):
            compinfo = self.get_compinfo(xget_int_attr(t, "icinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.gcomptagdecls[compinfo.ckey] = CGCompTag(compinfo, location)

    def _initialize_genumtagdefs(self, xnode: ET.Element) -> None:
        for t in xnode.findall("genumtag"):
            enuminfo = self.get_enuminfo(xget_int_attr(t, "ieinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.genumtagdefs[enuminfo.ename] = CGEnumTag(enuminfo, location)

    def _initialize_genumtagdecls(self, xnode: ET.Element) -> None:
        for t in xnode.findall("genumtagdecl"):
            enuminfo = self.get_enuminfo(xget_int_attr(t, "ieinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.genumtagdecls[enuminfo.ename] = CGEnumTag(enuminfo, location)

    def _initialize_gvardefs(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gvar"):
            varinfo = self.get_varinfo(xget_int_attr(t, "ivinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            initializer = None
            if "iinit" in t.attrib:
                initializer = self.get_initinfo(xget_int_attr(t, "iinit"))
            self.gvardefs[varinfo.vid] = CGVarDef(varinfo, location, initializer)

    def _initialize_gvardecls(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gvardecl"):
            varinfo = self.get_varinfo(xget_int_attr(t, "ivinfo"))
            location = self.get_location(xget_int_attr(t, "iloc"))
            self.gvardecls[varinfo.vid] = CGVarDecl(varinfo, location)

    def _initialize_gfunctions(self, xnode: ET.Element) -> None:
        for t in xnode.findall("gfun"):
            varinfo = self.get_varinfo(xget_int_attr(t, "ivinfo"))
            self.gfunctions[varinfo.vid] = CGFunction(varinfo)
