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

from chc.api.CFunctionCandidateContract import CFunctionCandidateContract

class CFileCandidateContracts(object):
    """User-provided contracts for the functions in a c-file."""

    def __init__(self,cfile,contractpath):
        self.cfile = cfile
        self.contractpath = contractpath
        self.xnode = UF.get_kta_contracts(self.contractpath,self.cfile.name)
        self.functions = {}       #  function name -> CFunctionCandidateContract
        self._initialize(self.xnode)

    def collect_post(self):
        '''collects advertised post conditions from functions'''
        def f(fn): fn.collect_post()
        self.iter_functions(f)

    def get_function_contract(self,name):
        if name in self.functions:
            return self.functions[name]

    def has_function_contract(self,name): return name in self.functions

    def iter_functions(self,f):
        for fn in self.functions: f(self.functions[fn])

    def write_mathml(self,cnode):
        ffnode = ET.Element('functions')
        ddnode = ET.Element('data-structures')
        cnode.extend([ddnode, ffnode])
        for fn in self.functions.values():
            fnode = ET.Element('function')
            fnode.set('name',fn.name)
            fn.write_mathml(fnode)
            ffnode.append(fnode)

    def save_mathml_contract(self):
        fnode = ET.Element('cfile')
        self.write_mathml(fnode)
        UF.save_candidate_contracts_file(self.contractpath,self.cfile.name,fnode)

    def __str__(self):
        lines = []
        return '\n'.join(lines)

    def _initialize(self,xnode):
        if xnode is None: return
        for fnode in xnode.find('functions').findall('function'):
            fn = CFunctionCandidateContract(self,fnode)
            self.functions[fn.name] = fn
        
        
