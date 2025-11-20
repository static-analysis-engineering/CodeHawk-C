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
"""Main access point for a c function."""

import xml.etree.ElementTree as ET

from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING


from chc.api.CFunctionApi import CFunctionApi

from chc.app.CFunDeclarations import CFunDeclarations
from chc.app.CInstr import CCallInstr
from chc.app.CFunctionReturnSite import CFunctionReturnSite
from chc.app.CLocation import CLocation
from chc.app.CStmt import CFunctionBody
from chc.app.IndexManager import FileVarReference

from chc.invariants.CFunVarDictionary import CFunVarDictionary
from chc.invariants.CFunInvDictionary import CFunInvDictionary
from chc.invariants.CFunInvariantTable import CFunInvariantTable
from chc.invariants.CInvariantFact import CInvariantFact

from chc.proof.CFunPODictionary import CFunPODictionary
from chc.proof.CFunctionCallsiteSPOs import CFunctionCallsiteSPOs
from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPPO import CFunctionPPO
from chc.proof.CFunctionProofs import CFunctionProofs
from chc.proof.CFunctionSPOs import CFunctionSPOs

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.api.CFunctionContract import CFunctionContract
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.app.CApplication import CApplication
    from chc.app.CDictionary import CDictionary
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.COffset import COffset
    from chc.app.CTyp import CTyp
    from chc.app.CVarInfo import CVarInfo


class CandidateOutputParameter:

    def __init__(
            self,
            cfun: "CFunction",
            cvar: "CVarInfo",
            offsets: List["COffset"]) -> None:
        self._cfun = cfun
        self._cvar = cvar
        self._offsets = offsets

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def parameter(self) -> "CVarInfo":
        return self._cvar

    @property
    def offsets(self) -> List["COffset"]:
        return self._offsets

    def __str__(self) -> str:
        return (
            self.parameter.vname + "[" + ", ".join(str(o) for o in self.offsets) + "]")


class CAnalysisInfo:

    def __init__(self, xnode: Optional[ET.Element], cfun: "CFunction") -> None:
        self._xnode = xnode
        self._cfun = cfun

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cdictionary(self) -> "CDictionary":
        return self.cfun.cdictionary

    @property
    def cfiledecls(self) -> "CFileDeclarations":
        return self.cfun.cfiledecls

    @property
    def analysis(self) -> str:
        if self._xnode is None:
            return "undefined-behavior"
        else:
            return self._xnode.get("name", "unknown")

    @property
    def candidate_parameters(self) -> List[CandidateOutputParameter]:
        result: List[CandidateOutputParameter] = []
        if self._xnode is not None:
            if self.analysis == "output-parameters":
                xparams = self._xnode.find("candidate-parameters")
                if xparams is not None:
                    xparamlist = xparams.findall("vinfo")
                    for xparam in xparamlist:
                        xid = int(xparam.get("xid", "-1"))
                        if xid > 0:
                            vinfo = self.cfiledecls.get_varinfo(xid)
                            xoffsets = xparam.get("offsets", "")
                            if xoffsets is not None:
                                offsets = list(
                                    self.cdictionary.get_offset(int(i))
                                    for i in xoffsets.split(","))

                            result.append(CandidateOutputParameter(
                                self.cfun, vinfo, offsets))
        return result

    def __str__(self) -> str:
        return ", ".join(str(vinfo) for vinfo in self.candidate_parameters)


class CFunction:
    """Function implementation."""

    def __init__(self, cfile: "CFile", xnode: ET.Element, fname: str) -> None:
        self.xnode = xnode
        self._cfile = cfile
        self._name = fname
        self._cfundecls: Optional[CFunDeclarations] = None
        self._svar: Optional["CVarInfo"] = None
        self._formals: Dict[int, "CVarInfo"] = {}  # vid -> CVarInfo
        self._locals: Dict[int, "CVarInfo"] = {}  # vid -> CVarInfo
        self._sbody: Optional[CFunctionBody] = None
        self._returnsites: Optional[List[CFunctionReturnSite]] = None
        self._podictionary: Optional[CFunPODictionary] = None
        self._api: Optional[CFunctionApi] = None
        self._proofs: Optional[CFunctionProofs] = None
        self._vard: Optional[CFunVarDictionary] = None
        self._invd: Optional[CFunInvDictionary] = None
        self._invarianttable: Optional[CFunInvariantTable] = None
        self._analysisinfo: Optional[CAnalysisInfo] = None

    def xmsg(self, txt: str) -> str:
        return "Function " + self.name + ": " + txt

    @property
    def name(self) -> str:
        return self._name

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    @property
    def targetpath(self) -> str:
        return self.cfile.targetpath

    @property
    def projectname(self) -> str:
        return self.cfile.projectname

    @property
    def cfilepath(self) -> Optional[str]:
        return self.cfile.cfilepath

    @property
    def cfilename(self) -> str:
        return self.cfile.cfilename

    @property
    def formals(self) -> Dict[int, "CVarInfo"]:
        if len(self._formals) == 0:
            for (vid, vinfo) in self.cfundecls.varinfos.items():
                if vinfo.is_param:
                    self._formals[vid] = vinfo
        return self._formals

    @property
    def locals(self) -> Dict[int, "CVarInfo"]:
        if len(self._locals) == 0:
            for (vid, vinfo) in self.cfundecls.varinfos.items():
                if not vinfo.is_param:
                    self._locals[vid] = vinfo
        return self._locals

    @property
    def ftype(self) -> "CTyp":
        return self.svar.vtype

    @property
    def cfiledecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def cdictionary(self) -> "CDictionary":
        return self.cfile.dictionary

    @property
    def interfacedictionary(self) -> "InterfaceDictionary":
        return self.cfile.interfacedictionary

    @property
    def api(self) -> CFunctionApi:
        if self._api is None:
            axnode = UF.get_api_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if axnode is not None:
                apinode = axnode.find("api")
                if apinode is not None:
                    self._api = CFunctionApi(self, apinode)
                else:
                    raise UF.CHCError(self.xmsg("api file has no api node"))
            else:
                raise UF.CHCError(self.xmsg("api file not found"))
        return self._api

    def has_outstanding_api_requests(self) -> bool:
        return self.api.has_outstanding_requests()

    @property
    def svar(self) -> "CVarInfo":
        if self._svar is None:
            xsvar = self.xnode.find("svar")
            if xsvar is not None:
                xivinfo = xsvar.get("ivinfo")
                if xivinfo is not None:
                    self._svar = self.cfiledecls.get_varinfo(int(xivinfo))
                else:
                    raise UF.CHCError(
                        self.xmsg(
                            "ivinfo attribute "
                            + "is missing from svar element in cfun file"))
            else:
                raise UF.CHCError(
                    self.xmsg("svar element is missing from cfun file"))
        return self._svar

    @property
    def sbody(self) -> CFunctionBody:
        if self._sbody is None:
            xsbody = self.xnode.find("sbody")
            if xsbody is not None:
                self._sbody = CFunctionBody(self, xsbody)
            else:
                raise UF.CHCError(
                    self.xmsg("sbody element is missing from cfun file"))
        return self._sbody

    @property
    def cfundecls(self) -> CFunDeclarations:
        if self._cfundecls is None:
            dxnode = self.xnode.find("declarations")
            if dxnode is not None:
                self._cfundecls = CFunDeclarations(self, dxnode)
            else:
                raise UF.CHCError(
                    self.xmsg("declarations are missing from cfun file"))
        return self._cfundecls

    @property
    def vardictionary(self) -> CFunVarDictionary:
        if self._vard is None:
            vxnode = UF.get_vars_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if vxnode is not None:
                xvard = vxnode.find("var-dictionary")
                if xvard is not None:
                    self._vard = CFunVarDictionary(self, xvard)
                else:
                    raise UF.CHCError(
                        self.xmsg("var-dictionary missing from cfun-vars file"))
            else:
                raise UF.CHCError(
                    self.xmsg(
                        "var-dictionary file not found for function "
                        + self.name
                        + " in file "
                        + self.cfile.name))
        return self._vard

    @property
    def invdictionary(self) -> CFunInvDictionary:
        if self._invd is None:
            ixnode = UF.get_invs_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if ixnode is not None:
                xinvs = ixnode.find("inv-dictionary")
                if xinvs is not None:
                    self._invd = CFunInvDictionary(self, xinvs)
                else:
                    raise UF.CHCError(
                        self.xmsg("inv-dictionary missing from cfun-invs file"))
            else:
                raise UF.CHCError(
                    self.xmsg("inv-dictionary file not found"))
        return self._invd

    @property
    def invarianttable(self) -> CFunInvariantTable:
        if self._invarianttable is None:
            ixnode = UF.get_invs_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if ixnode is not None:
                xinvs = ixnode.find("location-invariants")
                if xinvs is not None:
                    self._invarianttable = CFunInvariantTable(self, xinvs)
                else:
                    raise UF.CHCError(
                        self.xmsg("inv-table missing from cfun-invs file"))
            else:
                raise UF.CHCError(
                    self.xmsg("inv-dictionary file not found"))
        return self._invarianttable

    @property
    def podictionary(self) -> CFunPODictionary:
        if self._podictionary is None:
            pxnode = UF.get_pod_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if pxnode is None:
                raise UF.CHCError(self.xmsg("pod file not found"))
            self._podictionary = CFunPODictionary(self, pxnode)
        return self._podictionary

    @property
    def returnsites(self) -> List[CFunctionReturnSite]:
        if self._returnsites is None:
            self._returnsites = []
            xsponode = UF.get_spo_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if xsponode is None:
                raise UF.CHCError(self.xmsg("spo file is missing"))
            xxsponode = xsponode.find("spos")
            if xxsponode is None:
                raise UF.CHCError(self.xmsg("spo file has no spos element"))
            xreturnsites = xxsponode.find("returnsites")
            if xreturnsites is None:
                raise UF.CHCError(
                    self.xmsg("spo file has no returnsites element"))
            for xreturnsite in xreturnsites.findall("rs"):
                self._returnsites.append(CFunctionReturnSite(self, xreturnsite))
        return self._returnsites

    def get_returnsite(
            self, ctxtid: int) -> Optional[CFunctionReturnSite]:
        for rs in self.returnsites:
            if rs.context.index == ctxtid:
                return rs
        return None

    @property
    def proofs(self) -> CFunctionProofs:
        if self._proofs is None:
            xpponode = UF.get_ppo_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if xpponode is None:
                raise UF.CHCError(self.xmsg("ppo file is missing"))
            xxpponode = xpponode.find("ppos")
            if xxpponode is None:
                raise UF.CHCError(self.xmsg("_ppo file has no ppos element"))
            xsponode = UF.get_spo_xnode(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name)
            if xsponode is None:
                raise UF.CHCError(self.xmsg("spo file is missing"))
            xxsponode = xsponode.find("spos")
            if xxsponode is None:
                raise UF.CHCError(self.xmsg("spo file has no spos element"))
            self._proofs = CFunctionProofs(self, xxpponode, xxsponode)
        return self._proofs

    @property
    def analysis_info(self) -> CAnalysisInfo:
        if self._analysisinfo is None:
            if UF.has_ppo_file(
                    self.targetpath,
                    self.projectname,
                    self.cfilepath,
                    self.cfilename,
                    self.name):
                xpponode = UF.get_ppo_xnode(
                    self.targetpath,
                    self.projectname,
                    self.cfilepath,
                    self.cfilename,
                    self.name)
                if xpponode is not None:
                    self._analysisinfo = (
                        CAnalysisInfo(xpponode.find("analysis-info"), self))
                else:
                    self._analysisinfo = CAnalysisInfo(None, self)
            else:
                self._analysisinfo = CAnalysisInfo(None, self)
        return self._analysisinfo

    def reinitialize_tables(self) -> None:
        self._api = None
        self._podictionary = None
        self._vardictionary = None
        self._proofs = None

    def get_formal_vid(self, name: str) -> int:
        for v in self.formals:
            if self.formals[v].vname == name:
                return v
        else:
            raise UF.CHCError(
                "Formals: " + ",".join([str(v) for v in self.formals.values()]))

    def get_variable_vid(self, vname: str) -> int:
        for v in self.formals:
            if self.formals[v].vname == vname:
                return self.formals[v].vid
        for v in self.locals:
            if self.locals[v].vname == vname:
                return self.locals[v].vid
        raise UF.CHCError("Could not find vid for variable \"" + vname + "\"")

    def has_variable_vid(self, vname: str) -> bool:
        for v in self.formals:
            if self.formals[v].vname == vname:
                return True
        for v in self.locals:
            if self.locals[v].vname == vname:
                return True
        return False

    @property
    def strings(self) -> List[str]:
        return self.sbody.strings

    # returns the number of occurrences of vid in expressions and lhs
    def get_variable_uses(self, vid: int) -> int:
        return self.sbody.get_variable_uses(vid)

    def has_function_contract(self) -> bool:
        return self.cfile.has_function_contract(self.name)

    def get_function_contract(self) -> Optional["CFunctionContract"]:
        if self.has_function_contract():
            return self.cfile.get_function_contract(self.name)
        return None

    def selfignore(self):
        return self.has_function_contract() and self.get_function_contract().ignore

    def iter_ppos(self, f: Callable[[CFunctionPPO], None]) -> None:
        self.proofs.iter_ppos(f)

    def get_ppo(self, index: int) -> CFunctionPPO:
        return self.proofs.get_ppo(index)

    def get_spo(self, index: int) -> CFunctionPO:
        return self.proofs.get_spo(index)

    def iter_callsites(self, f: Callable[[CFunctionCallsiteSPOs], None]) -> None:
        self.proofs.iter_callsites(f)

    def get_vid(self) -> int:
        return self.svar.vid

    def get_api(self) -> CFunctionApi:
        return self.api

    def has_location(self) -> bool:
        return self.svar.vdecl is not None

    def get_location(self) -> CLocation:
        if self.svar.vdecl is not None:
            return self.svar.vdecl
        else:
            raise UF.CHCError(f"Function {self.name} does not have a location")

    def has_source_code_file(self) -> bool:
        return self.has_location()

    def get_source_code_file(self) -> str:
        if self.has_location():
            return self.get_location().file
        else:
            raise UF.CHCError(f"Function {self.name} does not have source file")

    def has_line_number(self) -> bool:
        if self.has_source_code_file():
            srcfile = self.get_source_code_file()
            return self.cfile.cfilename + ".c" == srcfile
        else:
            return False

    def get_line_number(self) -> int:
        if self.has_line_number():
            return self.get_location().line
        else:
            raise UF.CHCError(f"Function {self.name} does not have a line number")

    def get_formals(self) -> List["CVarInfo"]:
        return list(self.formals.values())

    def get_locals(self) -> List["CVarInfo"]:
        return list(self.locals.values())

    @property
    def block_count(self) -> int:
        return self.sbody.block_count

    @property
    def stmt_count(self) -> int:
        return self.sbody.stmt_count

    @property
    def instr_count(self) -> int:
        return self.sbody.instr_count

    @property
    def call_instrs(self) -> List[CCallInstr]:
        return self.sbody.call_instrs

    def violates_contract_conditions(self) -> bool:
        return len(self.api.contract_condition_failures) > 0

    def get_contract_condition_violations(self) -> List[Tuple[str, str]]:
        return self.api.contract_condition_failures

    def update_spos(self) -> None:
        if self.selfignore():
            return
        try:
            self.proofs.update_spos()
        except UF.CHCError as e:
            chklogger.logger.error(str(e))

    def collect_post_assumes(self) -> None:
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self.proofs.collect_post_assumes()
        self.save_spos()

    def distribute_post_guarantees(self) -> None:
        self.proofs.distribute_post_guarantees()

    def collect_post(self) -> None:
        """Add postcondition requests to the contract of the callee"""
        for r in self.api.postcondition_requests.values():
            tgtvid = r.callee.vid
            filevar = FileVarReference(self.cfile.index, tgtvid)
            tgtfun = self.capp.resolve_vid_function(filevar)
            if tgtfun is None:
                chklogger.logger.warning(
                    ("No function found to register post request in function: "
                     + "%s:%s"),
                    self.cfile.name, self.name)
            else:
                tgtcfile = tgtfun.cfile
                if tgtfun.cfile.has_function_contract(tgtfun.name):
                    tgtifx = tgtfun.cfile.interfacedictionary
                    tgtpostconditionix = tgtifx.index_xpredicate(r.postcondition)
                    tgtpostcondition = tgtifx.get_xpredicate(tgtpostconditionix)
                    cfuncontract = tgtcfile.get_function_contract(tgtfun.name)
                    if cfuncontract is not None:
                        cfuncontract.add_postrequest(tgtpostcondition)

    def save_spos(self) -> None:
        try:
            self.proofs.save_spos()
        except UF.CHCError as e:
            chklogger.logger.error(str(e))

    def save_pod(self) -> None:
        cnode = ET.Element("function")
        cnode.set("name", self.name)
        try:
            self.podictionary.write_xml(cnode)
            UF.save_pod_file(
                self.targetpath,
                self.projectname,
                self.cfilepath,
                self.cfilename,
                self.name,
                cnode)
        except UF.CHCError as e:
            chklogger.logger.error(str(e))

    def reload_ppos(self) -> None:
        self.proofs.reload_ppos()

    def reload_spos(self) -> None:
        self.proofs.reload_spos()

    def get_ppos(self) -> List[CFunctionPO]:
        return self.proofs.ppolist

    def get_spos(self) -> List[CFunctionPO]:
        return self.proofs.spolist

    def get_open_ppos(self) -> List[CFunctionPO]:
        return self.proofs.open_ppos

    def get_open_spos(self) -> List[CFunctionPO]:
        return self.proofs.open_spos

    def get_ppos_violated(self) -> List[CFunctionPO]:
        return self.proofs.ppos_violated

    def get_spo_violations(self) -> List[CFunctionPO]:
        return self.proofs.get_spo_violations()

    def get_ppos_delegated(self) -> List[CFunctionPO]:
        return self.proofs.ppos_delegated
