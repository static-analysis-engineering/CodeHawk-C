# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, TYPE_CHECKING


from chc.api.CFunctionApi import CFunctionApi


from chc.app.CLocation import CLocation
from chc.app.CFunDeclarations import CFunDeclarations
from chc.app.CInstr import CCallInstr
from chc.app.CStmt import CFunctionBody
from chc.invariants.CFunVarDictionary import CFunVarDictionary
from chc.invariants.CFunInvDictionary import CFunInvDictionary
from chc.invariants.CFunInvariantTable import CFunInvariantTable
from chc.invariants.CInvariantFact import CInvariantFact

from chc.proof.CFunPODictionary import CFunPODictionary
from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPPO import CFunctionPPO
from chc.proof.CFunctionPPOs import CFunctionPPOs
from chc.proof.CFunctionProofs import CFunctionProofs
from chc.proof.CFunctionSPOs import CFunctionSPOs

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CTyp import CTyp
    from chc.app.CVarInfo import CVarInfo
    

class CFunction(object):
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
        self._podictionary: Optional[CFunPODictionary] = None
        self._api: Optional[CFunctionApi] = None
        self._proofs: Optional[CFunctionProofs] = None
        self._vard: Optional[CFunVarDictionary] = None
        self._invd: Optional[CFunInvDictionary] = None
        self._invarianttable: Optional[CFunInvariantTable] = None
        self._initialize()

    def xmsg(self, txt: str) -> str:
        return "Function " + self.name + ": " + txt

    @property
    def name(self) -> str:
        return self._name

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
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def cfiledecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    @property
    def interfacedictionary(self) -> "InterfaceDictionary":
        return self.cfile.interfacedictionary

    @property
    def api(self) -> CFunctionApi:
        if self._api is None:
            axnode = UF.get_api_xnode(
                self.capp.path, self.cfile.name, self.name)
            if axnode is not None:
                apinode = axnode.find("api")
                if apinode is not None:
                    self._api = CFunctionApi(self, apinode)
                else:
                    raise UF.CHCError(self.xmsg("api file has no api node"))
            else:
                raise UF.CHCError(self.xmsg("api file not found"))
        return self._api

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
                self.capp.path, self.cfile.name, self.name)
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
                self.capp.path, self.cfile.name, self.name)
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
                self.capp.path, self.cfile.name, self.name)
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
                self.capp.path, self.cfile.name, self.name)
            if pxnode is None:
                raise UF.CHCError(self.xmsg("pod file not found"))
            self._podictionary = CFunPODictionary(self, pxnode)
        return self._podictionary

    @property
    def proofs(self) -> CFunctionProofs:
        if self._proofs is None:
            xpponode = UF.get_ppo_xnode(
                self.capp.path, self.cfile.name, self.name)
            if xpponode is None:
                raise UF.CHCError(self.xmsg("ppo file is missing"))
            xxpponode = xpponode.find("ppos")
            if xxpponode is None:
                raise UF.CHCError(self.xmsg("_ppo file has no ppos element"))
            xsponode = UF.get_spo_xnode(
                self.capp.path, self.cfile.name, self.name)
            if xsponode is None:
                raise UF.CHCError(self.xmsg("spo file is missing"))
            xxsponode = xsponode.find("spos")
            if xxsponode is None:
                raise UF.CHCError(self.xmsg("_spo file has no spos element"))
            self._proofs = CFunctionProofs(self, xxpponode, xxsponode)
        return self._proofs

    def reinitialize_tables(self) -> None:
        self._api = None
        self._podictionary = None
        self._vardictionary = None

    '''
    def export_function_data(self, result: Dict[str, object]) -> None:
        fnresult: Dict[str, object] = {}
        fnresult["type"] = self.ftype.to_idict()
        fnresult["typestr"] = str(self.ftype)
        fnresult["stmt-count"] = self.get_stmt_count()
        fnresult["instr-count"] = self.get_instr_count()
        fnresult["call-instrs"] = [i.to_dict() for i in self.get_call_instrs()]
        fnresult["call-instrs-strs"] = [str(i) for i in self.get_call_instrs()]
        result[self.name] = fnresult
    '''

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

    @property
    def strings(self) -> List[str]:
        return self.sbody.strings

    # returns the number of occurrences of vid in expressions and lhs
    def get_variable_uses(self, vid: int) -> int:
        return self.sbody.get_variable_uses(vid)

    def has_function_contract(self) -> bool:
        return self.cfile.has_function_contract(self.name)

    def get_function_contract(self):
        if self.has_function_contract():
            return self.cfile.get_function_contract(self.name)

    def selfignore(self):
        return self.has_function_contract() and self.get_function_contract().ignore

    def iter_ppos(self, f):
        self.proofs.iter_ppos(f)

    def get_ppo(self, index):
        return self.proofs.get_ppo(index)

    def get_spo(self, index):
        return self.proofs.get_spo(index)

    def iter_callsites(self, f):
        self.proofs.iter_callsites(f)

    def get_vid(self):
        return self.svar.get_vid()

    def get_api(self) -> CFunctionApi:
        return self.api

    def get_location(self):
        return self.svar.vdecl

    def get_source_code_file(self) -> str:
        return self.get_location().file

    def get_line_number(self) -> int:
        if self.cfile.name + ".c" == self.get_source_code_file():
            return self.get_location().line
        raise Exception("No relevant line number")

    def get_formals(self):
        return self.formals.values()

    def get_locals(self):
        return self.locals.values()

    '''
    def get_body(self) -> CFunctionBody:
        return self.body
    '''

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

    def get_invariants(self):
        self._readinvariants()
        return self.invariants

    def violates_contract_conditions(self):
        return len(self.api.contractconditionfailures) > 0

    def get_contract_condition_violations(self):
        return self.api.contractconditionfailures

    def get_proofs(self):
        return self.proofs

    def get_callsite_spos(self):
        return self.proofs.getspos

    def update_spos(self) -> None:
        if self.selfignore():
            return
        self.proofs.update_spos()

    def collect_post_assumes(self) -> None:
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self.proofs.collect_post_assumes()
        self.save_spos()

    def distribute_post_guarantees(self):
        self.proofs.distribute_post_guarantees()

    def collect_post(self) -> None:
        """Add postcondition requests to the contract of the callee"""
        for r in self.api.postcondition_requests.values():
            tgtfid = r.callee.vid
            tgtfun = self.capp.resolve_vid_function(self.cfile.index, tgtfid)
            if tgtfun is None:
                print(
                    "No function found to register post request in function "
                    + self.cfile.name
                    + ":"
                    + self.name
                )
            else:
                tgtcfile = tgtfun.cfile
                if tgtfun.cfile.has_function_contract(tgtfun.name):
                    tgtifx = tgtfun.cfile.interfacedictionary
                    tgtpostconditionix = tgtifx.index_xpredicate(r.postcondition)
                    tgtpostcondition = tgtifx.get_xpredicate(tgtpostconditionix)
                    cfuncontract = tgtcfile.get_function_contract(tgtfun.name)
                    cfuncontract.add_postrequest(tgtpostcondition)

    def save_spos(self) -> None:
        self.proofs.save_spos()

    def save_pod(self) -> None:
        cnode = ET.Element("function")
        cnode.set("name", self.name)
        self.podictionary.write_xml(cnode)
        UF.save_pod_file(self.cfile.capp.path, self.cfile.name, self.name, cnode)

    def reload_ppos(self) -> None:
        self.proofs.reload_ppos()

    def reload_spos(self) -> None:
        self.proofs.reload_spos()

    def get_ppos(self) -> List[CFunctionPPO]:
        return self.proofs.ppolist

    def get_spos(self) -> List[CFunctionPO]:
        return self.proofs.spolist

    def get_open_ppos(self) -> List[CFunctionPPO]:
        return self.proofs.open_ppos

    def get_open_spos(self) -> List[CFunctionPO]:
        return self.proofs.open_spos

    def get_violations(self):
        return self.proofs.get_violations()

    def get_spo_violations(self):
        return self.proofs.get_spo_violations()

    def get_delegated(self):
        return self.proofs.get_delegated()

    def _initialize(self) -> None:
        pass
    '''
        for v in self.cfundecls.get_formals():
            self.formals[v.get_vid()] = v
        for v in self.cfundecls.get_locals():
            self.locals[v.get_vid()] = v
        self.vard.initialize()
        self.invtable.initialize()
    '''
