# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2021-2022 Henny B. Sipma
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
"""Dictionary for program context specifications."""

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Mapping, TYPE_CHECKING

from chc.app.CContext import CContextNode, CfgContext, ExpContext, ProgramContext

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue

if TYPE_CHECKING:
    from chc.app.CFile import CFile


class CContextDictionary:

    def __init__(self, cfile: "CFile", xnode: ET.Element) -> None:
        self._cfile = cfile
        self.node_table = IndexedTable("nodes")
        self.cfgcontext_table = IndexedTable("cfg-contexts")
        self.expcontext_table = IndexedTable("exp-contexts")
        self.context_table = IndexedTable("contexts")
        self.tables = [
            self.node_table,
            self.cfgcontext_table,
            self.expcontext_table,
            self.context_table]
        self._objmaps: Dict[
            str, Callable[[], Mapping[int, IndexedTableValue]]] = {
            "cfg": self.get_cfg_context_map,
            "exp": self.get_exp_context_map,
            "p": self.get_program_context_map}
        self.initialize(xnode)

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    # --------------------- retrieve items from dictionary tables --------------

    def get_node(self, ix: int) -> CContextNode:
        return CContextNode(self, self.node_table.retrieve(ix))

    def get_cfg_context(self, ix: int) -> CfgContext:
        return CfgContext(self, self.cfgcontext_table.retrieve(ix))

    def get_cfg_context_map(self) -> Dict[int, IndexedTableValue]:
        return self.cfgcontext_table.objectmap(self.get_cfg_context)

    def get_exp_context(self, ix: int) -> ExpContext:
        return ExpContext(self, self.expcontext_table.retrieve(ix))

    def get_exp_context_map(self) -> Dict[int, IndexedTableValue]:
        return self.expcontext_table.objectmap(self.get_exp_context)

    def get_program_context(self, ix: int) -> ProgramContext:
        return ProgramContext(self, self.context_table.retrieve(ix))

    def get_program_context_map(self) -> Dict[int, IndexedTableValue]:
        return self.context_table.objectmap(self.get_program_context)

    # ----------------------- Printing -----------------------------------------

    def objectmap_to_string(self, name: str) -> str:
        if name in self._objmaps:
            objmap = self._objmaps[name]()
            lines: List[str] = []
            if len(objmap) > 0:
                lines.append("index  value")
                lines.append("-" * 80)
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "    " + str(obj))
            else:
                lines.append(f"Table for {name} is empty")
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name + " does not correspond to a table")

    # ------------------- create new contexts ----------------------------------

    def index_node(self, cnode: CContextNode) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CContextNode:
            itv = IndexedTableValue(index, tags, args)
            return CContextNode(self, itv)

        return self.node_table.add_tags_args(cnode.tags, cnode.args, f)

    def index_exp_context(self, expcontext: ExpContext) -> int:
        args = [self.index_node(x) for x in expcontext.nodes]

        def f(index: int, tags: List[str], args: List[int]) -> ExpContext:
            itv = IndexedTableValue(index, tags, args)
            return ExpContext(self, itv)

        return self.expcontext_table.add_tags_args([], args, f)

    def index_empty_exp_context(self) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> ExpContext:
            itv = IndexedTableValue(index, tags, args)
            return ExpContext(self, itv)

        return self.expcontext_table.add_tags_args([], [], f)

    def index_cfg_context(self, cfgcontext: CfgContext) -> int:
        args = [self.index_node(x) for x in cfgcontext.nodes]

        def f(index: int, tags: List[str], args: List[int]) -> CfgContext:
            itv = IndexedTableValue(index, tags, args)
            return CfgContext(self, itv)

        return self.cfgcontext_table.add_tags_args([], args, f)

    def index_context(self, context: ProgramContext) -> int:
        args = [
            self.index_cfg_context(context.cfg_context),
            self.index_exp_context(context.exp_context)]

        def f(index: int, tags: List[str], args: List[int]) -> ProgramContext:
            itv = IndexedTableValue(index, tags, args)
            return ProgramContext(self, itv)

        return self.context_table.add_tags_args([], args, f)

    def index_cfg_projection(self, context: ProgramContext) -> int:
        args = [
            self.index_cfg_context(context.cfg_context),
            self.index_empty_exp_context()]

        def f(index: int, tags: List[str], args: List[int]) -> ProgramContext:
            itv = IndexedTableValue(index, tags, args)
            return ProgramContext(self, itv)

        return self.context_table.add_tags_args([], args, f)

    def read_xml_context(self, xnode: ET.Element) -> ProgramContext:
        ictxt = xnode.get("ictxt")
        if ictxt is None:
            raise UF.CHCError("ictxt attribute is missing")
        return self.get_program_context(int(ictxt))

    # assume that python never adds new contexts
    def write_xml_context(
            self, xnode: ET.Element, context: ProgramContext) -> None:
        xnode.set("ictxt", str(context.index))

    # --------------------- initialize dictionary from file --------------------

    def initialize(self, xnode: ET.Element) -> None:
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.reset()
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError(
                    "Table " + t.name + " not found in context file")
