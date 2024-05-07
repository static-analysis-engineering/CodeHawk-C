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
"""User-provided function contract with assumptions and guarantees."""

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.api.CFileContracts import CFileContracts
    from chc.api.CFunctionApi import CFunctionApi
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.XPredicate import XPredicate
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction



class CFunctionContract(object):

    def __init__(
            self,
            cfilecontracts: "CFileContracts",
            xnode: ET.Element) -> None:
        self._cfilecontracts = cfilecontracts
        self._xnode = xnode
        self._signature: Optional[Dict[str, int]] = None  # name -> index nr
        self._postconditions: Optional[Dict[int, "XPredicate"]] = None
        self._preconditions: Optional[Dict[int, "XPredicate"]] = None
        self._sideeffects: Optional[Dict[int, "XPredicate"]] = None
        self._postrequests: Dict[int, "XPredicate"] = {}
        # self._initialize(self.xnode)

    @property
    def cfilecontracts(self) -> "CFileContracts":
        return self._cfilecontracts

    @property
    def name(self) -> str:
        n = self._xnode.get("name")
        if n is None:
            raise UF.CHCError("Function Contract without name")
        else:
            return n

    @property
    def ignore(self) -> bool:
        return self._xnode.get("ignore", "no") == "yes"

    @property
    def cfile(self) -> "CFile":
        return self.cfilecontracts.cfile

    @property
    def cfun(self) -> "CFunction":
        return self.cfile.get_function_by_name(self.name)

    @property
    def api(self) -> "CFunctionApi":
        return self.cfun.api

    @property
    def ifd(self) -> "InterfaceDictionary":
        return self.cfile.interfacedictionary

    '''
    @property
    def prd(self) -> "PredicateDictionary":
        return self.cfile.predicatedictionary
    '''

    def has_assertions(self) -> bool:
        return (len(self.postconditions) + len(self.preconditions)) > 0

    def has_postconditions(self) -> bool:
        return len(self.postconditions) > 0

    def has_preconditions(self) -> bool:
        return len(self.preconditions) > 0

    @property
    def postrequests(self) -> Dict[int, "XPredicate"]:
        return self._postrequests

    @property
    def signature(self) -> Dict[str, int]:
        if self._signature is None:
            xsig = self._xnode.find("parameters")
            if xsig is not None:
                self._signature = {}
                for xpar in xsig.findall("par"):
                    xname = xpar.get("name")
                    xnr = xpar.get("nr")
                    if xname is not None and xnr is not None:
                        self._signature[xname] = int(xnr)
                return self._signature
            else:
                print("Problem with function contract signature: " + self.name)
        self._signature = {}
        return self._signature

    @property
    def rsignature(self) -> Dict[int, str]:
        return {v: k for k, v in self.signature.items()}

    @property
    def postconditions(self) -> Dict[int, "XPredicate"]:
        chklogger.logger.info("Retrieve postconditions for %s", self.name)
        if self._postconditions is None:
            self._postconditions = {}
            xpost = self._xnode.find("postconditions")
            if xpost is not None:
                for xpc in xpost.findall("post"):
                    ipc = self.ifd.parse_mathml_xpredicate(xpc, self.signature)
                    pc = self.ifd.get_xpredicate(ipc)
                    self._postconditions[ipc] = pc
                return self._postconditions
        # self._postconditions = None
        return self._postconditions

    @property
    def preconditions(self) -> Dict[int, "XPredicate"]:
        if self._preconditions is None:
            xpre = self._xnode.find("preconditions")
            if xpre is not None:
                self._preconditions = {}
                for xpc in xpre.findall("pre"):
                    ipc = self.ifd.parse_mathml_xpredicate(xpc, self.signature)
                    pc = self.ifd.get_xpredicate(ipc)
                    self._preconditions[ipc] = pc
                return self._preconditions
        self._preconditions = {}
        return self._preconditions

    @property
    def sideeffects(self) -> Dict[int, "XPredicate"]:
        if self._sideeffects is None:
            xse = self._xnode.find("sideeffects")
            if xse is not None:
                self._sideeffects = {}
                for xs in xse.findall("sideeffect"):
                    ise = self.ifd.parse_mathml_xpredicate(xs, self.signature)
                    se = self.ifd.get_xpredicate(ise)
                    self._sideeffects[ise] = se
                return self._sideeffects
        self._sideeffects = {}
        return self._sideeffects

    def add_postrequest(self, req: "XPredicate") -> None:
        """Add post request from caller's function api"""

        if req.index in self.postconditions:
            return
        self.postrequests[req.index] = req

    '''
    def _initialize_signature(self, ppnode: ET.Element):
        if ppnode is None:
            print("Problem with function contract signature: " + self.name)
            return
        for pnode in ppnode.findall("par"):
            self.signature[pnode.get("name")] = int(pnode.get("nr"))
            self.rsignature[int(pnode.get("nr"))] = pnode.get("name")

    def _initialize_postconditions(self, pcsnode):
        if pcsnode is None:
            return
        for pcnode in pcsnode.findall("post"):
            ipc = self.ixd.parse_mathml_xpredicate(pcnode, self.signature)
            pc = self.ixd.get_xpredicate(ipc)
            self.postconditions[ipc] = pc

    def _initialize_preconditions(self, prenode):
        if prenode is None:
            return
        gvars = self.cfilecontracts.globalvariables
        for pnode in prenode.findall("pre"):
            ipre = self.ixd.parse_mathml_xpredicate(pnode, self.signature, gvars=gvars)
            pre = self.ixd.get_xpredicate(ipre)
            self.preconditions[ipre] = pre

    def _initialize_sideeffects(self, sidenode):
        if sidenode is None:
            return
        gvars = self.cfilecontracts.globalvariables
        for snode in sidenode.findall("sideeffect"):
            iside = self.ixd.parse_mathml_xpredicate(snode, self.signature, gvars=gvars)
            se = self.ixd.get_xpredicate(iside)
            self.sideeffects[iside] = se

    def _initialize(self, xnode):
        try:
            self._initialize_signature(xnode.find("parameters"))
            self._initialize_postconditions(xnode.find("postconditions"))
            self._initialize_preconditions(xnode.find("preconditions"))
            self._initialize_sideeffects(xnode.find("sideeffects"))
        except Exception as e:
            print(
                "Error in reading function contract "
                + self.name
                + " in file "
                + self.cfun.cfile.name
                + ": "
                + str(e)
            )
            exit(1)
        '''

    def report_postconditions(self) -> str:
        lines: List[str] = []
        if len(self.postconditions) == 1:
            return (
                "  "
                + self.name
                + ": "
                + list(self.postconditions.values())[0].pretty())
        elif len(self.postconditions) > 1:
            lines.append("  " + self.name)
            pclines = []
            for pc in self.postconditions.values():
                pclines.append("     " + pc.pretty())
            lines = lines + sorted(pclines)
            return "\n".join(lines)
        return ""

    def report_preconditions(self) -> str:
        lines: List[str] = []
        try:
            if len(self.preconditions) == 1:
                return (
                    "  "
                    + self.name
                    + ": "
                    + list(self.preconditions.values())[0].pretty())
            elif len(self.preconditions) > 1:
                lines.append("  " + self.name)
                pclines = []
                for pc in self.preconditions.values():
                    pclines.append("     " + pc.pretty())
                lines = lines + sorted(pclines)
                return "\n".join(lines)
            return ""
        except UF.CHCError as e:
            msg = (
                "Error in contract function: "
                + self.name
                + " in file: "
                + self.cfilecontracts.cfile.name
                + ": "
                + str(e)
            )
            raise UF.CHCError(msg)

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("Contract for " + self.name)

        def add(title: str, pl: List["XPredicate"]) -> None:
            if len(pl) > 0:
                lines.append(title)
                for p in pl:
                    lines.append("     " + (p.pretty()))

        add("  Postconditions:", list(self.postconditions.values()))
        add("  Preconditions :", list(self.preconditions.values()))
        return "\n".join(lines)
