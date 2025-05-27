# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2025 Aarno Labs LLC
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
"""C-file main access point."""

import os
import xml.etree.ElementTree as ET

from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING)

from chc.api.InterfaceDictionary import InterfaceDictionary
from chc.api.CFileContracts import CFileContracts
from chc.api.CFunctionContract import CFunctionContract

from chc.app.CContextDictionary import CContextDictionary
from chc.app.CFileAssignmentDictionary import CFileAssignmentDictionary
from chc.app.CFileDictionary import CFileDictionary
from chc.app.CFileDeclarations import CFileDeclarations
from chc.app.CFileGlobals import CFileGlobals
from chc.app.CFunction import CFunction
from chc.app.CFileGlobals import CGCompTag
from chc.app.CFileGlobals import CGEnumTag
from chc.app.CFileGlobals import CGFunction
from chc.app.CFileGlobals import CGType
from chc.app.CFileGlobals import CGVarDecl
from chc.app.CFileGlobals import CGVarDef
from chc.app.CGXrefs import CGXrefs
from chc.app.CPrettyPrinter import CPrettyPrinter

from chc.proof.CFilePredicateDictionary import CFilePredicateDictionary
from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPPO import CFunctionPPO

from chc.source.CSrcFile import CSrcFile

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger
import chc.util.xmlutil as UX


if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CInstr import CCallInstr
    from chc.app.CVarInfo import CVarInfo


class CFunctionNotFoundException(Exception):
    def __init__(self, cfile: "CFile", functionname: str) -> None:
        self.cfile = cfile
        self.functionname = functionname

    def __str__(self) -> str:
        lines = []
        lines.append("*" * 80)
        lines.append(
            (
                "Function "
                + self.functionname
                + " not found in file "
                + self.cfile.name
                + "; function names available:"
            )
        )
        lines.append("-" * 80)
        for n in self.cfile.functionnames:
            lines.append("  " + n)
        lines.append("*" * 80)
        return "\n".join(lines)


class CFile(object):
    """C File main access point."""

    def __init__(
            self,
            capp: "CApplication",
            index: int,
            cfilename: str,
            cfilepath: Optional[str]) -> None:
        self._index = index
        self._capp = capp
        self._cfilename = cfilename
        self._cfilepath = cfilepath
        self._xnode: Optional[ET.Element] = None
        self._declarations: Optional[CFileDeclarations] = None
        self._dictionary: Optional[CFileDictionary] = None
        self._contextdictionary: Optional[CContextDictionary] = None
        self._predicatedictionary: Optional[CFilePredicateDictionary] = None
        self._interfacedictionary: Optional[InterfaceDictionary] = None
        self._assigndictionary: Optional[CFileAssignmentDictionary] = None
        self._functions: Optional[Dict[int, CFunction]] = None  # vid -> CFunction
        self.strings: Dict[int, Tuple[int, str]] = {}  # string-index -> (len,string)
        self._sourcefile: Optional[CSrcFile] = None
        self._contracts: Optional[CFileContracts] = None

        self._cfileglobals: Optional[CFileGlobals] = None

    @property
    def index(self) -> int:
        return self._index

    @property
    def cfilename(self) -> str:
        """Returns base filename (without extension)."""

        return self._cfilename

    @property
    def cfilepath(self) -> Optional[str]:
        """Returns path relative to project directory or None if at toplevel."""

        return self._cfilepath

    @property
    def name(self) -> str:
        """Returns the full name relative to the project directory.

        Note: the filename is without extension
        """

        if self.cfilepath is None:
            return self.cfilename
        else:
            return os.path.join(self.cfilepath, self.cfilename)

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def targetpath(self) -> str:
        return self.capp.targetpath

    @property
    def projectname(self) -> str:
        return self.capp.projectname

    @property
    def contractpath(self) -> str:
        return self.capp.contractpath

    @property
    def cfileglobals(self) -> CFileGlobals:
        if self._cfileglobals is None:
            chklogger.logger.info("Load _cfile for %s", self.name)
            xcfile = UF.get_cfile_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            if xcfile is None:
                raise UF.CHCError(f"_cfile.xml not found for {self.name}")
            self._cfileglobals = CFileGlobals(self, xcfile)
        return self._cfileglobals

    @property
    def gfunctions(self) -> Dict[int, "CGFunction"]:
        return self.cfileglobals.gfunctions

    def header_declarations(
            self,
            gvarnames: Dict[str, str] = {},
            fnnames: Dict[str, str] = {}) -> str:
        lines: List[str] = []
        srcfilename = self.name + ".c"
        lines.append("// " + srcfilename + "\n")
        gvars = self.gvardefs.values()
        if len(gvars) > 0:
            lines.append("// static and global variable definitions\n")
        for gvar in gvars:
            pp = CPrettyPrinter()
            binloc: Optional[str] = gvarnames.get(gvar.varinfo.vname)
            gvardef = pp.gvar_definition_str(
                gvar.varinfo, srcloc=srcfilename, binloc=binloc)
            lines.append(gvardef)

        fns = self.gfunctions.values()
        if len(gvars) > 0 and len(fns) > 0:
            lines.append("// function signatures\n")
        for fn in fns:
            if fn.is_system_function:
                continue
            pp = CPrettyPrinter()
            binloc = fnnames.get(fn.varinfo.vname)
            fndecl = pp.function_declaration_str(
                fn.varinfo, srcloc=srcfilename, binloc=binloc)
            lines.append(fndecl)
        return "\n".join(lines)

    @property
    def functioncount(self) -> int:
        return self.cfileglobals.functioncount

    @property
    def gcomptagdecls(self) -> Dict[int, "CGCompTag"]:
        return self.cfileglobals.gcomptagdecls

    @property
    def gcomptagdefs(self) -> Dict[int, "CGCompTag"]:
        return self.cfileglobals.gcomptagdefs

    @property
    def genumtagdecls(self) -> Dict[str, "CGEnumTag"]:
        return self.cfileglobals.genumtagdecls

    @property
    def genumtagdefs(self) -> Dict[str, "CGEnumTag"]:
        return self.cfileglobals.genumtagdefs

    @property
    def gtypes(self) -> Dict[str, "CGType"]:
        return self.cfileglobals.gtypes

    @property
    def gvardecls(self) -> Dict[int, "CGVarDecl"]:
        return self.cfileglobals.gvardecls

    @property
    def gvardefs(self) -> Dict[int, "CGVarDef"]:
        return self.cfileglobals.gvardefs

    def has_global_varinfo(self, vid: int) -> bool:
        return vid in self.cfileglobals.global_varinfo_vids

    def get_global_varinfo(self, vid: int) -> "CVarInfo":
        if vid in self.cfileglobals.global_varinfo_vids:
            return self.cfileglobals.global_varinfo_vids[vid]
        else:
            raise UF.CHCError(f"Global variable with vid: {vid} not found")

    def has_global_varinfo_by_name(self, name: str) -> bool:
        return name in self.cfileglobals.global_varinfo_names

    def get_global_varinfo_by_name(self, name: str) -> "CVarInfo":
        if name in self.cfileglobals.global_varinfo_names:
            return self.cfileglobals.global_varinfo_names[name]
        else:
            raise UF.CHCError(
                f"Varinfo with name {name} not found in {self.name}")

    @property
    def functions(self) -> Dict[int, CFunction]:
        if self._functions is None:
            self._functions = {}
            for (vid, gf) in self.gfunctions.items():
                fnname = gf.vname
                xnode = UF.get_cfun_xnode(
                    self.targetpath,
                    self.projectname,
                    self.cfilepath,
                    self.cfilename,
                    fnname)
                if xnode is not None:
                    cfunction = CFunction(self, xnode, fnname)
                    self._functions[vid] = cfunction
                else:
                    chklogger.logger.warning("Function {fnname} not found")
        return self._functions

    @property
    def functionxref(self) -> Dict[str, int]:
        """Returns a map from function names to vid's."""

        return {cfun.name: index for (index, cfun) in self.functions.items()}

    @property
    def functionnames(self) -> List[str]:
        return [cfun.name for cfun in self.functions.values()]

    @property
    def sourcefile(self) -> "CSrcFile":
        if self._sourcefile is None:
            srcpath = UF.get_savedsource_path(self.targetpath, self.projectname)
            srcfile = os.path.join(srcpath, self.name + ".c")
            chklogger.logger.info("Source file: %s", srcfile)
            self._sourcefile = CSrcFile(self.capp, srcfile)
        return self._sourcefile

    @property
    def dictionary(self) -> CFileDictionary:
        if self._dictionary is None:
            xnode = UF.get_cfile_dictionary_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            if xnode is None:
                raise UF.CHCError("File dictionary file not found")
            xdict = xnode.find("c-dictionary")
            if xdict is None:
                raise UF.CHCError("File dictionary node not found")
            self._dictionary = CFileDictionary(self, xdict)
        return self._dictionary

    def reset_dictionary(self) -> None:
        self._dictionary = None

    @property
    def contextdictionary(self) -> CContextDictionary:
        if self._contextdictionary is None:
            xnode = UF.get_cfile_contexttable_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            if xnode is None:
                raise UF.CHCError("Context table file not found")
            self._contextdictionary = CContextDictionary(self, xnode)
        return self._contextdictionary

    def reset_contextdictionary(self) -> None:
        self._contextdictionary = None

    @property
    def declarations(self) -> CFileDeclarations:
        d = self.dictionary
        if self._declarations is None:
            xnode = UF.get_cfile_dictionary_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            if xnode is None:
                raise UF.CHCError("File dictionary file not found")
            xdecls = xnode.find("c-declarations")
            if xdecls is None:
                raise UF.CHCError("File declarations node not found")
            self._declarations = CFileDeclarations(self, xdecls)
        return self._declarations

    def reset_declarations(self) -> None:
        self._declarations = None

    @property
    def interfacedictionary(self) -> InterfaceDictionary:
        if self._interfacedictionary is None:
            xnode = UF.get_cfile_interface_dictionary_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            self._interfacedictionary = InterfaceDictionary(self, xnode)
        return self._interfacedictionary

    def reset_interfacedictionary(self) -> None:
        self._interfacedictionary = None

    @property
    def assigndictionary(self) -> CFileAssignmentDictionary:
        if self._assigndictionary is None:
            xnode = UF.get_cfile_assignment_dictionary_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            self._assigndictionary = CFileAssignmentDictionary(self, xnode)
        return self._assigndictionary

    @property
    def predicatedictionary(self) -> CFilePredicateDictionary:
        if self._predicatedictionary is None:
            xnode = UF.get_cfile_predicate_dictionary_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename)
            self._predicatedictionary = CFilePredicateDictionary(self, xnode)
        return self._predicatedictionary

    def reset_predicatedictionary(self) -> None:
        self._predicatedictionary = None

    def collect_post_assumes(self) -> None:
        """Collect callsite postconditions from callee's contracts and add as assume."""

        for fn in self.get_functions():
            try:
                fn.collect_post_assumes()
            except UF.CHCError as e:
                chklogger.logger.error(str(e))
                continue

        self.save_interface_dictionary()
        self.save_predicate_dictionary()
        self.save_declarations()

    @property
    def contracts(self) -> CFileContracts:
        if self._contracts is None:
            self._contracts = CFileContracts(self, self.contractpath)
        return self._contracts

    def has_file_contracts(self) -> bool:
        return not (self.contracts is None)

    def has_outstanding_fn_api_requests(self) -> bool:
        """Returns true if any of this file's functions posted a request."""

        return (
            any(fn.has_outstanding_api_requests() for fn in self.get_functions()))

    def has_function_contract(self, name: str) -> bool:
        return self.contracts.has_function_contract(name)

    def get_function_contract(self, name: str) -> Optional[CFunctionContract]:
        if self.has_function_contract(name):
            return self.contracts.function_contract(name)
        return None

    def get_max_functionname_length(self) -> int:
        if len(self.functionnames) > 0:
            return max([len(x) for x in self.functionnames])
        else:
            return 10

    def get_source_line(self, n: int) -> str:
        line = self.sourcefile.get_line(n)
        return line if line else "n/a"

    def reinitialize_tables(self) -> None:
        chklogger.logger.info("Reinitialize tables: %s", self.name)
        self.reset_dictionary()
        self.reset_contextdictionary()
        self.reset_declarations()
        self.reset_predicatedictionary()
        self.reset_interfacedictionary()
        for fn in self.get_functions():
            fn.reinitialize_tables()

    def has_function_by_name(self, fnname: str) -> bool:
        return fnname in self.functionxref

    def get_function_by_name(self, fnname: str) -> CFunction:
        if fnname in self.functionxref:
            fvid = self.functionxref[fnname]
            return self.functions[fvid]
        else:
            raise CFunctionNotFoundException(self, fnname)

    def get_function_by_index(self, index: int) -> CFunction:
        if index in self.functions:
            return self.functions[index]
        else:
            raise Exception(
                'Unable to find function with global vid ' + str(index))

    def has_function_by_index(self, index: int) -> bool:
        return index in self.functions

    def get_functions(self) -> Iterable[CFunction]:
        return self.functions.values()

    def iter_functions(self, f: Callable[[CFunction], None]) -> None:
        for fn in self.get_functions():
            try:
                f(fn)
            except UF.CHCError as e:
                chklogger.logger.error(str(e))
                continue

    def get_compinfos(self) -> List["CCompInfo"]:
        return self.cfileglobals.get_compinfos()

    def get_compinfo_by_ckey(self, ckey: int) -> "CCompInfo":
        if ckey in self.cfileglobals.global_compinfo_ckeys:
            return self.cfileglobals.global_compinfo_ckeys[ckey]
        else:
            raise UF.CHCError(f"Struct with ckey {ckey} not found")

    def get_strings(self) -> Dict[str, List[str]]:
        """Returns a list of the strings referenced in this file."""

        result: Dict[str, List[str]] = {}
        for fn in self.get_functions():
            result[fn.name] = fn.strings
        return result

    def get_variable_uses(self, vid: int) -> Dict[str, int]:
        """Returns a mapping from function name to a count of variable refs.

        function name -> number of references with a given vid.
        """
        result: Dict[str, int] = {}
        for fn in self.get_functions():
            result[fn.name] = fn.get_variable_uses(vid)
        return result

    def get_callinstrs(self) -> List["CCallInstr"]:
        result: List["CCallInstr"] = []

        for fn in self.get_functions():
            result.extend(fn.call_instrs)
        return result

    def reload_spos(self) -> None:
        for fn in self.get_functions():
            try:
                fn.reload_spos()
            except UF.CHCError as e:
                chklogger.logger.error(e.msg)
                continue

    def reload_ppos(self) -> None:
        for fn in self.get_functions():
            try:
                fn.reload_ppos()
            except UF.CHCError as e:
                chklogger.logger.error(e.msg)
                continue

    def get_ppos(self) -> List[CFunctionPO]:
        result: List[CFunctionPO] = []
        for fn in self.get_functions():
            try:
                result.extend(fn.get_ppos())
            except UF.CHCError as e:
                chklogger.logger.error(str(e))
                continue
        return result

    def get_open_ppos(self) -> List[CFunctionPO]:
        """Returns a list of open primary proof obligations."""

        result: List[CFunctionPO] = []
        for fn in self.get_functions():
            result.extend(fn.get_open_ppos())
        return result

    def get_ppos_violated(self) -> List[CFunctionPO]:
        """Returns a list of primary proof obligations violated."""

        result: List[CFunctionPO] = []
        for fn in self.get_functions():
            result.extend(fn.get_ppos_violated())
        return result

    def get_ppos_delegated(self) -> List[CFunctionPO]:
        """Returns a list of primary proof obligations delegated."""

        result: List[CFunctionPO] = []
        for fn in self.get_functions():
            result.extend(fn.get_ppos_delegated())
        return result

    def get_spos(self) -> List[CFunctionPO]:
        result: List[CFunctionPO] = []
        for fn in self.get_functions():
            try:
                result.extend(fn.get_spos())
            except UF.CHCError as e:
                chklogger.logger.error(str(e))
                continue
        return result

    def get_line_ppos(self) -> Dict[int, Dict[str, Any]]:
        result: Dict[int, Dict[str, Any]] = {}
        fnppos = self.get_ppos()
        for ppo in fnppos:
            line = ppo.line
            pred = ppo.predicate_name
            if line not in result:
                result[line] = {}
            if pred not in result[line]:
                result[line][pred] = {}
                result[line][pred]["function"] = "TBD"
                result[line][pred]["ppos"] = []
                result[line][pred]["ppos"].append(ppo)
        return result

    def get_fn_spos(self, fname: str) -> List[CFunctionPO]:
        if self.has_function_by_name(fname):
            fn = self.get_function_by_name(fname)
            return fn.get_spos()
        else:
            return []

    def save_predicate_dictionary(self) -> None:
        xroot = UX.get_xml_header("po-dictionary", "po-dictionary")
        xnode = ET.Element("po-dictionary")
        xroot.append(xnode)
        self.predicatedictionary.write_xml(xnode)
        filename = UF.get_cfile_predicate_dictionaryname(
            self.targetpath, self.projectname, self.cfilepath, self.cfilename)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))
        chklogger.logger.info("Saved predicate dictionary: %s", filename)

    def save_interface_dictionary(self) -> None:
        xroot = UX.get_xml_header("interface-dictionary", "interface-dictionary")
        xnode = ET.Element("interface-dictionary")
        xroot.append(xnode)
        self.interfacedictionary.write_xml(xnode)
        filename = UF.get_cfile_interface_dictionaryname(
            self.targetpath, self.projectname, self.cfilepath, self.cfilename)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))
        chklogger.logger.info("Saved interface dictionary: %s", filename)

    def save_declarations(self) -> None:
        xroot = UX.get_xml_header("cfile", "cfile")
        xnode = ET.Element("cfile")
        xroot.append(xnode)
        self.declarations.write_xml(xnode)
        filename = UF.get_cfile_dictionaryname(
            self.targetpath, self.projectname, self.cfilepath, self.cfilename)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))
        chklogger.logger.info("Saved file declarations: %s", filename)

    def save_user_assumptions(self, userdata, assumptions):
        path = self.capp.path
        xroot = UX.get_xml_header("cfile", "cfile")
        xnode = ET.Element("cfile")
        xroot.append(xnode)
        userdata.write_xml(xnode, assumptions)
        filename = UF.get_cfile_usr_filename(path, self.name)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))
        chklogger.logger.info("Saved user assumptions: %s", filename)

    def create_contract(
            self, contractpath, preservesmemory=[], seed={}, ignorefns={}):
        if UF.has_contracts(contractpath, self.name):
            return
        cnode = ET.Element("cfile")
        cnode.set("name", self.name)
        dnode = ET.Element("data-structures")
        cnode.append(dnode)
        fseed = seed[self.name] if self.name in seed else None

        # add seed global variables
        if fseed is not None:
            if "globalvars" in fseed:
                ggnode = ET.Element("global-variables")
                cnode.append(ggnode)
                for gvar in fseed["globalvars"]:
                    gnode = ET.Element("gvar")
                    gnode.set("name", gvar)
                    ggnode.append(gnode)
                    for (gattr, gval) in fseed["globalvars"][gvar].items():
                        gnode.set(gattr, gval)

        ffnode = ET.Element("functions")
        cnode.append(ffnode)
        fseedfunctions = (
            fseed["functions"] if (fseed is not None) and "functions" in fseed
            else None
        )

        # add functions
        for fn in sorted(self.get_functions(), key=lambda fn: fn.name):
            fnode = ET.Element("function")
            fnode.set("name", fn.name)
            if fn.name in ignorefns:
                fnode.set("ignore", "yes")
                fnode.set("src", ignorefns[fn.name])
            ppnode = ET.Element("parameters")
            for fid in sorted(fn.formals, key=lambda fid: fn.formals[fid].vparam):
                pnode = ET.Element("par")
                pnode.set("name", fn.formals[fid].vname)
                pnode.set("nr", str(fn.formals[fid].vparam))
                ppnode.append(pnode)
            fnode.append(ppnode)

            # add pre/postconditions
            if (fseedfunctions is not None) and fn.name in fseedfunctions:
                fnseed = fseedfunctions[fn.name]
                if "postconditions" in fnseed:
                    pcnode = ET.Element("postconditions")
                    pcs = fnseed["postconditions"]
                    if "value" in pcs:
                        postnode = ET.Element("post")
                        mathnode = ET.Element("math")
                        applynode = ET.Element("apply")
                        eqnode = ET.Element("eq")
                        retnode = ET.Element("return")
                        cnnode = ET.Element("cn")
                        cnnode.text = pcs["value"]
                        applynode.extend([eqnode, retnode, cnnode])
                        mathnode.append(applynode)
                        postnode.append(mathnode)
                        pcnode.append(postnode)
                fnode.append(pcnode)

            if fn.name in preservesmemory:
                pcnode = ET.Element("postconditions")
                fnode.append(pcnode)
                prmnode = ET.Element("preserves-all-memory")
                apnode = ET.Element("apply")
                mnode = ET.Element("math")
                pnode = ET.Element("post")
                pnode.append(mnode)
                mnode.append(apnode)
                apnode.append(prmnode)
                pcnode.append(pnode)
            ffnode.append(fnode)
        UF.save_contracts_file(contractpath, self.name, cnode)
