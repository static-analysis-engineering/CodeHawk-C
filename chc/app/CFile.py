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
import os
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.xmlutil as UX

from chc.app.CFunction import CFunction
from chc.app.CGCompTag import CGCompTag
from chc.app.CGEnumTag import CGEnumTag
from chc.app.CGFunction import CGFunction
from chc.app.CGType import CGType
from chc.app.CGVarDecl import CGVarDecl
from chc.app.CGVarDef import CGVarDef

from chc.api.InterfaceDictionary import InterfaceDictionary
from chc.api.CFileContracts import CFileContracts
from chc.api.CFileCandidateContracts import CFileCandidateContracts
from chc.app.CGXrefs import CGXrefs
from chc.source.CSrcFile import CSrcFile
from chc.app.CContextTable import CContextTable
from chc.app.CFileDictionary import CFileDictionary
from chc.app.CFileDeclarations import CFileDeclarations
from chc.app.CFileAssignmentDictionary import CFileAssignmentDictionary


from chc.proof.CFilePredicateDictionary import CFilePredicateDictionary


class CFunctionNotFoundException(Exception):
    def __init__(self, cfile, functionname):
        self.cfile = cfile
        self.functionname = functionname

    def __str__(self):
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
    """C File level declarations."""

    def __init__(self, capp, index, xnode):
        self.index = index
        self.capp = capp
        self.xnode = xnode
        self.name = self.xnode.get("filename")
        self.declarations = CFileDeclarations(self)
        self.contexttable = CContextTable(self)
        self.predicatedictionary = CFilePredicateDictionary(self)
        self.interfacedictionary = InterfaceDictionary(self)
        self.assigndictionary = CFileAssignmentDictionary(self)
        self.functions = {}  # vid -> CFunction
        self.functionnames = {}  # functionname -> vid
        self.strings = {}  # string-index -> (len,string)
        self.sourcefile = None  # CSrcFile
        self.contracts = None
        self.candidate_contracts = None
        if not (self.capp.contractpath is None) and UF.has_contracts(
            self.capp.contractpath, self.name
        ):
            self.contracts = CFileContracts(self, self.capp.contractpath)
        if not (
            self.capp.candidate_contractpath is None
        ) and UF.has_candidate_contracts(self.capp.candidate_contractpath, self.name):
            self.candidate_contracts = CFileCandidateContracts(
                self, self.capp.candidate_contractpath
            )
        if self.contracts is not None:
            xnode = ET.Element("interface-dictionary")
            self.interfacedictionary.write_xml(xnode)
            UF.save_cfile_interface_dictionary(self.capp.path, self.name, xnode)
        self.gtypes = {}  # name -> CGType
        self.gcomptagdefs = {}  # key -> CGCompTag
        self.gcomptagdecls = {}  # key -> CGCompTag
        self.gvardecls = {}  # vid -> CGVarDecl
        self.gvardefs = {}  # vid -> CGVarDef

    def collect_post_assumes(self):
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self.iter_functions(lambda fn: fn.collect_post_assumes())
        self.save_interface_dictionary()
        self.save_predicate_dictionary()
        self.save_declarations()

    def save_candidate_contracts(self):
        if self.contracts is not None:
            self.contracts.save_mathml_contract()
        self.save_predicate_dictionary()
        self.save_interface_dictionary()

    def has_file_contracts(self):
        return not (self.contracts is None)

    def has_file_candidate_contracts(self):
        return not (self.candidate_contracts is None)

    def has_function_contract(self, name):
        return (not (self.contracts is None)) and (
            self.contracts.has_function_contract(name)
        )

    def get_function_contract(self, name):
        if not (self.contracts is None):
            return self.contracts.get_function_contract(name)

    def get_max_functionname_length(self):
        if len(self.functionnames) > 0:
            return max([len(x) for x in self.functionnames])
        else:
            return 10

    def get_source_line(self, n):
        self._initialize_source()
        if self.sourcefile is not None:
            return self.sourcefile.get_line(n)

    def reinitialize_tables(self):
        self.declarations.initialize()
        self.contexttable.initialize()
        self.predicatedictionary.initialize(force=True)
        self.interfacedictionary.initialize()
        self.iter_functions(lambda f: f.reinitialize_tables())

    def is_struct(self, ckey):
        return self.declarations.is_struct(ckey)

    def get_structname(self, ckey):
        return self.declarations.get_structname(ckey)

    def get_function_names(self):
        self._initialize_functions()
        return self.functionnames.keys()

    def has_function_by_name(self, fname):
        self._initialize_functions()
        return fname in self.functionnames

    def get_function_by_name(self, fname):
        self._initialize_functions()
        if fname in self.functionnames:
            vid = self.functionnames[fname]
            return self.functions[vid]
        else:
            raise UF.CFunctionNotFoundException(
                self, fname, list(self.functionnames.keys())
            )

    def get_function_by_index(self, index):
        self._initialize_functions()
        index = int(index)
        if index in self.functions:
            return self.functions[index]
        else:
            print("Unable to find function with global vid " + str(index))
            # raise FunctionMissingError('Unable to find function with global vid ' + str(index))

    def has_function_by_index(self, index):
        self._initialize_functions()
        return index in self.functions

    def get_functions(self):
        self._initialize_functions()
        return self.functions.values()

    def iter_functions(self, f):
        for fn in self.get_functions():
            f(fn)

    # returns function name -> list of strings
    def get_strings(self):
        result = {}

        def f(fn):
            result[fn.name] = fn.get_strings()

        self.iter_functions(f)
        return result

    # returns function name -> count   (* references to variable with given
    # vid *)
    def get_variable_uses(self, vid):
        result = {}

        def f(fn):
            result[fn.name] = fn.get_variable_uses(vid)

        self.iter_functions(f)
        return result

    def get_callinstrs(self):
        result = []

        def f(fn):
            result.extend(fn.getcallinstrs())

        self.iter_functions(f)
        return result

    def reload_spos(self):
        def f(fn):
            fn.reload_spos()

        self.iter_functions(f)

    def reload_ppos(self):
        def f(fn):
            fn.reload_ppos()

        self.iter_functions(f)

    def get_ppos(self):
        result = []

        def f(fn):
            result.extend(fn.get_ppos())

        self.iter_functions(f)
        return result

    def get_line_ppos(self):
        result = {}
        fnppos = self.get_ppos()
        for fn in fnppos:
            for ppo in fnppos[fn]:
                line = ppo.getline()
                pred = ppo.get_predicate_tag()
                if line not in result:
                    result[line] = {}
                if pred not in result[line]:
                    result[line][pred] = {}
                    result[line][pred]["function"] = fn
                    result[line][pred]["ppos"] = []
                result[line][pred]["ppos"].append(ppo)
        return result

    def get_spos(self):
        result = []

        def f(fn):
            result.extend(fn.get_spos())

        self.iter_functions(f)
        return result

    def get_open_ppos(self):
        result = []

        def f(fn):
            result.extend(fn.get_open_ppos())

        self.iter_functions(f)
        return result

    def get_violations(self):
        result = []

        def f(fn):
            result.extend(fn.get_violations())

        self.iter_functions(f)
        return result

    def get_delegated(self):
        result = []

        def f(fn):
            result.extend(fn.get_delegated())

        self.iter_functions(f)
        return result

    def save_predicate_dictionary(self):
        path = self.capp.path
        xroot = UX.get_xml_header("po-dictionary", "po-dictionary")
        xnode = ET.Element("po-dictionary")
        xroot.append(xnode)
        self.predicatedictionary.write_xml(xnode)
        filename = UF.get_cfile_predicate_dictionaryname(path, self.name)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))

    def save_interface_dictionary(self):
        path = self.capp.path
        xroot = UX.get_xml_header("interface-dictionary", "interface-dictionary")
        xnode = ET.Element("interface-dictionary")
        xroot.append(xnode)
        self.interfacedictionary.write_xml(xnode)
        filename = UF.get_cfile_interface_dictionaryname(path, self.name)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))

    def save_declarations(self):
        path = self.capp.path
        xroot = UX.get_xml_header("cfile", "cfile")
        xnode = ET.Element("cfile")
        xroot.append(xnode)
        self.declarations.write_xml(xnode)
        filename = UF.get_cfile_dictionaryname(path, self.name)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))

    def save_user_assumptions(self, userdata, assumptions):
        path = self.capp.path
        xroot = UX.get_xml_header("cfile", "cfile")
        xnode = ET.Element("cfile")
        xroot.append(xnode)
        userdata.write_xml(xnode, assumptions)
        filename = UF.get_cfile_usr_filename(path, self.name)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))

    def create_contract(self, contractpath, preservesmemory=[], seed={}, ignorefns={}):
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
            fseed["functions"] if (fseed is not None) and "functions" in fseed else None
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

    def create_candidate_contract(self, contractpath):
        cnode = ET.Element("cfile")
        cnode.set("name", self.name)
        ffnode = ET.Element("functions")
        dnode = ET.Element("data-structures")
        cnode.extend([dnode, ffnode])
        for fn in self.get_functions():
            fnode = ET.Element("function")
            fnode.set("name", fn.name)
            ppnode = ET.Element("parameters")
            for fid in sorted(fn.formals, key=lambda fid: fn.formals[fid].vparam):
                pnode = ET.Element("par")
                pnode.set("name", fn.formals[fid].vname)
                pnode.set("nr", str(fn.formals[fid].vparam))
                ppnode.append(pnode)
            fnode.append(ppnode)
            fnode.append(ET.Element("postconditions"))
            fnode.append(ET.Element("data-structure-requests"))
            ffnode.append(fnode)
        UF.save_candidate_contracts_file(contractpath, self.name, cnode)

    def export_file_data(self):
        result = {}
        result["filename"] = self.name
        result["functions"] = {}
        self.iter_functions(lambda f: f.export_function_data(result["functions"]))
        return result

    def get_gtypes(self):
        self._initialize_gtypes()
        return self.gtypes

    def _initialize_gtypes(self):
        if len(self.gtypes) > 0:
            return
        for t in self.xnode.find("global-type-definitions").findall("gtype"):
            name = t.find("typeinfo").get("tname")
            self.gtypes[name] = CGType(self, t)

    def get_gcomptagdefs(self):
        self._initialize_gcomptagdefs()
        return self.gcomptagdefs

    def _initialize_gcomptagdefs(self):
        if len(self.gcomptagdefs) > 0:
            return
        for c in self.xnode.find("global-comptag-definitions").findall("gcomptag"):
            key = int(c.find("compinfo").get("ckey"))
            self.gcomptagdefs[key] = CGCompTag(self, c)

    def get_gcomptagdecls(self):
        self._initialize_gcomptagdecls()
        return self.gcomptagdecls

    def _initialize_gcomptagdecls(self):
        if len(self.gcomptagdecls) > 0:
            return
        for c in self.xnode.find("global-comptag-declarations").findall("gcomptagdecl"):
            key = int(c.find("compinfo").get("ckey"))
            self.gcomptagdecls[key] = CGCompTag(self, c)

    def _initialize_genumtagdefs(self):
        if len(self.genumtagdefs) > 0:
            return
        for e in self.xnode.find("global-enumtag-definitions").findall("genumtag"):
            name = e.find("enuminfo").get("ename")
            self.genumtagdefs[name] = CGEnumTag(self, e)

    def _initialize_genumtagdecls(self):
        if len(self.genumtagdecls) > 0:
            return
        for e in self.xnode.find("global-enumtag-declarations").findall("genumtag"):
            name = e.find("enuminfo").get("ename")
            self.genumtagdecls[name] = CGEnumTag(self, e)

    def get_gvardecls(self):
        self._initialize_gvardecls()
        return self.gvardecls

    def _initialize_gvardecls(self):
        if len(self.gvardecls) > 0:
            return
        for v in self.xnode.find("global-var-declarations").findall("gvardecl"):
            vid = int(v.find("varinfo").get("vid"))
            self.gvardecls[vid] = CGVarDecl(self, v)

    def get_gvardefs(self):
        self._initialize_gvardefs()
        return self.gvardefs

    def _initialize_gvardefs(self):
        if len(self.gvardefs) > 0:
            return
        for v in self.xnode.find("global-var-definitions").findall("gvar"):
            vid = int(v.find("varinfo").get("vid"))
            self.gvardefs[vid] = CGVarDef(self, v)

    def get_gfunctions(self):
        self._initialize_gfunctions()
        return self.declarations.gfunctions

    def _initialize_gfunctions(self):
        if len(self.declarations.gfunctions) > 0:
            return
        for f in self.xnode.find("functions").findall("gfun"):
            vid = int(f.find("svar").get("vid"))
            self.declarations.gfunctions[vid] = CGFunction(self, f)

    def _initialize_function(self, vid):
        if vid in self.functions:
            return
        fname = self.declarations.get_gfunction(vid).get_name()
        f = UF.get_cfun_xnode(self.capp.path, self.name, fname)
        if f is not None:
            self.functions[vid] = CFunction(self, f)
            self.functionnames[fname] = vid

    def _initialize_functions(self):
        self._initialize_gfunctions()
        for vid in self.declarations.gfunctions.keys():
            self._initialize_function(vid)

    def _initialize_source(self):
        if self.sourcefile is None:
            self.sourcefile = self.capp.get_srcfile(self.name)
