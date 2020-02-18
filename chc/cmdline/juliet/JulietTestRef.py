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

from chc.cmdline.juliet.JulietTestFileRef import JulietTestFileRef

class JulietTestRef():

    def __init__(self,testsetref,test,d):
        self.testsetref = testsetref
        self.test = test
        self.d = d
        self.cfiles = {}    #  filename -> JulietTestFileRef
        self._initialize()

    def get_test(self): return self.test

    def expand(self,m): return self.testsetref.expand(m)

    def get_cfiles(self): return self.cfiles.items()

    def get_violations(self):
        result = []
        def f(name,ctestfile):
            violations = ctestfile.get_violations()
            result.extend(sum([ v[1] for v in violations ],[]))
        self.iter(f)
        return result

    def get_safe_controls(self):
        result = []
        def f(name,ctestfile):
            safecontrols = ctestfile.get_safe_controls()
            result.extend(sum([ v[1] for v in safecontrols ],[]))
        self.iter(f)
        return result

    '''f: (filename,juliettestfile) -> unit. '''
    def iter(self,f):
        for (filename,cfile) in self.get_cfiles():
            f(filename,cfile)

    def __str__(self):
        lines = []
        for f in self.cfiles:
            lines.append(f)
            lines.append(str(self.cfiles[f]))
        return '\n'.join(lines)

    def _initialize(self):
        for f in self.d['cfiles']:
            self.cfiles[f] = JulietTestFileRef(self,self.d['cfiles'][f])
