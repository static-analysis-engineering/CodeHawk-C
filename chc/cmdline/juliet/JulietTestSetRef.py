# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
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

from chc.cmdline.juliet.JulietTestRef import JulietTestRef

class JulietTestSetRef(object):

    def __init__(self,d):
        self.d = d
        self.tests = {}      # testindex (str) -> JulietTestRef
        self.macros = {}
        self._initialize()

    def expand(self,m):
        if m.startswith('PPO'):
            if m in self.macros:
                return self.macros[m]
            else:
                return m
        if m.startswith('PS'):
            if m in self.macros:
                lst = self.macros[m]
                return [ self.expand(x) for x in lst ]
            else:
                return m
        return m

    def get_predicates(self):
        result = []
        for p in self.macros:
            if p.startswith('PPO'):
                result.append(self.macros[p]['P'])
        return result

    def get_tests(self): return self.tests.items()

    def get_predicate_violations(self):
        result = {}
        violations = self.get_violations()
        for v in violations:
            p = v.predicate
            if not p in result: result[p] = 0
            result[p] += 1
        return result

    def get_predicate_safe_controls(self):
        result = {}
        safecontrols = self.get_safe_controls()
        for s in safecontrols:
            p = s.predicate
            if not p in result: result[p] = 0
            result[p] += 1
        return result

    def get_violations(self):
        result = []
        def f(i,test):
            result.extend(test.get_violations())
        self.iter(f)
        return result

    def get_safe_controls(self):
        result = []
        def f(i,test):
            result.extend(test.get_safe_controls())
        self.iter(f)
        return result

    def iter(self,f):
        for (t,test) in self.get_tests():
            f(t,test)

    def __str__(self):
        lines = []
        for test in sorted(self.tests):
            lines.append('\nTest ' + test)
            lines.append(str(self.tests[test]))
        return '\n'.join(lines)

    def _initialize(self):
        for m in self.d['macros']:
            self.macros[m] = self.d['macros'][m]
        for test in self.d['tests']:
            self.tests[test] = JulietTestRef(self,test,self.d['tests'][test])
