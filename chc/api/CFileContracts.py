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

import xml.etree.ElementTree as ET

import chc.util.fileutil as UF

from chc.api.CFunctionContract import CFunctionContract

class CFileContractGlobalVar(object):
    """User assertion about global variable."""

    def __init__(self,gvinfo,gvalue=None,gconst=False):
        self.gvinfo = gvinfo
        self.gvalue = gvalue
        self.gconst = gconst

    def __str__(self):
        pconst = ' (const)' if self.gconst else ''
        pvalue = '' if self.gvalue is None else ': ' + str(self.gvalue) 
        return self.gvinfo.vname + pvalue + pconst


class CFileContracts(object):
    """User-provided contracts for the functions in a c-file."""

    def __init__(self,cfile,contractpath):
        self.cfile = cfile
        self.contractpath = contractpath
        self.xnode = UF.get_contracts(self.contractpath,self.cfile.name)
        self.functions = {}       #  function name -> CFunctionContract
        self.globalvariables = {}     # name -> CVarInfo
        self._initialize(self.xnode)

    def get_function_contract(self,name):
        if name in self.functions:
            return self.functions[name]

    def has_function_contract(self,name): return name in self.functions

    def has_assertions(self):
        hasfns = any( [ f.has_assertions() for f in self.functions.values() ])
        hasglobals = len(self.globalvariables) > 0
        return hasfns or hasglobals

    def has_postconditions(self):
        return any( [ f.has_postconditions() for f in self.functions.values() ])

    def has_preconditions(self):
        return any( [ f.has_preconditions() for f in self.functions.values() ])

    def count_postconditions(self):
        return sum( [ len(f.postconditions) for f in self.functions.values() ])

    def count_preconditions(self):
        return sum( [ len(f.preconditions) for f in self.functions.values() ])

    def iter_functions(self,f):
        for fn in self.functions: f(self.functions[fn])

    def report_postconditions(self):
        lines = []
        if self.has_postconditions():
            lines.append('\nFile: ' + self.cfile.name + ' - postconditions')
            lines.append('-' * 80)
            for fname in sorted(self.functions):
                f = self.functions[fname]
                if f.has_postconditions():
                    lines.append(f.report_postconditions())
            return '\n'.join(lines)
        return ''

    def report_preconditions(self):
        lines = []
        if self.has_preconditions():
            lines.append('\nFile: ' + self.cfile.name + ' - preconditions')
            lines.append('-' * 80)
            for fname in  sorted(self.functions):
                f = self.functions[fname]
                if f.has_preconditions():
                    lines.append(f.report_preconditions())
            return '\n'.join(lines)
        return ''

    def __str__(self):
        lines = []
        if self.has_assertions():
            lines.append('\nFile: ' + self.cfile.name)
            lines.append('-' * 80)
            for cgv in self.globalvariables.values():
                lines.append('  ' + str(cgv))
            for f in self.functions.values():
                if f.has_assertions():
                    lines.append('\n' + str(f))
            lines.append('-' * 80)
        return '\n'.join(lines)

    def _initialize(self,xnode):
        if xnode is None: return
        gvnode = xnode.find('global-variables')
        if not gvnode is None:
            for gnode in gvnode.findall('gvar'):
                name = gnode.get('name')
                gvinfo = self.cfile.declarations.get_global_varinfo_by_name(name)
                gconst = 'const' in gnode.attrib and gnode.get('const') == 'yes'
                gvalue = int(gnode.get('value')) if 'value' in gnode.attrib else None
                self.globalvariables[name] = CFileContractGlobalVar(gvinfo,gvalue,gconst)
        for fnode in xnode.find('functions').findall('function'):
            fn = CFunctionContract(self,fnode)
            self.functions[fn.name] = fn

