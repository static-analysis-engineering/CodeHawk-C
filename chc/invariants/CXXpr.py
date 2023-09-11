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
"""Expression."""


from typing import List, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunXprDictionaryRecord, xprregistry)

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunXprDictionary import CFunXprDictionary
    from chc.invariants.CXConstant import CXConstant
    from chc.invariants.CXVariable import CXVariable


xpr_operator_strings = {
    "plus": " + ",
    "minus": " - ",
    "mult": " * ",
    "div": " / * ",
    "ge": " >= ",
    "le": " <= ",
}


class CXXpr(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_var(self) -> bool:
        return False

    @property
    def is_const(self) -> bool:
        return False

    @property
    def is_op(self) -> bool:
        return False

    @property
    def is_attr(self) -> bool:
        return False

    def __str__(self) -> str:
        return "xxpr:" + self.tags[0]


@xprregistry.register_tag("v", CXXpr)
class CXXVar(CXXpr):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CXXpr.__init__(self, xd, ixval)

    @property
    def is_var(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    def __str__(self) -> str:
        return str(self.variable)


@xprregistry.register_tag("c", CXXpr)
class CXXConst(CXXpr):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CXXpr.__init__(self, xd, ixval)

    @property
    def is_const(self) -> bool:
        return True

    @property
    def constant(self) -> "CXConstant":
        return self.xd.get_xcst(self.args[0])

    def __str__(self) -> str:
        return str(self.constant)


@xprregistry.register_tag("x", CXXpr)
class CXXOp(CXXpr):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CXXpr.__init__(self, xd, ixval)

    @property
    def is_op(self) -> bool:
        return True

    @property
    def operator(self) -> str:
        return self.tags[1]

    @property
    def operands(self) -> List["CXXpr"]:
        return [self.xd.get_xpr(i) for i in self.args]

    def __str__(self) -> str:
        operands = self.operands
        if len(operands) == 1:
            return (
                "("
                + xpr_operator_strings[self.operator]
                + str(operands[0]) + ")")
        elif len(operands) == 2:
            return (
                "("
                + str(operands[0])
                + xpr_operator_strings[self.operator]
                + str(operands[1])
                + ")")
        else:
            return (
                "("
                + xpr_operator_strings[self.operator]
                + "("
                + ",".join(str(x) for x in operands)
                + ")")


@xprregistry.register_tag("a", CXXpr)
class CXXAttr(CXXpr):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CXXpr.__init__(self, xd, ixval)

    @property
    def is_attr(self) -> bool:
        return True

    @property
    def attr(self) -> str:
        return self.tags[1]

    @property
    def xpr(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[0])

    def __str__(self) -> str:
        return "attr(" + self.attr + "," + str(self.xpr) + ")"


class CXprList(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def xprs(self) -> List["CXXpr"]:
        return [self.xd.get_xpr(i) for i in self.args]

    def __str__(self) -> str:
        return " && ".join(str(x) for x in self.xprs)


class CXprListList(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def xprlists(self) -> List["CXprList"]:
        return [self.xd.get_xpr_list(i) for i in self.args]

    def __str__(self) -> str:
        return " || ".join("(" + str(x) + ")" for x in self.xprlists)
