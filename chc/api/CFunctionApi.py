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

import xml.etree.ElementTree as ET

from typing import Callable, cast, Dict, List, Optional, Tuple, TYPE_CHECKING

from chc.api.ApiAssumption import ApiAssumption
from chc.api.ContractAssumption import ContractAssumption
from chc.api.GlobalAssumption import GlobalAssumption
from chc.api.PostConditionRequest import PostConditionRequest

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.XPredicate import XPredicate
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CTyp import CFunArg, CTypFun
    from chc.app.CFunction import CFunction

memory_free_functions = ["free", "realloc"]


class CFunctionApi:

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        self.xnode = xnode     # api node in api file
        self._cfun = cfun
        # self.parameters = {}  # nr -> (vid,vname)
        self._api_assumptions: Optional[Dict[int, ApiAssumption]] = None
        self._contract_assumptions: Optional[  # (callee,index) -> ContractAssumption
            Dict[Tuple[int, int], ContractAssumption]] = None
        self._global_assumption_requests: Optional[Dict[int, GlobalAssumption]] = None
        self._postcondition_requests: Optional[Dict[int, PostConditionRequest]] = None
        self._postcondition_guarantees: Optional[Dict[int, "XPredicate"]] = None
        self._library_calls: Optional[Dict[Tuple[str, str], int]] = None  # (header,fname) -> count
        self._contract_condition_failures: Optional[List[Tuple[str, str]]] = None
        self._missing_summaries: Optional[List[str]] = None

    def xmsg(self, msg: str) -> str:
        return "Function api of " + self.cfun.name + ": " + msg

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def interfacedictionary(self) -> "InterfaceDictionary":
        return self.cfile.interfacedictionary

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    def has_outstanding_postcondition_requests(self) -> bool:
        return (
            sum([len(r.get_open_ppos())
                 for r in self.postcondition_requests.values()])) > 0

    @property
    def missing_summaries(self) -> List[str]:
        if self._missing_summaries is None:
            self._missing_summaries = []
            xmsnode = self.xnode.find("missing-summaries")
            if xmsnode is not None:
                for x in xmsnode.findall("ms"):
                    msname = x.get("n")
                    if msname is not None:
                        self._missing_summaries.append(msname)
        return self._missing_summaries

    def has_missing_summaries(self) -> bool:
        return len(self.missing_summaries) > 0

    def has_outstanding_global_requests(self) -> bool:
        return (
            sum([len(r.get_open_ppos())
                 for r in self.global_assumption_requests.values()])) > 0

    def has_outstanding_requests(self) -> bool:
        return (
            self.has_outstanding_postcondition_requests()
            or self.has_outstanding_global_requests())

    @property
    def api_assumptions(self) -> Dict[int, ApiAssumption]:
        if self._api_assumptions is None:
            self._api_assumptions = {}
            xass = self.xnode.find("api-assumptions")
            if xass is not None:
                for x in xass.findall("aa"):
                    p = self.cfile.predicatedictionary.read_xml_predicate(x)
                    id = p.index
                    ppos = IT.get_attribute_int_list(x, "ppos")
                    spos = IT.get_attribute_int_list(x, "spos")
                    isglobal = x.get("global", "no") == "yes"
                    isfile = x.get("file", "no") == "yes"
                    apiass = ApiAssumption(
                        self, id, p, ppos, spos, isglobal=isglobal, isfile=isfile)
                    self._api_assumptions[id] = apiass
        return self._api_assumptions

    @property
    def contract_assumptions(self) -> Dict[Tuple[int, int], ContractAssumption]:
        if self._contract_assumptions is None:
            self._contract_assumptions = {}
            xcass = self.xnode.find("contract-assumptions")
            if xcass is not None:
                for x in xcass.findall("ca"):
                    p = self.cfile.interfacedictionary.read_xml_postcondition(x)
                    id = p.index
                    callee = int(x.get("callee", "-1"))
                    ppos = IT.get_attribute_int_list(x, "ppos")
                    spos = IT.get_attribute_int_list(x, "spos")
                    cass = ContractAssumption(self, id, callee, p, ppos, spos)
                    self._contract_assumptions[(callee, id)] = cass
        return self._contract_assumptions

    @property
    def postcondition_requests(self) -> Dict[int, PostConditionRequest]:
        if self._postcondition_requests is None:
            self._postcondition_requests = {}
            xprs = self.xnode.find("postcondition-requests")
            if xprs is not None:
                for x in xprs.findall("rr"):
                    pc = self.interfacedictionary.read_xml_postrequest(x)
                    ppos = IT.get_attribute_int_list(x, "ppos")
                    spos = IT.get_attribute_int_list(x, "spos")
                    request = PostConditionRequest(self, pc, ppos, spos)
                    self._postcondition_requests[pc.index] = request
        return self._postcondition_requests

    @property
    def postcondition_guarantees(self) -> Dict[int, "XPredicate"]:
        if self._postcondition_guarantees is None:
            self._postcondition_guarantees = {}
            xpgs = self.xnode.find("postcondition-guarantees")
            if xpgs is not None:
                for x in xpgs.findall("gg"):
                    p = self.interfacedictionary.read_xml_postcondition(x)
                    self._postcondition_guarantees[p.index] = p
        return self._postcondition_guarantees

    @property
    def global_assumption_requests(self) -> Dict[int, GlobalAssumption]:
        if self._global_assumption_requests is None:
            self._global_assumption_requests = {}
            xgar = self.xnode.find("global-assumption-requests")
            if xgar is not None:
                for x in xgar.findall("hh"):
                    xid = x.get("ipr")
                    if xid is None:
                        raise UF.CHCError(
                            self.xmsg(
                                "ipr attribute missing in global-assumption-requests"))
                    id = int(xid)
                    p = self.cfile.interfacedictionary.get_xpredicate(id)
                    ppos = IT.get_attribute_int_list(x, "ppos")
                    spos = IT.get_attribute_int_list(x, "spos")
                    gas = GlobalAssumption(self, id, p, ppos, spos)
                    self._global_assumption_requests[id] = gas
        return self._global_assumption_requests

    @property
    def library_calls(self) -> Dict[Tuple[str, str], int]:
        if self._library_calls is None:
            self._library_calls = {}
            xlcs = self.xnode.find("library-calls")
            if xlcs is not None:
                for x in xlcs.findall("lc"):
                    header = x.get("h")
                    fname = x.get("f")
                    count = x.get("c")
                    if (
                            (header is not None)
                            and (fname is not None)
                            and (count is not None)):
                            self._library_calls[(header, fname)] = int(count)
        return self._library_calls

    @property
    def contract_condition_failures(self) -> List[Tuple[str, str]]:
        if self._contract_condition_failures is None:
            self._contract_condition_failures = []
            xfcs = self.xnode.find("contract-condition-failures")
            if xfcs is not None:
                for x in xfcs.findall("failure"):
                    cfname = x.get("name")
                    cfdesc = x.get("desc")
                    if cfname is not None and cfdesc is not None:
                        self._contract_condition_failures.append((cfname, cfdesc))
        return self._contract_condition_failures

    @property
    def parameters(self) -> List["CFunArg"]:
        ftype = cast("CTypFun", self.cfun.ftype)
        if ftype.funargs is not None:
            return ftype.funargs.arguments
        else:
            raise UF.CHCError("Function signature without parameters")
        # return self.cfun.ftype.get_args().get_args()

    @property
    def formal_vids(self) -> List[int]:
        return [self.cfun.get_formal_vid(p.name) for p in self.parameters]

    def iter_api_assumptions(self, f: Callable[[ApiAssumption], None]) -> None:
        for a in self.api_assumptions.values():
            f(a)

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("Api:")
        lines.append("  parameters:")
        for n in self.parameters:
            lines.append("    " + str(n).rjust(2))
        if len(self.contract_condition_failures) > 0:
            lines.append("\n  CONTRACT CONDITION FAILURE ")
            for (name, desc) in self.contract_condition_failures:
                lines.append("     " + name + ":" + desc)
        if len(self.global_assumption_requests) > 0:
            lines.append("\n  global assumption requests")
            for g in self.global_assumption_requests.values():
                lines.append("  " + str(g))
        else:
            lines.append("\n  -- no global assumption requests")

        if len(self.api_assumptions) > 0:
            lines.append("\n  api assumptions")
            for a in self.api_assumptions.values():
                lines.append("   " + str(a))
        else:
            lines.append("\n  -- no assumptions")
        if len(self.contract_assumptions) > 0:
            lines.append("\n contract assumptions")
            for ca in self.contract_assumptions.values():
                lines.append("   " + str(ca))
        else:
            lines.append("\n  -- no contract assumptions")
        if len(self.postcondition_requests) > 0:
            lines.append("\n  postcondition requests:")
            for p in self.postcondition_requests.values():
                lines.append("   " + str(p))
        else:
            lines.append("\n  -- no postcondition requests")
        if len(self.postcondition_guarantees) > 0:
            lines.append("\n  postcondition guarantees:")
            for pg in self.postcondition_guarantees.values():
                lines.append("   " + str(pg))
        else:
            lines.append("\n  -- no postcondition guarantees")
        if len(self.library_calls) > 0:
            lines.append("\n  library calls:")
            for (k, v) in self.library_calls:
                lines.append(
                    "   "
                    + k
                    + ":"
                    + v
                    + " -- "
                    + str(self.library_calls[(k, v)]))
        else:
            lines.append("\n  -- no library calls")
        if len(self.missing_summaries) > 0:
            lines.append("\n  missing summaries:")
            for lc in self.missing_summaries:
                lines.append("   " + lc)
        return "\n".join(lines)
