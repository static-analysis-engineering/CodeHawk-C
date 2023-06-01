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
"""CHIF Variable; identified by name and sequence number."""


from typing import List, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import CFunXprDictionaryRecord

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunXprDictionary import CFunXprDictionary
    from chc.invariants.CVariableDenotation import CVariableDenotation
    from chc.invariants.CXSymbol import CXSymbol


class CXVariable(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def symbol(self) -> "CXSymbol":
        return self.xd.get_symbol(self.args[0])

    @property
    def name(self) -> str:
        return self.symbol.name

    @property
    def seqnr(self) -> int:
        return self.symbol.seqnr

    @property
    def chifvartype(self) -> str:
        return self.tags[0]

    @property
    def is_tmp(self) -> bool:
        return self.seqnr == -1

    @property
    def denotation(self) -> "CVariableDenotation":
        if self.has_denotation():
            return self.vd.get_c_variable_denotation(self.seqnr)
        else:
            raise UF.CHCError("Variable does not have a denotation")

    def has_denotation(self) -> bool:
        return self.seqnr > 0

    def __str__(self) -> str:
        vtype = "S" if self.chifvartype == "sv" else "N"
        return vtype + ":" + str(self.name)
