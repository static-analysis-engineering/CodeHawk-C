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

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF

from chc.api.CFunctionCandidateContract import CFunctionCandidateContract

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction


class CFileCandidateContracts:
    """User-provided contracts for the functions in a c-file."""

    def __init__(self, cfile: "CFile", contractpath: str) -> None:
        self._cfile = cfile
        self._contractpath = contractpath
        self.xnode = UF.get_candidate_contracts(self._contractpath, self._cfile.name)
        self._functions: Dict[str, CFunctionCandidateContract] = {}
        self._initialize(self.xnode)

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def contractpath(self) -> str:
        return self._contractpath

    @property
    def functions(self) -> Dict[str, CFunctionCandidateContract]:
        return self._functions

    def collect_post(self) -> None:
        """collects advertised post conditions from functions"""

        def f(fn: "CFunctionCandidateContract") -> None:
            fn.collect_post()

        self.iter_functions(f)

    def function_contract(self, name: str) -> CFunctionCandidateContract:
        if name in self.functions:
            return self.functions[name]
        raise UF.CHCError("No function contract found for " + name)

    def has_function_contract(self, name: str) -> bool:
        return name in self.functions

    def iter_functions(
            self, f: Callable[[CFunctionCandidateContract], None]) -> None:
        for fn in self.functions:
            f(self.functions[fn])

    def write_mathml(self, cnode: ET.Element) -> None:
        ffnode = ET.Element("functions")
        ddnode = ET.Element("data-structures")
        cnode.extend([ddnode, ffnode])
        for fn in self.functions.values():
            fnode = ET.Element("function")
            fnode.set("name", fn.name)
            fn.write_mathml(fnode)
            ffnode.append(fnode)

    def save_mathml_contract(self) -> None:
        fnode = ET.Element("cfile")
        self.write_mathml(fnode)
        UF.save_candidate_contracts_file(self.contractpath, self.cfile.name, fnode)

    def __str__(self) -> str:
        lines: List[str] = []
        return "\n".join(lines)

    def _initialize(self, xnode: Optional[ET.Element]) -> None:
        if xnode is None:
            return
        ffnode = xnode.find("functions")
        if ffnode is not None:
            for fnode in ffnode.findall("function"):
                if fnode is not None:
                    fn = CFunctionCandidateContract(self, fnode)
                    self._functions[fn.name] = fn
