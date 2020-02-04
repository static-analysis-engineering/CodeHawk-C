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
import chc.invariants.CInv as CI

non_relational_value_constructors = {
    'sx': lambda x:CI.NRVSymbolicExpr(*x),
    'sb': lambda x:CI.NRVSymbolicBound(*x),
    'iv': lambda x:CI.NRVIntervalValue(*x),
    'bv': lambda x:CI.NRVBaseOffsetValue(*x),
    'rs': lambda x:CI.NRVRegionSet(*x),
    'iz': lambda x:CI.NRVInitializedSet(*x),
    'ps': lambda x:CI.NRVPolicyStateSet(*x)
    }

inv_constructors = {
    'nrv': lambda x:CI.CInvariantNRVFact(*x),
    'x': lambda x:CI.UnreachableFact(*x),
    'pc': lambda x:CI.CParameterConstraintFact(*x)
    }


class CFunInvDictionary(object):

    '''Indexed function invariants.'''

    def __init__(self,vard):
        self.vard = vard
        self.cfun = self.vard.cfun
        self.xd = self.vard.xd
        self.non_relational_value_table = IT.IndexedTable('non-relational-value-table')
        self.invariant_fact_table = IT.IndexedTable('invariant-fact-table')
        self.invariant_list_table = IT.IndexedTable('invariant-list-table')
        self.tables = [
            (self.non_relational_value_table, self._read_xml_non_relational_value_table),
            (self.invariant_fact_table,self._read_xml_invariant_fact_table) ]
        self.initialize()

    # -------------------- Retrieve items from dictionary tables ---------------

    def get_non_relational_value(self,ix):
        return self.non_relational_value_table.retrieve(ix)

    def get_invariant_fact(self,ix):
        return self.invariant_fact_table.retrieve(ix)

    # ------------------- Provide read_xml service -----------------------------

    # TBD

    # --------------------- Index items by category ----------------------------

    # TBD

    # ------------------- Initialize dictionary from file ----------------------

    def initialize(self,force=False):
        xnode = UF.get_invs_xnode(self.cfun.cfile.capp.path,self.cfun.cfile.name,self.cfun.name)
        if not xnode is None:
            xinvs = xnode.find('inv-dictionary')
            for (t,f) in self.tables:
                t.reset()
                f(xinvs.find(t.name))

    # ---------------------- Printing ------------------------------------------

    def __str__(self):
        lines= []
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return '\n'.join(lines)

    # ---------------------------- Internal ------------------------------------

    def _read_xml_non_relational_value_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return non_relational_value_constructors[tag](args)
        self.non_relational_value_table.read_xml(txnode,'n',get_value)

    def _read_xml_invariant_fact_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return inv_constructors[tag](args)
        self.invariant_fact_table.read_xml(txnode,'n',get_value)
