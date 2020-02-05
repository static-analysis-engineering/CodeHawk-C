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

import json

from chc.cmdline.kendra.TestCFileRef import TestCFileRef

class TestSetRef(object):
    '''Provides access to the reference results of a set of C files.'''

    def __init__(self,specfilename):
        self.specfilename = specfilename
        with open(specfilename) as fp:
            self.r = json.load(fp)
        self.cfiles = {}
        self._initialize()

    def iter(self,f):
        for cfile in self.cfiles.values(): f(cfile)

    def get_cfilenames(self): return sorted(self.cfiles.keys())

    def get_cfiles(self):
        return sorted(self.cfiles.values(),key=lambda f:f.name)

    def get_cfile(self,cfilename):
        if cfilename in self.cfiles:
            return self.cfiles[cfilename]

    def set_ppos(self,cfilename,cfun,ppos):
        self.r['cfiles'][cfilename]['functions'][cfun]['ppos'] = ppos

    def set_spos(self,cfilename,cfun,spos):
        self.r['cfiles'][cfilename]['functions'][cfun]['spos'] = spos

    def has_characteristics(self): return 'characteristics' in self.r

    def get_characteristics(self):
        if 'characteristics' in self.r:
            return self.r['characteristics']

    def has_restrictions(self): return 'restrictions' in self.r

    def get_restrictions(self):
        if 'restrictions' in self.r:
            return self.r['restrictions']
        else:
            return []

    def is_linux_only(self):
        return 'linux-only' in self.get_restrictions()

    def save(self):
        with open(self.specfilename,'w') as fp:
            fp.write(json.dumps(self.r,indent=4,sort_keys=True))

    def __str__(self):
        lines = []
        for cfile in self.get_cfiles():
            lines.append(cfile.name)
            for cfun in cfile.get_functions():
                lines.append('  ' + cfun.name)
                if cfun.has_ppos():
                    for ppo in sorted(cfun.get_ppos(),key=lambda p:p.get_line()):
                        hasmultiple = cfun.has_multiple(ppo.get_line(),ppo.get_predicate())
                        ctxt = ppo.get_context_string() if hasmultiple else ''
                        status = ppo.get_status().ljust(12)
                        if ppo.get_status() == ppo.get_tgt_status():
                            tgtstatus = ''
                        else:
                            tgtstatus = '(' + ppo.get_tgt_status() + ')'
                        lines.append(
                            '    ' + str(ppo.get_line()).rjust(4) + '  ' +
                            ppo.get_predicate().ljust(24) +
                            ' ' + status + ' ' + ctxt.ljust(40) + tgtstatus)
        return '\n'.join(lines)

    def _initialize(self):
        for f in self.r['cfiles']:
            self.cfiles[f] = TestCFileRef(self,f,self.r['cfiles'][f])
