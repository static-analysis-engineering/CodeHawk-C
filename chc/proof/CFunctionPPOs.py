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

from chc.proof.CFunctionPPO import CFunctionPPO
from chc.proof.CFunctionPOs import CFunctionPOs
from chc.proof.CFunctionPO import CProofDependencies
from chc.proof.CFunctionPO import CProofDiagnostic


po_status = {
    'g': 'safe',
    'o': 'open',
    'r': 'violation',
    'x': 'dead-code'
    }

class CFunctionPPOs(CFunctionPOs):

    '''Represents the set of primary proof obligations for a function.'''

    def __init__(self,cproofs,xnode):
        CFunctionPOs.__init__(self,cproofs)
        self.xnode = xnode
        self.ppos = {}                   # ppoid -> CFunctionPPO
        self._initialize()

    def get_ppo(self,id):
        if id in self.ppos: return self.ppos[id]

    def iter(self,f): 
        for ppo in sorted(self.ppos,key=lambda p:(self.ppos[p].location.get_line(),
                                                       int(self.ppos[p].id))): 
            f(self.ppos[ppo])

    def __str__(self):
        lines = []
        def f(ppo): lines.append(str(ppo))
        self.iter(f)
        return '\n'.join(lines)

    def _initialize(self):
        for p in self.xnode.find('ppos').findall('ppo'):
            ppotype = self.cfun.podictionary.read_xml_ppo_type(p)
            id = ppotype.index
            deps = None
            status = po_status[p.get('s','o')]
            if 'deps' in p.attrib:
                level = p.get('deps')
                if level == 'a':
                    ids = p.get('ids')
                    if len(ids) > 0:
                        ids = [int(x) for x in p.get('ids').split(',') ]
                    else:
                        ids = []
                    invs = p.get('invs')
                    if len(invs) > 0:
                        invs = [ int(x) for x in invs.split(',') ]
                    else:
                        invs = []
                    deps = CProofDependencies(self,level,ids,invs)
                else:
                    deps = CProofDependencies(self,level)
            expl = None
            enode = p.find('e')
            if not enode is None:
                expl = enode.get('txt')
            diag = None
            dnode = p.find('d')
            if not dnode is None:
                pinvs = {}
                amsgs = {}
                kmsgs = {}
                for n in dnode.find('invs').findall('arg'):
                    pinvs[int(n.get('a'))] = [ int(x) for x in n.get('i').split(',') ]
                pmsgs =  [ x.get('t') for x in dnode.find('msgs').findall('msg') ]
                for n in dnode.find('amsgs').findall('arg'):
                    arg = int(n.get('a'))
                    msgs = [ x.get('t') for x in n.findall('msg') ]
                    amsgs[arg] = msgs
                knode = dnode.find('kmsgs')
                if not knode is None:
                    for n in knode.findall('key'):
                        key = n.get('k')
                        msgs = [  x.get('t') for x in n.findall('msg') ]
                        kmsgs[key] = msgs
                diag = CProofDiagnostic(pinvs,pmsgs,amsgs,kmsgs)
            self.ppos[id] = CFunctionPPO(self,ppotype,status,deps,expl,diag)
