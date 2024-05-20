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
"""Constant value."""


from typing import List, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunXprDictionaryRecord, xprregistry)

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunXprDictionary import CFunXprDictionary
    from chc.invariants.CXNumerical import CXNumerical
    from chc.invariants.CXSymbol import CXSymbol


class CXConstant(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_symset(self) -> bool:
        return False

    @property
    def is_intconst(self) -> bool:
        return False

    @property
    def is_boolconst(self) -> bool:
        return False

    @property
    def is_random(self) -> bool:
        return False

    @property
    def is_unknown_int(self) -> bool:
        return False

    @property
    def is_unknown_set(self) -> bool:
        return False

    def __str__(self) -> str:
        return "xcst:" + self.tags[0]


@xprregistry.register_tag("ss", CXConstant)
class CXSymSet(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CXConstant.__init__(self, xd, ixval)

    @property
    def is_symset(self) -> bool:
        return True

    @property
    def symbols(self) -> List["CXSymbol"]:
        return [self.xd.get_symbol(i) for i in self.args]

    def __str__(self) -> str:
        return "[" + ",".join(str(x) for x in self.symbols) + "]"


@xprregistry.register_tag("ic", CXConstant)
class CXIntConst(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_intconst(self) -> bool:
        return True

    @property
    def constvalue(self) -> "CXNumerical":
        return self.xd.get_numerical(self.args[0])

    def __str__(self) -> str:
        return str(self.constvalue)


@xprregistry.register_tag("bc", CXConstant)
class CXBoolConst(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_boolconst(self) -> bool:
        return True

    @property
    def is_true(self) -> bool:
        return self.args[0] == 1

    @property
    def is_false(self) -> bool:
        return self.args[0] == 0

    def __str__(self) -> str:
        return "true" if self.is_true else "false"


@xprregistry.register_tag("r", CXConstant)
class CXRandom(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_random(self) -> bool:
        return True

    def __str__(self) -> str:
        return "random"


@xprregistry.register_tag("ui", CXConstant)
class CXUnknownInt(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_unknown_int(self) -> bool:
        return True

    def __str__(self) -> str:
        return "unknown int"


@xprregistry.register_tag("us", CXConstant)
class CXUnknownSet(CXConstant):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def is_unknown_set(self) -> bool:
        return True

    def __str__(self) -> str:
        return "unknown set"
