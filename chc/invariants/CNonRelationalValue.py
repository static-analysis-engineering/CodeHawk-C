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


from typing import Any, Dict, List, Optional, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunInvDictionaryRecord, invregistry)

import chc.util.fileutil as UF

from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.app.CLocation import CLocation
    from chc.app.COffset import COffset
    from chc.app.CVarInfo import CVarInfo
    from chc.app.CTyp import CTyp
    from chc.invariants.CFunInvDictionary import CFunInvDictionary
    from chc.invariants.CVMemoryReferenceData import CVMemoryReferenceData
    from chc.invariants.CXNumerical import CXNumerical
    from chc.invariants.CXSymbol import CXSymbol
    from chc.invariants.CXVariable import CXVariable
    from chc.invariants.CXXpr import CXXpr, CXprListList


class CNonRelationalValue(CFunInvDictionaryRecord):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CFunInvDictionaryRecord.__init__(self, invd, ixval)

    @property
    def is_symbolic_expr(self) -> bool:
        return False

    @property
    def is_symbolic_bound(self) -> bool:
        return False

    @property
    def is_interval_value(self) -> bool:
        return False

    @property
    def is_base_offset_value(self) -> bool:
        return False

    @property
    def is_region_set(self) -> bool:
        return False

    @property
    def is_initialized_set(self) -> bool:
        return False

    @property
    def is_policy_state_set(self) -> bool:
        return False

    def __str__(self) -> str:
        return "nrv:" + self.tags[0]


@invregistry.register_tag("sx", CNonRelationalValue)
class CNRVSymbolicExpr(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_symbolic_expr(self) -> bool:
        return True

    @property
    def xpr(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[0])

    def __str__(self) -> str:
        return "sx:" + str(self.xpr)


@invregistry.register_tag("sb", CNonRelationalValue)
class CNRVSymbolicBound(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_symbolic_bound(self) -> bool:
        return True

    @property
    def bound(self) -> "CXprListList":
        return self.xd.get_xpr_list_list(self.args[0])

    @property
    def boundtype(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return self.boundtype + ":" + str(self.bound)


@invregistry.register_tag("iv", CNonRelationalValue)
class CNRVIntervalValue(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_interval_value(self) -> bool:
        return True

    @property
    def lowerbound(self) -> Optional["CXNumerical"]:
        if self.args[0] >= 0:
            return self.xd.get_numerical(self.args[0])
        return None

    @property
    def upperbound(self) -> Optional["CXNumerical"]:
        if self.args[1] >= 0:
            return self.xd.get_numerical(self.args[1])
        return None

    def has_lowerbound(self) -> bool:
        return self.lowerbound is not None

    def has_upperbound(self) -> bool:
        return self.upperbound is not None

    def has_value(self) -> bool:
        if self.lowerbound is not None and self.upperbound is not None:
            return self.lowerbound.equals(self.upperbound)
        return False

    @property
    def value(self) -> "CXNumerical":
        if self.has_value() and self.lowerbound is not None:
            return self.lowerbound
        else:
            raise UF.CHCError(
                "NRV Interval does not have a value: " + str(self))

    def __str__(self) -> str:
        if self.has_value():
            return "iv:" + str(self.value)
        else:
            lb = self.lowerbound
            ub = self.upperbound
            plb = "<-" if lb is None else "[" + str(lb)
            pub = "->" if ub is None else str(ub) + "]"
            return "iv:" + plb + ":" + pub


@invregistry.register_tag("bv", CNonRelationalValue)
class CNRVBaseOffsetValue(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_base_offset_value(self) -> bool:
        return True

    @property
    def addresstype(self) -> str:
        return self.tags[1]

    @property
    def xpr(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[0])

    @property
    def lowerbound(self) -> Optional["CXNumerical"]:
        if self.args[1] >= 0:
            return self.xd.get_numerical(self.args[1])
        else:
            return None

    @property
    def upperbound(self) -> Optional["CXNumerical"]:
        if self.args[2] >= 0:
            return self.xd.get_numerical(self.args[2])
        else:
            return None

    @property
    def canbenull(self) -> bool:
        return self.args[3] == 1

    def has_lowerbound(self) -> bool:
        return self.lowerbound is not None

    def has_upperbound(self) -> bool:
        return self.upperbound is not None

    def has_offsetvalue(self) -> bool:
        if self.lowerbound is not None and self.upperbound is not None:
            return self.lowerbound == self.upperbound
        else:
            return False

    @property
    def offsetvalue(self) -> "CXNumerical":
        if self.has_offsetvalue() and self.lowerbound is not None:
            return self.lowerbound
        else:
            raise UF.CHCError(
                "Base offset does not have a singleton offsetvalue: " + str(self))

    def __str__(self) -> str:
        pcbn = ", null:" + ("maybe" if self.canbenull else "no")
        if self.has_offsetvalue():
            return "bv:" + str(self.xpr) + str(self.offsetvalue) + pcbn
        else:
            lb = self.lowerbound
            ub = self.upperbound
            plb = "<-" if lb is None else "[" + str(lb)
            pub = "->" if ub is None else str(ub) + ")"
            return "bv:" + str(self.xpr) + ":" + plb + ";" + pub + pcbn


@invregistry.register_tag("rs", CNonRelationalValue)
class CNRVRegionSet(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_region_set(self) -> bool:
        return True

    @property
    def regions(self) -> List["CXSymbol"]:
        return [self.xd.get_symbol(i) for i in self.args]

    @property
    def size(self) -> int:
        return len(self.regions)

    def __str__(self) -> str:
        return "regions:" + ",".join(str(a) for a in self.regions)


@invregistry.register_tag("iz", CNonRelationalValue)
class CNRVInitializedSet(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_initialized_set(self) -> bool:
        return True

    @property
    def symbols(self) -> List["CXSymbol"]:
        return [self.xd.get_symbol(i) for i in self.args]

    def __str__(self) -> str:
        return ",".join(str(a) for a in self.symbols)


@invregistry.register_tag("ps", CNonRelationalValue)
class CNRVPolicyStateSet(CNonRelationalValue):

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        CNonRelationalValue.__init__(self, invd, ixval)

    @property
    def is_policy_state_set(self) -> bool:
        return True

    @property
    def symbols(self) -> List["CXSymbol"]:
        return [self.xd.get_symbol(i) for i in self.args]

    def __str__(self) -> str:
        return ",".join(str(a) for a in self.symbols)
