# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from chc.cmdline.kendra.TestCFunctionRef import TestCFunctionRef

if TYPE_CHECKING:
    from chc.cmdline.kendra.TestSetRef import TestSetRef


class TestCFileRef:

    def __init__(
            self, testsetref: "TestSetRef", name: str, refd: Dict[str, Any]) -> None:
        self._testsetref = testsetref
        self._name = name
        self._refd = refd
        self._functions: Dict[str, TestCFunctionRef] = {}
        # self._initialize()

    @property
    def testsetref(self) -> "TestSetRef":
        return self._testsetref

    @property
    def name(self) -> str:
        return self._name

    @property
    def refd(self) -> Dict[str, Any]:
        return self._refd

    @property
    def functions(self) -> Dict[str, TestCFunctionRef]:
        if len(self._functions) == 0:
            for (f, fdata) in self.refd["functions"].items():
                self._functions[f] = TestCFunctionRef(self, f, fdata)
        return self._functions

    '''
    def iter(self, f):
        for fn in self.functions.values():
            f(fn)
    '''

    @property
    def functionnames(self) -> List[str]:
        return sorted(self.functions.keys())

    '''
    def get_functions(self):
        return sorted(self.functions.values(), key=lambda f: f.name)
    '''

    def get_function(self, fname: str) -> Optional[TestCFunctionRef]:
        if fname in self.functions:
            return self.functions[fname]
        return None

    def has_domains(self) -> bool:
        return "domains" in self.refd and len(self.refd["domains"]) > 0

    @property
    def domains(self) -> List[str]:
        if self.has_domains():
            return self.refd["domains"]
        else:
            return []

    def has_spos(self) -> bool:
        for f in self.functions.values():
            if f.has_spos():
                return True
        else:
            return False

    '''
    def _initialize(self):
        for f in self.r["functions"]:
            self.functions[f] = TestCFunctionRef(self, f, self.r["functions"][f])
    '''
