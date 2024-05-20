# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2019  Kestrel Technology LLC
# Copyright (c) 2020-2024  Henny B. Sipma
# Copyright (c) 2024       Aarno Labs LLC
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

from typing import Iterator, List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CFieldInfo import CFieldInfo


class CompCompatibility:
    """Determines compatibility between two structs."""

    def __init__(self, comp1: "CCompInfo", comp2: "CCompInfo") -> None:
        self._comp1 = comp1
        self._comp2 = comp2

    @property
    def comp1(self) -> "CCompInfo":
        return self._comp1

    @property
    def comp2(self) -> "CCompInfo":
        return self._comp2

    def are_structurally_compatible(self) -> bool:
        """Returns true if comp1 and comp2 have the same fields.

        Note: The field types are not necessarily compatible.
        """
        if self.comp1.fieldcount == self.comp2.fieldcount:
            return set(self.comp1.fieldnames) == set(self.comp2.fieldnames)
        return False

    def are_shallow_compatible(
            self, incompatibles: Set[Tuple[str, str]] = set([])) -> bool:
        """Returns true if comp1 and comp2 are structurally compatible.

        Note: This means the the types of comp1 and comp2 are structurally
        compatible taking into account a list of pairs of struct tags that
        are explicitly declared incompatible.
        """
        if self.are_structurally_compatible():
            return self._forall_shallowcompatiblefieldtype(incompatibles)
        return False

    def __str__(self) -> str:
        if self.comp1.index == self.comp2.index:
            return "identical"
        if self.are_shallow_compatible():
            return "shallow compatible (without incompatibles declared)"
        if self.are_structurally_compatible():
            return self._find_incompatiblefieldtype()
        return "not structurally compatible"

    def _find_incompatiblefieldtype(self) -> str:
        fieldpairs: Iterator[Tuple["CFieldInfo", "CFieldInfo"]] = zip(
            self.comp1.fields, self.comp2.fields)
        for (finfo1, finfo2) in fieldpairs:
            t1 = finfo1.ftype
            t2 = finfo2.ftype
            if not t1.equal(t2):
                return "t1: " + str(t1) + "\nt2: " + str(t2)
        return "no incompatible fields found"

    def _forall_shallowcompatiblefieldtype(
            self, incompatibles: Set[Tuple[str, str]] = set([])) -> bool:
        fieldpairs: Iterator[Tuple["CFieldInfo", "CFieldInfo"]] = zip(
            self.comp1.fields, self.comp2.fields)
        for (finfo1, finfo2) in fieldpairs:
            t1 = finfo1.ftype.expand()
            t2 = finfo2.ftype.expand()
            if not t1.equal(t2):
                return False
        return True
