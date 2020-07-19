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

import os

import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
import chc.invariants.CXpr as CX

xcst_constructors = {
    'ss':lambda x:CX.CXCSymSet(*x),
    'ic':lambda x:CX.CXIntConst(*x),
    'bc':lambda x:CX.CXCBoolConst(*x),
    'r':lambda x:CX.CXRandom(*x),
    'ui':lambda x:CX.CXUnknownInt(*x),
    'us':lambda x:CX.CXUnknownSet(*x)
    }

xpr_constructors = {
    'v':lambda x:CX.CXVar(*x),
    'c':lambda x:CX.CXConst(*x),
    'x':lambda x:CX.CXOp(*x),
    'a':lambda x:CX.CXAttr(*x)
    }


class CFunXprDictionary (object):
    '''Indexed analysis expressions.'''

    def __init__(self,vd):
        self.vd = vd
        self.numerical_table = IT.IndexedTable('numerical-table')
        self.symbol_table = IT.IndexedTable('symbol-table')
        self.variable_table = IT.IndexedTable('variable-table')
        self.xcst_table = IT.IndexedTable('xcst-table')
        self.xpr_table = IT.IndexedTable('xpr-table')
        self.xpr_list_table = IT.IndexedTable('xpr-list-table')
        self.xpr_list_list_table = IT.IndexedTable('xpr-list-list-table')
        self.tables = [
            (self.numerical_table,self._read_xml_numerical_table),
            (self.symbol_table,self._read_xml_symbol_table),
            (self.variable_table,self._read_xml_variable_table),
            (self.xcst_table,self._read_xml_xcst_table),
            (self.xpr_table,self._read_xml_xpr_table),
            (self.xpr_list_table,self._read_xml_xpr_list_table),
            (self.xpr_list_list_table,self._read_xml_xpr_list_list_table) ]

    # ------------- Retrieve items from dictionary tables ----------------------

    def get_numerical(self,ix):
        if ix > 0:
            return self.numerical_table.retrieve(ix)

    def get_symbol(self,ix): return self.symbol_table.retrieve(ix)

    def get_variable(self,ix): return self.variable_table.retrieve(ix)

    def get_xcst(self,ix): return self.xcst_table.retrieve(ix)

    def get_xpr(self,ix): return self.xpr_table.retrieve(ix)

    def get_xpr_list(self,ix): return self.xpr_list_table.retrieve(ix)

    def get_xpr_list_list(self,ix): return self.xpr_list_list_table.retrieve(ix)

    # ------------ Provide read_xml service ------------------------------------

    # TBD

    # ------------- Index items by category ------------------------------------

    # TBD

    # -------------- Initialize dictionary from file ---------------------------

    def initialize(self,xnode,force=False):
        if xnode is None:
            print('no xpr dictionary found')
            return
        for (t,f) in self.tables: f(xnode.find(t.name))

    # ------------------ Printing ----------------------------------------------

    def __str__(self):
        lines = []
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return '\n'.join(lines)

    # ------------------------ Internal ----------------------------------------

    def _read_xml_numerical_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CX.CXNumerical(*args)
        self.numerical_table.read_xml(txnode,'n',get_value)

    def _read_xml_symbol_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CX.CXSymbol(*args)
        self.symbol_table.read_xml(txnode,'n',get_value)

    def _read_xml_variable_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CX.CXVariable(*args)
        self.variable_table.read_xml(txnode,'n',get_value)

    def _read_xml_xcst_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return xcst_constructors[tag](args)
        self.xcst_table.read_xml(txnode,'n',get_value)

    def _read_xml_xpr_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return xpr_constructors[tag](args)
        self.xpr_table.read_xml(txnode,'n',get_value)

    def _read_xml_xpr_list_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CX.CXprList(*args)
        self.xpr_list_table.read_xml(txnode,'n',get_value)

    def _read_xml_xpr_list_list_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CX.CXprListList(*args)
        self.xpr_list_list_table.read_xml(txnode,'n',get_value)
            
