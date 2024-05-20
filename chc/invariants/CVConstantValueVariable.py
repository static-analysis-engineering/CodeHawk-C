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
"""Symbolic values that are constant in the context of a function."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunVarDictionaryRecord, varregistry)

import chc.util.fileutil as UF

from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.app.CLocation import CLocation
    from chc.app.COffset import COffset
    from chc.app.CVarInfo import CVarInfo
    from chc.app.CTyp import CTyp
    from chc.invariants.CFunVarDictionary import CFunVarDictionary
    from chc.invariants.CVMemoryReferenceData import CVMemoryReferenceData
    from chc.invariants.CXVariable import CXVariable
    from chc.invariants.CXXpr import CXXpr


class CVConstantValueVariable(CFunVarDictionaryRecord):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CFunVarDictionaryRecord.__init__(self, vd, ixval)

    @property
    def is_initial_value(self) -> bool:
        return False

    @property
    def is_function_return_value(self) -> bool:
        return False

    @property
    def is_exp_function_return_value(self) -> bool:
        return False

    @property
    def is_sideeffect_value(self) -> bool:
        return False

    @property
    def is_exp_sideeffect_value(self) -> bool:
        return False

    @property
    def is_symbolic_value(self) -> bool:
        return False

    @property
    def is_tainted_value(self) -> bool:
        return False

    @property
    def is_memory_address(self) -> bool:
        return False

    def __str__(self) -> str:
        return "cvv " + self.tags[0]


@varregistry.register_tag("iv", CVConstantValueVariable)
class CVVInitialValue(CVConstantValueVariable):
    """Inital value of a variable at function entry.

    - args[0]: index of original variable in the xprdictionary
    - args[1]: index of variable type in cdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_initial_value(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    def __str__(self) -> str:
        return str(self.variable) + "_init"


@varregistry.register_tag("frv", CVConstantValueVariable)
class CVVFunctionReturnValue(CVConstantValueVariable):
    """Return value from a direct function call at a particular callsite.

    - args[0]: index of callsite location in file declarations
    - args[1]: index of programcontext in context dictionary
    - args[2]: vid of the varinfo of the function called
    - args[3..]: indices of argument expressions to the call in the xprdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_function_return_value(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.fdecls.get_location(self.args[0])

    @property
    def callee(self) -> "CVarInfo":
        return self.fundecls.get_varinfo(self.args[2])

    @property
    def arguments(self) -> List[Optional["CXXpr"]]:
        result: List[Optional["CXXpr"]] = []
        for a in self.args[3:]:
            if a == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(a))
        return result

    def __str__(self) -> str:
        return (
            str(self.callee.vname)
            + "("
            + ",".join(str(a) for a in self.arguments)
            + ")")


@varregistry.register_tag("erv", CVConstantValueVariable)
class CVVExpFunctionReturnValue(CVConstantValueVariable):
    """Return value from an indirect function call at a particular callsite.

    - args[0]: index of callsite location in file declarations
    - args[1]: index of porgramcontext in context dictionary
    - args[2]: index of indirect call expression in xprdictionary
    - args[3]: index of the typ of the call expression in the cdictionary
    - args[4..]: indices of argument expressions to the call in the xprdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_exp_function_return_value(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.fdecls.get_location(self.args[0])

    @property
    def callee(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[2])

    @property
    def arguments(self) -> List[Optional["CXXpr"]]:
        result: List[Optional["CXXpr"]] = []
        for a in self.args[3:]:
            if a == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(a))
        return result

    def __str__(self) -> str:
        return (
            str(self.callee)
            + "("
            + ",".join(str(a) for a in self.arguments)
            + ")")


@varregistry.register_tag("fsev", CVConstantValueVariable)
class CVVSideEffectValue(CVConstantValueVariable):
    """Side effect value of a direct call at a particular call site.

    - args[0]: index of callsite location in file declarations
    - args[1]: index of programcontext in context dictionary
    - args[2]: vid of the varinfo of the function called
    - args[3]: argument index of the side-effect (index starting at 1)
    - args[4]: index of the type of side-effect value in cdictionary
    - args[5..]: indices of the arguments passed to the call in xprdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_side_effect_value(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.fdecls.get_location(self.args[0])

    @property
    def callee(self) -> "CVarInfo":
        return self.fundecls.get_varinfo(self.args[2])

    @property
    def argindex(self) -> int:
        return self.args[3]

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[4])

    @property
    def arguments(self) -> List[Optional["CXXpr"]]:
        result: List[Optional["CXXpr"]] = []
        for a in self.args[5:]:
            if a == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(a))
        return result

    def __str__(self) -> str:
        return (
            str(self.callee)
            + "("
            + ",".join(str(a) for a in self.arguments)
            + ")")


@varregistry.register_tag("esev", CVConstantValueVariable)
class CVVExpSideEffectValue(CVConstantValueVariable):
    """Side effect value of an indirect call at a particular call site.

    - args[0]: index of callsite location in file declarations
    - args[1]: index of programcontext in context dictionary
    - args[2]: index of the indirect call expression in the xprdictionary
    - args[3]: argument index of the side-effect value (starting at 1)
    - args[4]: index of the type of the side-effect value in cdictionary
    - args[5..]: indices of the arguments passed to the call in xprdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_exp_side_effect_value(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.fdecls.get_location(self.args[0])

    @property
    def callee(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[2])

    @property
    def argindex(self) -> int:
        return self.args[3]

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[4])

    @property
    def arguments(self) -> List[Optional["CXXpr"]]:
        result: List[Optional["CXXpr"]] = []
        for a in self.args[5:]:
            if a == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(a))
        return result

    def __str__(self) -> str:
        return (
            str(self.callee)
            + "("
            + ",".join(str(a) for a in self.arguments)
            + ")")


@varregistry.register_tag("sv", CVConstantValueVariable)
class CVVSymbolicValue(CVConstantValueVariable):
    """Value representing a constant-value expression.

    - args[0]: index of the original expression in the xprdictionary
    - args[1]: index of the type of the expression in the cdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_symbolic_value(self) -> bool:
        return True

    @property
    def xpr(self) -> "CXXpr":
        return self.xd.get_xpr(self.args[0])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[1])

    def __str__(self) -> str:
        return str(self.xpr)


@varregistry.register_tag("tv", CVConstantValueVariable)
class CVVTaintedValue(CVConstantValueVariable):
    """External input value, optionally bounded.

    - args[0]: index of the external variable in the xprdictionary
    - args[1]: index of lower bound value in xprdictionary (or -1 for unbounded)
    - args[2]: index of upper bound vlaue in xprdictionary (or -1 for unbounded)
    - args[3]: index of the type of the variable in the cdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_tainted_value(self) -> bool:
        return True

    def has_lowerbound(self) -> bool:
        return self.args[1] >= 0

    def has_upperbound(self) -> bool:
        return self.args[2] >= 0

    @property
    def lowerbound(self) -> "CXXpr":
        if self.has_lowerbound():
            return self.xd.get_xpr(self.args[1])
        else:
            raise UF.CHCError("Tainted value does not have a lowerbound")

    @property
    def upperbound(self) -> "CXXpr":
        if self.has_upperbound():
            return self.xd.get_xpr(self.args[2])
        else:
            raise UF.CHCError("Tainted value does not have an upperbound")

    @property
    def origin(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[3])

    def __str__(self) -> str:
        return "taint-from-" + str(self.origin)


@varregistry.register_tag("bs", CVConstantValueVariable)
class CVVByteSequence(CVConstantValueVariable):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_byte_sequence(self) -> bool:
        return True

    @property
    def origin(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    def has_length(self) -> bool:
        return self.args[1] >= 0

    @property
    def length(self) -> "CXXpr":
        if self.has_length():
            return self.xd.get_xpr(self.args[1])
        else:
            raise UF.CHCError("ByteSequence does not have a length")

    def __str__(self) -> str:
        return "byte-seq-" + str(self.origin)


@varregistry.register_tag("ma", CVConstantValueVariable)
class CVVMemoryAddress(CVConstantValueVariable):
    """Memory address.

    - args[0]: memory reference index
    - args[1]: index of the offset in the cdictionary
    """

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVConstantValueVariable.__init__(self, vd, ixval)

    @property
    def is_memory_address(self) -> bool:
        return True

    @property
    def memory_reference(self) -> "CVMemoryReferenceData":
        return self.vd.get_memory_reference_data(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    def __str__(self) -> str:
        return (
            "memory-address:"
            + str(self.memory_reference)
            + ":"
            + str(self.offset))
