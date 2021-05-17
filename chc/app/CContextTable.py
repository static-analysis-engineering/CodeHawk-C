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

from typing import Any, Callable, List, Tuple, TYPE_CHECKING
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CFile import CFile


class CContextBaseRep(IT.IndexedTableValue):
    """Base class for all context representations."""

    def __init__(self, ctxttable: "CContextTable", index: int, tags: List[str], args: List[int]):
        self.ctxttable = ctxttable
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self) -> Tuple[str, str]:
        return (",".join(self.tags), ",".join([str(x) for x in self.args]))

    def write_xml(self, node: ET.Element) -> None:
        (tagstr, argstr) = self.get_key()
        if len(tagstr) > 0:
            node.set("t", tagstr)
        if len(argstr) > 0:
            node.set("a", argstr)
        node.set("ix", str(self.index))


class CContextNode(CContextBaseRep):
    def __init__(
        self,
        ctxttable: "CContextTable",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CContextBaseRep.__init__(self, ctxttable, index, tags, args)

    def __str__(self) -> str:
        if len(self.args) == 0:
            return "_".join(self.tags)
        else:
            return "_".join(self.tags) + ":" + "_".join([str(x) for x in self.args])


class CfgContext(CContextBaseRep):
    def __init__(
        self,
        ctxttable: "CContextTable",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CContextBaseRep.__init__(self, ctxttable, index, tags, args)

    def get_nodes(self) -> List[CContextNode]:
        return [self.ctxttable.get_node(x) for x in self.args]

    def get_rev_repr(self) -> str:
        revnodes = self.get_nodes()[:]
        revnodes.reverse()
        return "_".join([str(x) for x in revnodes])

    def __str__(self) -> str:
        return "_".join([str(x) for x in self.get_nodes()])


class ExpContext(CContextBaseRep):
    def __init__(
        self,
        ctxttable: "CContextTable",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CContextBaseRep.__init__(self, ctxttable, index, tags, args)

    def get_nodes(self) -> List[CContextNode]:
        return [self.ctxttable.get_node(x) for x in self.args]

    def __str__(self) -> str:
        return "_".join([str(x) for x in self.get_nodes()])


class CProgramContext(CContextBaseRep):
    """Represents a location in a function."""

    def __init__(
        self,
        ctxttable: "CContextTable",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CContextBaseRep.__init__(self, ctxttable, index, tags, args)

    def get_cfg_context(self) -> CfgContext:
        return self.ctxttable.get_cfg_context(self.args[0])

    def get_exp_context(self) -> ExpContext:
        return self.ctxttable.get_exp_context(self.args[1])

    def get_cfg_context_string(self) -> str:
        return str(self.get_cfg_context())

    def __str__(self) -> str:
        return (
            "(" + str(self.get_cfg_context()) + "," + str(self.get_exp_context()) + ")"
        )


class CContextTable(object):
    def __init__(self, cfile: "CFile"):
        self.cfile = cfile
        self.nodetable: IT.IndexedTable[CContextNode] = IT.IndexedTable("nodes")
        self.cfgtable: IT.IndexedTable[CfgContext] = IT.IndexedTable("cfg-contexts")
        self.exptable: IT.IndexedTable[ExpContext] = IT.IndexedTable("exp-contexts")
        self.contexttable: IT.IndexedTable[CProgramContext] = IT.IndexedTable("contexts")
        self.tables: List[Tuple[IT.IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
            (self.nodetable, self._read_xml_node_table),
            (self.cfgtable, self._read_xml_cfg_table),
            (self.exptable, self._read_xml_exp_table),
            (self.contexttable, self._read_xml_context_table),
        ]
        self.initialize()

    def get_node(self, id: int) -> CContextNode:
        return self.nodetable.retrieve(id)

    def get_program_context(self, id: int) -> CProgramContext:
        return self.contexttable.retrieve(id)

    def get_cfg_context(self, id: int) -> CfgContext:
        return self.cfgtable.retrieve(id)

    def get_exp_context(self, id: int) -> ExpContext:
        return self.exptable.retrieve(id)

    def index_node(self, cnode: CContextNode) -> int:
        def f(index: int, key: object) -> CContextNode:
            return CContextNode(self, index, cnode.tags, cnode.args)

        return self.nodetable.add(IT.get_key(cnode.tags, cnode.args), f)

    def index_exp_context(self, expcontext: ExpContext) -> int:
        args = [self.index_node(x) for x in expcontext.get_nodes()]

        def f(index: int, key: object) -> ExpContext:
            return ExpContext(self, index, [], args)

        return self.exptable.add(IT.get_key([], args), f)

    def index_empty_exp_context(self) -> int:
        def f(index: int, key: object) -> ExpContext:
            return ExpContext(self, index, [], [])

        return self.exptable.add(IT.get_key([], []), f)

    def index_cfg_context(self, cfgcontext: CfgContext) -> int:
        args = [self.index_node(x) for x in cfgcontext.get_nodes()]

        def f(index: int, key: object) -> CfgContext:
            return CfgContext(self, index, [], args)

        return self.cfgtable.add(IT.get_key([], args), f)

    def index_context(self, context: CProgramContext) -> int:
        args = [
            self.index_cfg_context(context.get_cfg_context()),
            self.index_exp_context(context.get_exp_context()),
        ]

        def f(index: int, key: object) -> CProgramContext:
            return CProgramContext(self, index, [], args)

        return self.contexttable.add(IT.get_key([], args), f)

    def index_cfg_projection(self, context: CProgramContext) -> int:
        args = [
            self.index_cfg_context(context.get_cfg_context()),
            self.index_empty_exp_context(),
        ]

        def f(index: int, key: object) -> CProgramContext:
            return CProgramContext(self, index, [], args)

        return self.contexttable.add(IT.get_key([], args), f)

    def read_xml_context(self, xnode: ET.Element) -> CProgramContext:
        self.initialize()
        ictxt = xnode.get("ictxt")
        if ictxt is None:
            raise Exception("missing attribute ictxt")
        return self.get_program_context(int(ictxt))

    # assume that python never adds new contexts
    def write_xml_context(self, xnode: ET.Element, context: CProgramContext) -> None:
        xnode.set("ictxt", str(context.index))

    def __str__(self) -> str:
        lines = []
        for v in self.contexttable.values():
            lines.append(str(v))
        lines.append("Nodes:        " + str(self.nodetable.size()))
        lines.append("Cfg contexts: " + str(self.cfgtable.size()))
        lines.append("Exp contexts: " + str(self.exptable.size()))
        lines.append("Program contexts: " + str(self.contexttable.size()))
        return "\n".join(lines)

    def initialize(self, force: bool = False) -> None:
        if self.nodetable.size() > 0 and not force:
            return
        xnode = UF.get_cfile_contexttable_xnode(self.cfile.capp.path, self.cfile.name)
        if xnode is None:
            return
        for (t, _) in self.tables:
            t.reset()
        nodes = xnode.find("nodes")
        if nodes is None:
            raise Exception("missing element `nodes`")
        self._read_xml_node_table(nodes)

        cfg_contexts = xnode.find("cfg-contexts")
        if cfg_contexts is None:
            raise Exception("missing element `cfg-contexts`")
        self._read_xml_cfg_table(cfg_contexts)

        exp_contexts = xnode.find("exp-contexts")
        if exp_contexts is None:
            raise Exception("missing element `exp-contexts`")
        self._read_xml_exp_table(exp_contexts)

        contexts = xnode.find("contexts")
        if contexts is None:
            raise Exception("missing element `contexts`")
        self._read_xml_context_table(contexts)

    def _get_args(self, node: ET.Element) -> List[int]:
        args = node.get("a")
        if args is None:
            return []
        return [int(x) for x in args.split(",")]

    def _get_tags(self, node: ET.Element) -> List[str]:
        tags = node.get("t")
        if tags is None:
            return []
        return tags.split(",")

    def _read_xml_node_table(self, xnode: ET.Element) -> None:
        def getvalue(node: ET.Element) -> CContextNode:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CContextNode(*args)

        self.nodetable.read_xml(xnode, "n", getvalue)

    def _read_xml_cfg_table(self, xnode: ET.Element) -> None:
        def getvalue(node: ET.Element) -> CfgContext:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CfgContext(*args)

        self.cfgtable.read_xml(xnode, "n", getvalue)

    def _read_xml_exp_table(self, xnode: ET.Element) -> None:
        def getvalue(node: ET.Element) -> ExpContext:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return ExpContext(*args)

        self.exptable.read_xml(xnode, "n", getvalue)

    def _read_xml_context_table(self, xnode: ET.Element) -> None:
        def getvalue(node: ET.Element) -> CProgramContext:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CProgramContext(*args)

        self.contexttable.read_xml(xnode, "n", getvalue)
