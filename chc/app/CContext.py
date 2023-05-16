# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2021-2022 Henny Sipma
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

from typing import List, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.app.CContextDictionary import CContextDictionary


class CContextDictionaryRecord(IndexedTableValue):

    def __init__(self, cxd: "CContextDictionary", ixval: IndexedTableValue
    ) -> None:
        IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._cxd = cxd

    @property
    def cxd(self) -> "CContextDictionary":
        return self._cxd

    def __str__(self) -> str:
        return "context-record:" + str(self.key)


class CContextNode(CContextDictionaryRecord):
    """Node in an expression or control-flow-graph context.

    tags[0]: name of the node
    tags[1..]: additional info on the node, e.g. field name in struct expression
    args[0]: stmt.id for statements, instr sequence number for instructions
    """

    def __init__(self, cxd: "CContextDictionary", ixval: IndexedTableValue
    ) -> None:
        CContextDictionaryRecord.__init__(self, cxd, ixval)

    @property
    def name(self) -> str:
        return self.tags[0]

    @property
    def data_id(self) -> int:
        if len (self.args) > 0:
            return self.args[0]
        else:
            raise UF.CHCError(
                "Context node " + self.name + " does not have a data-id")

    def __str__(self) -> str:
        if len(self.args) == 0:
            return "_".join(self.tags)
        else:
            return (
                "_".join(self.tags) + ":" + "_".join(str(x) for x in self.args))



class CfgContext(CContextDictionaryRecord):
    """Control-flow-graph context expressed by a list of context nodes.

    args[0..]: indices of context nodes in the context dictionary, inner context
    last
    """

    def __init__(self, cxd: "CContextDictionary", ixval: IndexedTableValue
    ) -> None:
        CContextDictionaryRecord.__init__(self, cxd, ixval)

    @property
    def nodes(self) -> List[CContextNode]:
        return [self.cxd.get_node(x) for x in self.args]

    def __str__(self) -> str:
        return "cfg:" + "_".join(str(x) for x in self.nodes)


class ExpContext(CContextDictionaryRecord):
    """Expression nesting context expressed by a list of context nodes.

    args[0..]: indices of context nodes in the context dictionary, inner context
    last
    """

    def __init__(self, cxd: "CContextDictionary", ixval: IndexedTableValue
    ) -> None:
        CContextDictionaryRecord.__init__(self, cxd, ixval)

    @property
    def nodes(self) -> List[CContextNode]:
        return [self.cxd.get_node(x) for x in self.args]

    def __str__(self) -> str:
        return "exp:" + "_".join(str(x) for x in self.nodes)


class ProgramContext(CContextDictionaryRecord):
    """Precise structural placement within a function (relative to ast, exps).

    args[0]: index of cfg context in context dictionary
    args[1]: index of exp context in context dictionary
    """

    def __init__(self, cxd: "CContextDictionary", ixval: IndexedTableValue
    ) -> None:
        CContextDictionaryRecord.__init__(self, cxd, ixval)

    @property
    def cfg_context(self) -> CfgContext:
        return self.cxd.get_cfg_context(self.args[0])

    @property
    def exp_context(self) -> ExpContext:
        return self.cxd.get_exp_context(self.args[1])

    def __str__(self) -> str:
        return "(" + str(self.cfg_context) + ", " + str(self.exp_context) + ")"

