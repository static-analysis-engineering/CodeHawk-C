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

from chc.proof.CFunctionPPOs import CFunctionPPOs
from chc.proof.CFunctionSPOs import CFunctionSPOs


import chc.util.fileutil as UF

'''
CFunctionProofs is the root of a data structure that provides access to
all proof obligations and associated evidence. Relationships between
proof obligation and evidence are established through the CFunctionProofs
object.

- CFunctionProofs
  - ppos: CFunctionPPOs
          - id -> CFunctionPPO

  - spos: CFunctionSPOs
          - callsitespos: context -> CFunctionCallsiteSPOs
                                     - id -> CFunctionCallsiteSPO
          - returnsitespos: context -> CFunctionReturnsiteSPOs
                                       id -> CFunctionReturnsiteSPO
'''

class CFunctionProofs(object):

    def __init__(self,cfun):
        self.cfun = cfun
        self.cfile = self.cfun.cfile
        self.capp = self.cfile.capp
        self.cfile.predicatedictionary.initialize()
        self.ppos = None           # CFunctionPPOs
        self.spos = None           # CFunctionSPOs

    def add_returnsite_postcondition(self,postcondition):
        self._get_spos()
        self.spos.add_returnsite_postcondition(postcondition)

    def update_spos(self):
        self._get_spos()
        self.spos.update()

    def distribute_post_guarantees(self):
        self._get_spos()
        self.spos.distribute_post_guarantees()

    def collect_post_assumes(self):
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self._get_spos()
        if self.spos is None:
            raise UF.CHCError('No supporting proof obligations found for '
                                + str(self.cfun.name) + ' in file '
                                + str(self.cfile.name))
        self.spos.collect_post_assumes()

    def reset_spos(self): self.spos = None

    def save_spos(self):
        cnode = ET.Element('function')
        cnode.set('name',self.cfun.name)
        self.spos.write_xml(cnode)
        self._save_spos(cnode)

    def get_ppo(self,id):
        self._get_ppos()
        return self.ppos.get_ppo(id)

    def get_spo(self,id):
        self._get_spos()
        return self.spos.get_spo(id)

    def iter_ppos(self,f): 
        self._get_ppos()
        self.ppos.iter(f)

    def iter_spos(self,f):
        self._get_spos()
        self.spos.iter(f)

    def iter_callsites(self,f):
        self._get_spos()
        self.spos.iter_callsites(f)

    def reload_ppos(self): self._get_ppos(force=True)

    def reload_spos(self): self._get_spos(force=True)

    def get_ppos(self):
        result = []
        def f(ppo): result.append(ppo)
        self.iter_ppos(f)
        return result

    def get_spos(self):
        self._get_spos()
        result = []
        def f(spo): result.append(spo)
        self.iter_spos(f)
        return result

    def get_open_ppos(self):
        result = []
        def f(ppo):
            if not ppo.is_closed(): result.append(ppo)
        self.iter_ppos(f)
        return result

    def get_open_spos(self):
        result = []
        def f(spo):
            if  not spo.is_closed(): result.append(spo)
        self.iter_spos(f)
        return result

    def get_violations(self):
        result = []
        def f(ppo):
            if ppo.is_violated(): result.append(ppo)
        self.iter_ppos(f)
        return result

    def get_spo_violations(self):
        result = []
        def f(spo):
            if spo.is_violated(): result.append(spo)
        self.iter_spos(f)
        return result

    def get_delegated(self):
        result = []
        def f(ppo):
            if ppo.is_delegated(): result.append(ppo)
        self.iter_ppos(f)
        return result

    def _get_ppos(self,force=False):
        if self.ppos is None or force:
            xnode = UF.get_ppo_xnode(self.capp.path,self.cfile.name,self.cfun.name)
            if not xnode is None:
                self.ppos = CFunctionPPOs(self,xnode)
            else:
                print('Unable to load ppos for ' + self.cfun.name + ' in file '
                          + self.cfile.name)

    def _get_spos(self,force=False):
        if self.spos is None or force:
            xnode = UF.get_spo_xnode(self.capp.path,self.cfile.name,self.cfun.name)
            if not xnode is None:
                self.spos = CFunctionSPOs(self,xnode)
            else:
                raise UF.CHCError('Unable to load spos for ' + self.cfun.name + ' in file '
                            + self.cfile.name)

    def _save_spos(self,cnode):
        UF.save_spo_file(self.capp.path,self.cfile.name,self.cfun.name,cnode)

