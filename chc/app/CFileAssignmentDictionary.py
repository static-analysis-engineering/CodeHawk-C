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

import chc.app.GlobalAssignment as GA

assignment_constructors = {
    'init': lambda x:GA.InitAssignment(*x),
    'g': lambda x:GA.GlobalAssignment(*x),
    'gi': lambda x:GA.GlobalIndexAssignment(*x),
    's': lambda x:GA.StaticAssignment(*x),
    'si': lambda x:GA.StaticIndexAssignment(*x),
    'f': lambda x:GA.FieldAssignment(*x),
    'u': lambda x:GA.UnknownAssignment(*x)
    }

class CFileAssignmentDictionary(object):
    '''Dictionary that encodes assignments to global and static variables and fields.'''

    def __init__(self,cfile):
        self.cfile = cfile
        self.declarations = self.cfile.declarations
        self.dictionary = self.declarations.dictionary
        self.assignment_table = IT.IndexedTable('assignment-table')
        self.function_name_table = IT.IndexedTable('function-name-table')
        self.tables = [
            (self.function_name_table, self._read_xml_function_name_table),
            (self.assignment_table, self._read_xml_assignment_table) ]
        self.initialize()

    def get_function_name(self,ix): return self.function_name_table.retrieve(ix)

    def get_assignment(self,ix): return self.assignment_table.retrieve(ix)

    def mk_assignment_index(self,tags,args):
        def f(index,key): return assignment_constructors[tags[0]]((self,index,tags,args))
        return self.assignment_table.add(IT.get_key(tags,args),f)

    def initialize(self):
        if self.assignment_table.size() > 0: return
        xnode = UF.get_cfile_assignment_dictionary_xnode(self.cfile.capp.path,self.cfile.name)
        if xnode is None: return
        for (t,f) in self.tables: f(xnode.find(t.name))

    def __str__(self):
        lines = []
        for (t,_) in self.tables:
            lines.append(str(t))
        return '\n'.join(lines)

    def _read_xml_function_name_table (self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return GA.GlobalAssignmentFunctionName(*args)
        self.function_name_table.read_xml(txnode,'n',get_value)

    def _read_xml_assignment_table(self,txnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return assignment_constructors[tag](args)
        self.assignment_table.read_xml(txnode,'n',get_value)
