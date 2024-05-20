# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs LLC
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
"""Dictionary of proof obligation types at function level."""

import importlib
import os

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Mapping, TYPE_CHECKING

from chc.proof.AssumptionType import AssumptionType
from chc.proof.CFunPODictionaryRecord import podregistry
from chc.proof.PPOType import PPOType
from chc.proof.SPOType import SPOType

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue


if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.app.CApplication import CApplication
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.proof.CFilePredicateDictionary import CFilePredicateDictionary

importlib.import_module("chc.proof.AssumptionType")
importlib.import_module("chc.proof.PPOType")
importlib.import_module("chc.proof.SPOType")


class CFunPODictionary(object):
    """Indexed function proof obligations."""

    def __init__(
            self,
            cfun: "CFunction",
            xnode: ET.Element) -> None:
        self._cfun = cfun
        self.assumption_type_table = IndexedTable("assumption-table")
        self.ppo_type_table = IndexedTable("ppo-type-table")
        self.spo_type_table = IndexedTable("spo-type-table")
        self.tables = [
            self.assumption_type_table,
            self.ppo_type_table,
            self.spo_type_table]
        self._objmaps: Dict[
            str, Callable[[], Mapping[int, IndexedTableValue]]] = {
            "assumption": self.get_assumption_type_map,
            "ppo": self.get_ppo_type_map,
            "spo": self.get_spo_type_map}
        self.initialize(xnode)

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    @property
    def pd(self) -> "CFilePredicateDictionary":
        return self.cfile.predicatedictionary

    @property
    def interfacedictionary(self) -> "InterfaceDictionary":
        return self.cfile.interfacedictionary

    # ------------------------ Retrieve items from dictionary ----------------

    def get_assumption_type(self, ix: int) -> AssumptionType:
        return podregistry.mk_instance(
            self, self.assumption_type_table.retrieve(ix), AssumptionType)

    def get_assumption_type_map(self) -> Dict[int, IndexedTableValue]:
        return self.assumption_type_table.objectmap(self.get_assumption_type)

    def get_ppo_type(self, ix: int) -> PPOType:
        return podregistry.mk_instance(
            self, self.ppo_type_table.retrieve(ix), PPOType)

    def get_ppo_type_map(self) -> Dict[int, IndexedTableValue]:
        return self.ppo_type_table.objectmap(self.get_ppo_type)

    def get_spo_type(self, ix: int) -> SPOType:
        return podregistry.mk_instance(
            self, self.spo_type_table.retrieve(ix), SPOType)

    def get_spo_type_map(self) -> Dict[int, IndexedTableValue]:
        return self.spo_type_table.objectmap(self.get_spo_type)

    # ------------------------- Provide read/write xml service ---------------

    def read_xml_assumption_type(
            self, txnode: ET.Element, tag: str = "iast") -> AssumptionType:
        optix = txnode.get(tag)
        if optix is not None:
            return self.get_assumption_type(int(optix))
        else:
            raise UF.CHCError("Error in reading xml assumption type")

    def read_xml_ppo_type(self, txnode: ET.Element, tag: str = "ippo") -> PPOType:
        optix = txnode.get(tag)
        if optix is not None:
            return self.get_ppo_type(int(optix))
        else:
            raise UF.CHCError("Error in reading xml ppo type")

    def read_xml_spo_type(self, txnode: ET.Element, tag: str = "ispo") -> SPOType:
        optix = txnode.get(tag)
        if optix is not None:
            return self.get_spo_type(int(optix))
        else:
            raise UF.CHCError("Error in reading xml spo type")

    def write_xml_spo_type(
            self, txnode: ET.Element, spotype: SPOType, tag: str = "ispo") -> None:
        txnode.set(tag, str(self.index_spo_type(spotype.tags, spotype.args)))

    # -------------------------- Index items by category ---------------------

    def index_assumption_type(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> AssumptionType:
            itv = IndexedTableValue(index, tags, args)
            return AssumptionType(self, itv)

        return self.assumption_type_table.add_tags_args(tags, args, f)

    def index_ppo_type(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> PPOType:
            itv = IndexedTableValue(index, tags, args)
            return PPOType(self, itv)

        return self.ppo_type_table.add_tags_args(tags, args, f)

    def index_spo_type(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> SPOType:
            itv = IndexedTableValue(index, tags, args)
            return SPOType(self, itv)

        return self.spo_type_table.add_tags_args(tags, args, f)

    # ---------------------- Initialize dictionary from file -----------------

    def initialize(self, xnode: ET.Element) -> None:
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.reset()
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError(
                    "Table " + t.name + " not found in podictionary")

    # ------------------------------ Printing --------------------------------

    def write_xml(self, node: ET.Element) -> None:

        def f(n: ET.Element, r: IndexedTableValue) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)

    def objectmap_to_string(self, name: str) -> str:
        if name in self._objmaps:
            objmap = self._objmaps[name]()
            lines: List[str] = []
            if len(objmap) == 0:
                lines.append(f"\nTable for {name} is empty\n")
            else:
                lines.append("index  value")
                lines.append("-" * 80)
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "    " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name +  " does not correspond to a table")            

    def __str__(self) -> str:
        lines: List[str] = []
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)
