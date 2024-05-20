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
"""Numerical value; corresponds to chlib:numerical_t."""


from typing import List, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import CFunXprDictionaryRecord

from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunXprDictionary import CFunXprDictionary


class CXNumerical(CFunXprDictionaryRecord):

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        CFunXprDictionaryRecord.__init__(self, xd, ixval)

    @property
    def value(self) -> int:
        return int(self.tags[0])

    def equals(self, other: "CXNumerical") -> bool:
        return self.value == other.value

    def __str__(self) -> str:
        return self.tags[0]
