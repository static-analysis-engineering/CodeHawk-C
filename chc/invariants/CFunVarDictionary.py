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

import chc.invariants.CVar as CV

from chc.invariants.CFunXprDictionary import CFunXprDictionary

memory_base_constructors = {
    'null':lambda x:CV.MemoryBaseNull(*x),
    'str':lambda x:CV.MemoryBaseStringLiteral(*x),
    'sa':lambda x:CV.MemoryBaseStackAddress(*x),
    'saa':lambda x:CV.MemoryBaseAllocStackAddress(*x),
    'ga':lambda x:CV.MemoryBaseGlobalAddress(*x),
    'ha':lambda x:CV.MemoryBaseHeapAddress(*x),
    'bv':lambda x:CV.MemoryBaseBaseVar(*x),
    'ui':lambda x:CV.MemoryBaseUninterpreted(*x),
    'fr':lambda x:CV.MemoryBaseFreed(*x)
    }

constant_value_variable_constructors = {
    'iv':lambda x:CV.CVVInitialValue(*x),
    'frv':lambda x:CV.CVVFunctionReturnValue(*x),
    'erv':lambda x:CV.CVVExpFunctionReturnValue(*x),
    'fsev':lambda x:CV.CVVSideEffectValue(*x),
    'esev':lambda x:CV.CVVExpSideEffectValue(*x),
    'sv':lambda x:CV.CVVSymbolicValue(*x),
    'tv':lambda x:CV.CVVTaintedValue(*x),
    'bs':lambda x:CV.CVVByteSequence(*x),
    'ma':lambda x:CV.CVVMemoryAddress(*x)
    }

c_variable_denotation_constructors = {
    'libv':lambda x:CV.CVLibraryVariable(*x),
    'lv':lambda x:CV.LocalVariable(*x),
    'gv':lambda x:CV.GlobalVariable(*x),
    'mv':lambda x:CV.MemoryVariable(*x),
    'mrv':lambda x:CV.MemoryRegionVariable(*x),
    'rv':lambda x:CV.ReturnVariable(*x),
    'fv':lambda x:CV.FieldVariable(*x),
    'cv':lambda x:CV.CheckVariable(*x),
    'av':lambda x:CV.AuxiliaryVariable(*x),
    'xv':lambda x:CV.AugmentationVariable(*x)
    }

class CFunVarDictionary (object):
    '''Indexed analysis variables.'''

    def __init__(self,fdecls):
        self.fdecls = fdecls
        self.cfun = self.fdecls.cfun
        self.cfile = self.cfun.cfile
        self.xd = CFunXprDictionary(self)
        self.memory_base_table = IT.IndexedTable('memory-base-table')
        self.memory_reference_data_table = IT.IndexedTable('memory-reference-data-table')
        self.constant_value_variable_table = IT.IndexedTable('constant-value-variable-table')
        self.c_variable_denotation_table = IT.IndexedTable('c-variable-denotation-table')
        self.tables = [
            (self.memory_base_table,self._read_xml_memory_base_table),
            (self.memory_reference_data_table,self._read_xml_memory_reference_data_table),
            (self.constant_value_variable_table,self._read_xml_constant_value_variable_table),
            (self.c_variable_denotation_table,self._read_xml_c_variable_denotation_table) ]

    # -------------------- Retrieve items from dictionary tables ---------------

    def get_memory_base(self,ix):
        return self.memory_base_table.retrieve(ix)

    def get_memory_reference_data(self,ix):
        return self.memory_reference_data_table.retrieve(ix)

    def get_constant_value_variable(self,ix):
        return self.constant_value_variable_table.retrieve(ix)

    def get_c_variable_denotation(self,ix):
        return self.c_variable_denotation_table.retrieve(ix)

    # ------------------- Provide read_xml service -----------------------------

    # TBD

    # ------------------- Index items by category ------------------------------

    # TBD

    # ------------------- Initialize dictionary from file ----------------------

    def initialize(self,force=False):
        xnode = UF.get_vars_xnode(self.cfun.cfile.capp.path,self.cfun.cfile.name,self.cfun.name)
        if not xnode is None:
            xvard = xnode.find('var-dictionary')
            self.xd.initialize(xvard.find('xpr-dictionary'))
            for (t,f) in self.tables:
                t.reset()
                f(xvard.find(t.name))
   # ---------------------- Printing ------------------------------------------

    def __str__(self):
        lines = []
        lines.append('Xpr dictionary')
        lines.append('-' * 80)
        lines.append(str(self.xd))
        lines.append('\nVar dictionary')
        lines.append('-' * 80)
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return '\n'.join(lines)

    # ----------------------- Internal -----------------------------------------

    def _read_xml_memory_base_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return memory_base_constructors[tag](args)
        self.memory_base_table.read_xml(txnode,'n',get_value)

    def _read_xml_memory_reference_data_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CV.MemoryReferenceData(*args)
        self.memory_reference_data_table.read_xml(txnode,'n',get_value)

    def _read_xml_constant_value_variable_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return constant_value_variable_constructors[tag](args)
        self.constant_value_variable_table.read_xml(txnode,'n',get_value)

    def _read_xml_c_variable_denotation_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return c_variable_denotation_constructors[tag](args)
        self.c_variable_denotation_table.read_xml(txnode,'n',get_value)
