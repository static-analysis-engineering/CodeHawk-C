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

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

from chc.app.CVarInfo import CVarInfo


class CFunDeclarations(object):
    '''Function parameter and local variable declarations.'''

    def __init__(self,cfun,xnode):
        self.cfun = cfun
        self.varinfos = {}                # vid -> CVarInfo
        self.dictionary = cfun.cfile.declarations.dictionary
        self.local_varinfo_table = IT.IndexedTable('local-varinfo-table')
        self.tables = [
            (self.local_varinfo_table,self._read_xml_local_varinfo_table) ]
        self.initialize(xnode)

    def get_formals(self):
        return [ x for x in self.local_varinfo_table.values() if x.vparam > 0 ]

    def get_locals(self):
        return [ x for x in self.local_varinfo_table.values() if x.vparam == 0 ]

    def get_varinfo(self,vid):
        if vid in self.varinfos:
            return self.varinfos[vid]
        return self.cfun.cfile.declarations.get_global_varinfo(vid)

    def get_global_varinfo_by_name(self,name):
        return self.cfun.cfile.declarations.get_global_varinfo_by_name(name)

    def get_location(self,ix): return self.cfun.cfile.declarations.get_location(ix)

    def __str__(self):
        lines = []
        for (t,_) in self.table:
            if t.size() > 0:
                lines.append(str(t))
        lines.append('\nVarinfos:')
        lines.append('-' * 40)
        for vid in sorted(self.varinfos):
            lines.append(str(vid).rjust(5) + '  ' + self.varinfos[vid].vname)
        return '\n'.join(lines)

    def initialize(self,xnode):
        for (t,f) in self.tables:
            t.reset()
            f(xnode.find(t.name))
        for v in self.local_varinfo_table.values():
            self.varinfos[v.get_vid()] = v

    def _read_xml_local_varinfo_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CVarInfo(*args)
        self.local_varinfo_table.read_xml(xnode,'n',get_value)
