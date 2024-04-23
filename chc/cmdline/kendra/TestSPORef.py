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

from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.cmdline.kendra.TestCFunctionRef import TestCFunctionRef


class TestSPORef:

    def __init__(
            self, testcfunctionref: "TestCFunctionRef", refd: Dict[str, str]
    ) -> None:
        self._testcfunctionref = testcfunctionref
        self._refd = refd

    @property
    def testcfunctionref(self) -> "TestCFunctionRef":
        return self._testcfunctionref

    @property
    def refd(self) -> Dict[str, str]:
        return self._refd

    @property
    def line(self) -> int:
        return int(self.refd["line"])

    @property
    def context(self) -> str:
        return self.refd["cfgctxt"]

    @property
    def tgt_status(self) -> str:
        return self.refd["tgtstatus"]

    @property
    def status(self) -> str:
        return self.refd["status"]

    @property
    def predicate(self) -> str:
        return self.refd["predicate"]

    @property
    def type(self) -> str:
        return self.refd["type"]

    @property
    def argnr(self) -> str:
        return self.refd["argnr"]

    @property
    def id(self) -> Tuple[str, str]:
        if self.type == "callsite":
            return (self.predicate, self.argnr)
        return ("?", "?")
