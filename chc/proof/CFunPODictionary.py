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
import chc.util.IndexedTable as IT

import chc.proof.AssumptionType as AT
import chc.proof.POType as PP

assumption_type_constructors = {
    'la': lambda x:AT.ATLocalAssumptionType(*x),
    'aa': lambda x:AT.ATApiAssumptionType(*x),
    'gi': lambda x:AT.ATGlobalApiAssumptionType(*x),
    'ca': lambda x:AT.ATPostconditionType(*x),
    'ga': lambda x:AT.ATGlobalAssumptionType(*x)
    }

ppo_type_constructors = {
    'p': lambda x:PP.PPOType(*x),
    'pl': lambda x:PP.PPOLibType(*x)
    }

spo_type_constructors = {
    'cs': lambda x:PP.CallsiteSPOType(*x),
    'rs': lambda x:PP.ReturnsiteSPOType(*x),
    'ls': lambda x:PP.LocalSPOType(*x)
    }

class CFunPODictionary(object):
    """Indexed function proof obligations."""

    def __init__(self,cfun):
        self.cfun = cfun
        self.pd = self.cfun.cfile.predicatedictionary
        self.assumption_type_table = IT.IndexedTable('assumption-table')
        self.ppo_type_table = IT.IndexedTable('ppo-type-table')
        self.spo_type_table = IT.IndexedTable('spo-type-table')
        self.tables = [
            (self.assumption_type_table,self._read_xml_assumption_type_table),
            (self.ppo_type_table, self._read_xml_ppo_type_table),
            (self.spo_type_table, self._read_xml_spo_type_table) ]
        self.initialize()

    # ------------------------ Retrieve items from dictionary ------------------

    def get_assumption_type(self,ix):
        return self.assumption_type_table.retrieve(ix)

    def get_ppo_type(self,ix):
        return self.ppo_type_table.retrieve(ix)

    def get_spo_type(self,ix):
        return self.spo_type_table.retrieve(ix)

    # ------------------------- Provide read/write xml service -----------------

    def read_xml_assumption_type(self,txnode,tag='iast'):
        return self.get_assumption_type(int(txnode.get(tag)))

    def read_xml_ppo_type(self,txnode,tag='ippo'):
        return self.get_ppo_type(int(txnode.get(tag)))

    def read_xml_spo_type(self,txnode,tag='ispo'):
        return self.get_spo_type(int(txnode.get(tag)))

    def write_xml_spo_type(self,txnode,spotype,tag='ispo'):
        txnode.set(tag,self.index_spo_type(spotype.tags,spotype.args))

    # -------------------------- Index items by category -----------------------

    def index_assumption_type(self,tags,args):
        def f(index,key): return assumption_type_constructors[tags[0]]((self,index,tags,args))
        return self.assumption_type_table.add(IT.get_key(tags,args),f)

    def index_ppo_type(self,tags,args):
        def f(index,key): return ppo_type_constructors[tags[0]]((self,index,tags,args))
        return self.ppo_type_table.add(IT.get_key(tags,args),f)

    def index_spo_type(self,tags,args):
        def f(index,key): return spo_type_constructors[tags[0]]((self,index,tags,args))
        return self.spo_type_table.add(IT.get_key(tags,args),f)

    # ---------------------- Initialize dictionary from file -------------------

    def initialize(self):
        xnode = UF.get_pod_xnode(self.cfun.cfile.capp.path,self.cfun.cfile.name,self.cfun.name)
        if not xnode is None:
            for (t,f) in self.tables:
                t.reset()
                f(xnode.find(t.name))

    # ------------------------------ Printing ----------------------------------

    def write_xml(self,node):
        def f(n,r):r.write_xml(n)
        for (t,_) in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode,f)
            node.append(tnode)

    def __str__(self):
        lines = []
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return '\n'.join(lines)

    # -------------------------------- Internal --------------------------------

    def _read_xml_assumption_type_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return assumption_type_constructors[tag](args)
        self.assumption_type_table.read_xml(txnode,'n',get_value)

    def _read_xml_ppo_type_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return ppo_type_constructors[tag](args)
        self.ppo_type_table.read_xml(txnode,'n',get_value)

    def _read_xml_spo_type_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return spo_type_constructors[tag](args)
        self.spo_type_table.read_xml(txnode,'n',get_value)
    
