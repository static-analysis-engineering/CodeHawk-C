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

from typing import List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

from chc.invariants.CFunDictionaryRecord import varregistry

from chc.invariants.CFunXprDictionary import CFunXprDictionary
from chc.invariants.CVariableDenotation import CVariableDenotation
from chc.invariants.CVConstantValueVariable import CVConstantValueVariable
from chc.invariants.CVMemoryBase import CVMemoryBase
from chc.invariants.CVMemoryReferenceData import CVMemoryReferenceData


if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFunction import CFunction
    from chc.app.CFunDeclarations import CFunDeclarations


class CFunVarDictionary:
    """Indexed analysis variables."""

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        self._cfun = cfun
        self.xnode = xnode
        self._xd: Optional[CFunXprDictionary] = None
        self.memory_base_table = IT.IndexedTable("memory-base-table")
        self.memory_reference_data_table = IT.IndexedTable(
            "memory-reference-data-table")
        self.constant_value_variable_table = IT.IndexedTable(
            "constant-value-variable-table")
        self.c_variable_denotation_table = IT.IndexedTable(
            "c-variable-denotation-table")
        self.tables: List[IT.IndexedTable] = [
            self.memory_base_table,
            self.memory_reference_data_table,
            self.constant_value_variable_table,
            self.c_variable_denotation_table
        ]
        self.initialize(xnode)

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def cdictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def fundecls(self) -> "CFunDeclarations":
        return self.cfun.cfundecls

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def xd(self) -> CFunXprDictionary:
        if self._xd is None:
            xprd = self.xnode.find("xpr-dictionary")
            if xprd is None:
                raise UF.CHCError(
                    "Xpr dictionary not found in variable dictionary for "
                    + "function " + self.cfun.name)
            else:
                self._xd = CFunXprDictionary(self, xprd)
        return self._xd

    # -------------------- Retrieve items from dictionary tables -------------

    def get_memory_base(self, ix: int) -> CVMemoryBase:
        if ix > 0:
            return varregistry.mk_instance(
                self, self.memory_base_table.retrieve(ix), CVMemoryBase)
        else:
            raise UF.CHCError("Illegal memory base index value: " + str(ix))

    def get_memory_reference_data(self, ix: int) -> CVMemoryReferenceData:
        if ix > 0:
            return CVMemoryReferenceData(
                self, self.memory_reference_data_table.retrieve(ix))
        else:
            raise UF.CHCError("Illegal memory reference data index value")

    def get_constant_value_variable(self, ix: int) -> CVConstantValueVariable:
        if ix > 0:
            return varregistry.mk_instance(
                self,
                self.constant_value_variable_table.retrieve(ix),
                CVConstantValueVariable)
        else:
            raise UF.CHCError("Illegal constant-value-variable index value: " + str(ix))

    def get_c_variable_denotation(self, ix: int) -> CVariableDenotation:
        if ix > 0:
            return varregistry.mk_instance(
                self,
                self.c_variable_denotation_table.retrieve(ix),
                CVariableDenotation)
        else:
            raise UF.CHCError("Illegal c-variable denotation index value: " + str(ix))

    # ------------------- Provide read_xml service ---------------------------

    # TBD

    # ------------------- Index items by category ----------------------------

    # TBD

    # ------------------- Initialize dictionary from file --------------------

    def initialize(self, xnode: ET.Element) -> None:
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.reset()
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError(
                    "Var dictionary table " + t.name + " not found")

    # ---------------------- Printing ------------------------------------------

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("Xpr dictionary")
        lines.append("-" * 80)
        lines.append(str(self.xd))
        lines.append("\nVar dictionary")
        lines.append("-" * 80)
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)
