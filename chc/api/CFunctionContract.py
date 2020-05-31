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

class CFunctionContract(object):
    """Representsa user-provided function contract."""

    def __init__(self,cfilecontracts,xnode):
        self.cfilecontracts = cfilecontracts
        self.ixd = self.cfilecontracts.cfile.interfacedictionary
        self.prd = self.cfilecontracts.cfile.predicatedictionary
        self.xnode = xnode
        self.name  = self.xnode.get('name')
        self.cfun = self.cfilecontracts.cfile.get_function_by_name(self.name)
        self.api = self.cfun.api
        self.ignore = self.xnode.get('ignore','no') == 'yes'
        self.signature = {}                   # name -> index nr
        self.rsignature = {}                  # index nr -> name
        self.postconditions = {}              # index -> XPredicate
        self.preconditions = {}               # index -> XPredicate
        self.sideeffects = {}                 # index -> XPredicate
        self._initialize(self.xnode)

    def has_assertions(self):
        return (len(self.postconditions) + len(self.preconditions)) > 0

    def has_postconditions(self):
        return len(self.postconditions) > 0

    def has_preconditions(self):
        return len(self.preconditions) > 0
        
    def _initialize_signature(self,ppnode):
        if ppnode is None:
            print('Problem with function contract signature: ' + self.name)
            return
        for pnode in ppnode.findall('par'):
            self.signature[pnode.get('name')] = int(pnode.get('nr'))
            self.rsignature[int(pnode.get('nr'))] = pnode.get('name')

    def _initialize_postconditions(self,pcsnode):
        if pcsnode is None: return
        for pcnode in pcsnode.findall('post'):
            ipc = self.ixd.parse_mathml_xpredicate(pcnode,self.signature)
            pc = self.ixd.get_xpredicate(ipc)
            self.postconditions[ipc] = pc

    def _initialize_preconditions(self,prenode):
        if prenode is None: return
        gvars = self.cfilecontracts.globalvariables
        for pnode in prenode.findall('pre'):
            ipre = self.ixd.parse_mathml_xpredicate(pnode,self.signature,gvars=gvars)
            pre = self.ixd.get_xpredicate(ipre)
            self.preconditions[ipre] = pre

    def _initialize_sideeffects(self,sidenode):
        if sidenode is None: return
        gvars = self.cfilecontracts.globalvariables
        for snode in sidenode.findall('sideeffect'):
            iside = self.ixd.parse_mathml_xpredicate(snode,self.signature,gvars=gvars)
            se = self.ixd.get_xpredicate(iside)
            self.sideeffects[iside] = se

    def _initialize(self,xnode):
        try:
            self._initialize_signature(xnode.find('parameters'))
            self._initialize_postconditions(xnode.find('postconditions'))
            self._initialize_preconditions(xnode.find('preconditions'))
            self._initialize_sideeffects(xnode.find('sideeffects'))
        except Exception as e:
            print('Error in reading function contract ' + self.name
                      + ' in file ' + self.cfun.cfile.name + ': ' + str(e))
            exit(1)

    def report_postconditions(self):
        lines = []
        if len(self.postconditions) == 1:
            return ('  ' + self.name + ': ' + self.postconditions.values()[0].pretty())
        elif len(self.postconditions) > 1:
            lines.append('  ' + self.name)
            pclines = []
            for pc in self.postconditions.values():
                pclines.append('     ' + pc.pretty())
            lines = lines + sorted(pclines)
            return  '\n'.join(lines)
        return ''

    def report_preconditions(self):
        lines = []
        try:
            if len(self.preconditions) == 1:
                return ('  ' + self.name + ': ' + self.preconditions.values()[0].pretty())
            elif len(self.preconditions) > 1:
                lines.append('  ' + self.name)
                pclines = []
                for pc in self.preconditions.values():
                    pclines.append('     ' + pc.pretty())
                lines = lines + sorted(pclines)
                return '\n'.join(lines)
            return ''
        except UF.CHCError as e:
            msg = ('Error in contract function: ' + self.name + ' in file: '
                     + self.cfilecontracts.cfile.name + ': ' + str(e))
            raise UF.CHCError(msg)

    def __str__(self):
        lines = []
        lines.append('Contract for ' + self.name)
        def add(t, pl):
            if len(pl) > 0:
                lines.append(t)
                for p in pl: lines.append('     ' + (p.pretty()))
        add('  Postconditions:', self.postconditions.values())
        add('  Preconditions :', self.preconditions.values())
        return '\n'.join(lines)
                                            

