# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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

from typing import List, TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

from chc.invariants.CFunDictionaryRecord import xprregistry

from chc.invariants.CXConstant import CXConstant
from chc.invariants.CXNumerical import CXNumerical
from chc.invariants.CXSymbol import CXSymbol
from chc.invariants.CXVariable import CXVariable
from chc.invariants.CXXpr import CXXpr, CXprList, CXprListList


if TYPE_CHECKING:
    from chc.invariants.CFunVarDictionary import CFunVarDictionary


class CFunXprDictionary(object):
    """Indexed analysis expressions."""

    def __init__(self, vd: "CFunVarDictionary", xnode: ET.Element) -> None:
        self._vd = vd
        self.xnode = xnode
        self.numerical_table = IT.IndexedTable("numerical-table")
        self.symbol_table = IT.IndexedTable("symbol-table")
        self.variable_table = IT.IndexedTable("variable-table")
        self.xcst_table = IT.IndexedTable("xcst-table")
        self.xpr_table = IT.IndexedTable("xpr-table")
        self.xpr_list_table = IT.IndexedTable("xpr-list-table")
        self.xpr_list_list_table = IT.IndexedTable("xpr-list-list-table")
        self.tables: List[IT.IndexedTable] = [
            self.numerical_table,
            self.symbol_table,
            self.variable_table,
            self.xcst_table,
            self.xpr_table,
            self.xpr_list_table,
            self.xpr_list_list_table
        ]
        self.initialize(xnode)

    @property
    def vd(self) -> "CFunVarDictionary":
        return self._vd

    # ------------- Retrieve items from dictionary tables --------------------

    def get_numerical(self, ix: int) -> CXNumerical:
        if ix > 0:
            return CXNumerical(self, self.numerical_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal numerical index value: " + str(ix))

    def get_symbol(self, ix: int) -> CXSymbol:
        if ix > 0:
            return CXSymbol(self, self.symbol_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal symbol index value: " + str(ix))

    def get_variable(self, ix: int) -> CXVariable:
        if ix > 0:
            return CXVariable(self, self.variable_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal variable index value: " + str(ix))

    def get_xcst(self, ix: int) -> CXConstant:
        if ix > 0:
            return xprregistry.mk_instance(
                self,
                self.xcst_table.retrieve(ix),
                CXConstant)
        else:
            raise UF.CHCError("Illegal constant index value: " + str(ix))

    def get_xpr(self, ix: int) -> CXXpr:
        if ix > 0:
            return xprregistry.mk_instance(
                self,
                self.xpr_table.retrieve(ix),
                CXXpr)
        else:
            raise UF.CHCError("Illegal xpr index value: " + str(ix))

    def get_xpr_list(self, ix: int) -> CXprList:
        if ix > 0:
            return CXprList(self, self.xpr_list_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal xpr-list index value: " + str(ix))

    def get_xpr_list_list(self, ix: int) -> CXprListList:
        if ix > 0:
            return CXprListList(self, self.xpr_list_list_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal xpr-list-list index value: " + str(ix))

    # ------------ Provide read_xml service ----------------------------------

    # TBD

    # ------------- Index items by category ----------------------------------

    # TBD

    # -------------- Initialize dictionary from file -------------------------

    def initialize(self, xnode: ET.Element, force: bool = False) -> None:
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.reset()
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError(
                    "Xpr dictionary table " + t.name + " not found")

    # ------------------ Printing --------------------------------------------

    def __str__(self) -> str:
        lines: List[str] = []
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)
