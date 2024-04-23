# ------------------------------------------------------------------------------
# C Source Code Analyzer
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

from typing import Any, Dict, List, TYPE_CHECKING

from chc.cmdline.kendra.TestPPORef import TestPPORef
from chc.cmdline.kendra.TestSPORef import TestSPORef

if TYPE_CHECKING:
    from chc.cmdline.kendra.TestCFileRef import TestCFileRef


class TestCFunctionRef:

    def __init__(
            self,
            testcfileref: "TestCFileRef",
            name: str,
            refd: Dict[str, Any]
    ) -> None:
        self._testcfileref = testcfileref
        self._name = name
        self._refd = refd
        self._line_ppos: Dict[int, List[TestPPORef]] = {}
        self._line_spos: Dict[int, List[TestSPORef]] = {}
        # self._initialize()

    @property
    def testcfileref(self) -> "TestCFileRef":
        return self._testcfileref

    @property
    def name(self) -> str:
        return self._name

    @property
    def refd(self) -> Dict[str, Any]:
        return self._refd

    @property
    def line_ppos(self) -> Dict[int, List[TestPPORef]]:
        if len(self._line_ppos) == 0:
            if "ppos" in self.refd:
                for p in self.refd["ppos"]:
                    ppo = TestPPORef(self, p)
                    self._line_ppos.setdefault(ppo.line, [])
                    self._line_ppos[ppo.line].append(ppo)
        return self._line_ppos

    @property
    def line_spos(self) -> Dict[int, List[TestSPORef]]:
        if len(self._line_spos) == 0:
            if "spos" in self.refd:
                for p in self.refd["spos"]:
                    spo = TestSPORef(self, p)
                    self._line_spos.setdefault(spo.line, [])
                    self._line_spos[spo.line].append(spo)
        return self._line_spos

    @property
    def ppos(self) -> List[TestPPORef]:
        result: List[TestPPORef] = []
        for line in self.line_ppos:
            result.extend(self.line_ppos[line])
        return result

    def add_ppo(self, ppo: Dict[str, Any]) -> None:
        self._refd["ppos"].append(ppo)

    def has_ppos(self) -> bool:
        return len(self.ppos) > 0

    def get_pred_ppos(self, pred: str) -> List[TestPPORef]:
        result: List[TestPPORef] = []
        for line in self.line_ppos:
            for ppo in self.line_ppos[line]:
                if ppo.predicate == pred:
                    result.append(ppo)
        return result

    @property
    def spos(self) -> List[TestSPORef]:
        result: List[TestSPORef] = []
        for line in self.line_spos:
            result.extend(self.line_spos[line])
        return result

    def has_spos(self) -> bool:
        return len(self.spos) > 0

    def has_multiple(self, line: int, pred: str) -> bool:
        if line in self.line_ppos:
            ppopreds = [p for p in self.line_ppos[line] if p.predicate == pred]
        return len(ppopreds) > 1
