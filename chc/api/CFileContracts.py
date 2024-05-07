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
"""User-provided contracts for variables and functions in a c-file."""

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

from chc.api.CFunctionContract import CFunctionContract

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CVarInfo import CVarInfo


class CFileContractGlobalVar:
    """User assertion about global variable."""

    def __init__(
            self,
            gvinfo: "CVarInfo",
            gvalue: Optional[int] = None,
            gconst: bool = False) -> None:
        self.gvinfo = gvinfo
        self.gvalue = gvalue
        self.gconst = gconst

    def __str__(self) -> str:
        pconst = " (const)" if self.gconst else ""
        pvalue = "" if self.gvalue is None else ": " + str(self.gvalue)
        return self.gvinfo.vname + pvalue + pconst


class CFileContracts:
    """User-provided contracts for the functions in a c-file."""

    def __init__(self, cfile: "CFile", contractpath: str) -> None:
        self._cfile = cfile
        self._contractpath = contractpath
        # self.xnode = UF.get_contracts(self._contractpath, self._cfile.name)
        self._functions: Dict[str, CFunctionContract] = {}
        self._globalvariables: Dict[str, CFileContractGlobalVar] = {}
        self._initialize()

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def contractpath(self) -> str:
        return self._contractpath

    @property
    def functions(self) -> Dict[str, CFunctionContract]:
        return self._functions

    @property
    def globalvariables(self) -> Dict[str, CFileContractGlobalVar]:
        return self._globalvariables

    def function_contract(self, name: str) -> CFunctionContract:
        if name in self.functions:
            return self.functions[name]
        else:
            raise UF.CHCError("No function contract found for " + name)

    def has_function_contract(self, name: str) -> bool:
        """Returns true if this contract contains a function contract for name."""

        return name in self.functions

    def has_assertions(self) -> bool:
        hasfns = any([f.has_assertions() for f in self.functions.values()])
        hasglobals = len(self.globalvariables) > 0
        return hasfns or hasglobals

    def has_postconditions(self) -> bool:
        return any([f.has_postconditions() for f in self.functions.values()])

    def has_preconditions(self) -> bool:
        return any([f.has_preconditions() for f in self.functions.values()])

    def count_postconditions(self) -> int:
        return sum([len(f.postconditions) for f in self.functions.values()])

    def count_preconditions(self) -> int:
        return sum([len(f.preconditions) for f in self.functions.values()])

    def iter_functions(self, f: Callable[[CFunctionContract], None]) -> None:
        for fn in self.functions:
            f(self.functions[fn])

    def report_postconditions(self) -> str:
        lines: List[str] = []
        if self.has_postconditions():
            lines.append("\nFile: " + self.cfile.name + " - postconditions")
            lines.append("-" * 80)
            for fname in sorted(self.functions):
                f = self.functions[fname]
                if f.has_postconditions():
                    lines.append(f.report_postconditions())
            return "\n".join(lines)
        return ""

    def report_preconditions(self) -> str:
        lines: List[str] = []
        if self.has_preconditions():
            lines.append("\nFile: " + self.cfile.name + " - preconditions")
            lines.append("-" * 80)
            for fname in sorted(self.functions):
                f = self.functions[fname]
                if f.has_preconditions():
                    lines.append(f.report_preconditions())
            return "\n".join(lines)
        return ""

    def __str__(self) -> str:
        lines: List[str] = []
        if self.has_assertions():
            lines.append("\nFile: " + self.cfile.name)
            lines.append("-" * 80)
            for cgv in self.globalvariables.values():
                lines.append("  " + str(cgv))
            for f in self.functions.values():
                if f.has_assertions():
                    lines.append("\n" + str(f))
            lines.append("-" * 80)
        return "\n".join(lines)

    def _initialize(self) -> None:
        xnode = UF.get_contracts(self.contractpath, self.cfile.name)
        if xnode is None:
            return
        gvnode = xnode.find("global-variables")
        if gvnode is not None:
            for gnode in gvnode.findall("gvar"):
                name = gnode.get("name")
                if name is None:
                    raise UF.CHCError("No name specified for global variable")
                gvinfo = self.cfile.get_global_varinfo_by_name(name)
                gconst = "const" in gnode.attrib and gnode.get("const") == "yes"
                gval = gnode.get("value")
                gvalue = int(gval) if gval else None
                self.globalvariables[name] = CFileContractGlobalVar(
                    gvinfo, gvalue, gconst
                )
        ffnode = xnode.find("functions")
        if ffnode is not None:
            for fnode in ffnode.findall("function"):
                fn = CFunctionContract(self, fnode)
                chklogger.logger.info("Function contract found for %s", fn.name)
                self._functions[fn.name] = fn
