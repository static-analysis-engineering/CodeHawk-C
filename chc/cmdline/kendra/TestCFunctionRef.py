# ------------------------------------------------------------------------------
# C Source Code Analyzer
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

from chc.cmdline.kendra.TestPPORef import TestPPORef
from chc.cmdline.kendra.TestSPORef import TestSPORef


class TestCFunctionRef(object):
    def __init__(self, testcfileref, name, r):
        self.testcfileref = testcfileref
        self.name = name
        self.r = r
        self.ppos = {}
        self.spos = {}
        self._initialize()

    def get_ppos(self):
        result = []
        for l in self.ppos:
            result.extend(self.ppos[l])
        return result

    def add_ppo(self, ppo):
        self.r["ppos"].append(ppo)

    def has_ppos(self):
        return len(self.ppos) > 0

    def get_pred_ppos(self, pred):
        result = []
        for line in self.ppos:
            for ppo in self.ppos[line]:
                if ppo.get_predicate() == pred:
                    result.append(ppo)
        return result

    def get_spos(self):
        result = []
        for l in self.spos:
            result.extend(self.spos[l])
        return result

    def has_spos(self):
        return len(self.spos) > 0

    def has_multiple(self, line, pred):
        if line in self.ppos:
            ppopreds = [p for p in self.ppos[line] if p.get_predicate() == pred]
        return len(ppopreds) > 1

    def _initialize(self):
        if "ppos" in self.r:
            for p in self.r["ppos"]:
                ppo = TestPPORef(self, p)
                line = ppo.get_line()
                if line not in self.ppos:
                    self.ppos[line] = []
                self.ppos[line].append(ppo)
            if "spos" in self.r:
                for s in self.r["spos"]:
                    spo = TestSPORef(self, s)
                    line = spo.get_line()
                    if line not in self.spos:
                        self.spos[line] = []
                    self.spos[line].append(spo)
