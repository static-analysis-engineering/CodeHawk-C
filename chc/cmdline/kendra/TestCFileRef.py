# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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


from chc.cmdline.kendra.TestCFunctionRef import TestCFunctionRef

class TestCFileRef(object):

    def __init__(self,testsetref,name,r):
        self.testsetref = testsetref
        self.name = name
        self.r = r
        self.functions = {}
        self._initialize()

    def iter(self,f):
        for fn in self.functions.values(): f(fn)

    def get_functionnames(self): return sorted(self.functions.keys())

    def get_functions(self):
        return sorted(self.functions.values(),key=lambda f:f.name)

    def get_function(self,fname):
        if fname in self.functions:
            return self.functions[fname]

    def has_domains(self):
        return 'domains' in self.r and len(self.r['domains']) > 0

    def get_domains(self): return self.r['domains']

    def has_spos(self):
        for f in self.get_functions():
            if f.has_spos(): return True
        else: return False

    def _initialize(self):
        for f in self.r['functions']:
            self.functions[f] = TestCFunctionRef(self,f,self.r['functions'][f])
