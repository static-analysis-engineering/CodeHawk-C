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
"""Different types of invariants."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunInvDictionaryRecord, invregistry)

import chc.util.fileutil as UF

from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunInvDictionary import CFunInvDictionary
    from chc.invariants.CNonRelationalValue import CNonRelationalValue
    from chc.invariants.CXVariable import CXVariable
    from chc.invariants.CXXpr import CXXpr


class CInvariantFact(CFunInvDictionaryRecord):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CFunInvDictionaryRecord.__init__(self, invd, ixval)

    @property
    def is_nrv_fact(self) -> bool:
        return False

    @property
    def is_unreachable_fact(self) -> bool:
        return False

    @property
    def is_parameter_constraint(self) -> bool:
        return False

    def __str__(self) -> str:
        return "invariant-fact:" + self.tags[0]


@invregistry.register_tag("nrv", CInvariantFact)
class CInvariantNRVFact(CInvariantFact):
    """Non-relational-value fact (relation with symbolic constants)."""

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CInvariantFact.__init__(self, invd, ixval)

    @property
    def is_nrv_fact(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    @property
    def non_relational_value(self) -> "CNonRelationalValue":
        return self.invd.get_non_relational_value(self.args[1])

    def __str__(self) -> str:
        return (
            str(self.variable).rjust(32)
            + " : "
            + str(self.non_relational_value))


@invregistry.register_tag("pc", CInvariantFact)
class CParameterConstraint(CInvariantFact):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CInvariantFact.__init__(self, invd, ixval)

    @property
    def xpr(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[0])

    @property
    def is_parameter_constraint(self) -> bool:
        return True

    def __str__(self) -> str:
        return str(self.xpr)


@invregistry.register_tag("x", CInvariantFact)
class CUnreachableFact(CInvariantFact):
    """Domain that signals unreachability."""

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CInvariantFact.__init__(self, invd, ixval)

    @property
    def is_unreachable_fact(self) -> bool:
        return True

    @property
    def domain(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "unreachable(" + self.domain + ")"
