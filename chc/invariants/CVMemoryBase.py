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
"""Different types of memory base values (global, stack, heap)."""

from typing import Any, Dict, List, TYPE_CHECKING

from chc.invariants.CFunDictionaryRecord import (
    CFunVarDictionaryRecord, varregistry)

import chc.util.fileutil as UF

from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.invariants.CFunVarDictionary import CFunVarDictionary
    from chc.invariants.CXVariable import CXVariable


class CVMemoryBase(CFunVarDictionaryRecord):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CFunVarDictionaryRecord.__init__(self, vd, ixval)

    @property
    def is_null(self) -> bool:
        return False

    @property
    def is_stack_address(self) -> bool:
        return False

    @property
    def is_alloc_stack_address(self) -> bool:
        return False

    @property
    def is_heap_address(self) -> bool:
        return False

    @property
    def is_global_address(self) -> bool:
        return False

    @property
    def is_basevar(self) -> bool:
        return False

    @property
    def is_string_literal(self) -> bool:
        return False

    @property
    def is_freed(self) -> bool:
        return False

    @property
    def is_uninterpreted(self) -> bool:
        return False

    def __str__(self) -> str:
        return "memory-base " + self.tags[0]


@varregistry.register_tag("null", CVMemoryBase)
class CVMemoryBaseNull(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_null(self) -> bool:
        return True

    def has_associated_region(self) -> bool:
        return (self.args[0] > 0)

    @property
    def associated_region(self) -> "CVMemoryBase":
        if self.args[0] > 0:
            return self.vd.get_memory_base(self.args[0])
        else:
            raise UF.CHCError(
                str(self) + " does not have an associated region")

    def __str__(self) -> str:
        if self.has_associated_region():
            return "null(" + str(self.associated_region) + ")"
        else:
            return "null"


@varregistry.register_tag("sa", CVMemoryBase)
class CVMemoryBaseStackAddress(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_stack_address(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    def __str__(self) -> str:
        return "&" + str(self.variable)


@varregistry.register_tag("ga", CVMemoryBase)
class CVMemoryBaseGlobalAddress(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_global_address(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    def __str__(self) -> str:
        return "&" + str(self.variable)


@varregistry.register_tag("saa", CVMemoryBase)
class CVMemoryBaseAllocStackAddress(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_alloc_stackaddress(self) -> bool:
        return True

    @property
    def region_id(self) -> int:
        return self.args[0]

    def __str__(self) -> str:
        return "alloca-" + str(self.region_id)


@varregistry.register_tag("ha", CVMemoryBase)
class CVMemoryBaseHeapAddress(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_heap_address(self) -> bool:
        return True

    @property
    def is_valid(self) -> bool:
        return self.args[1] == 1

    @property
    def region_id(self) -> int:
        return self.args[0]

    def __str__(self) -> str:
        return "heap-" + str(self.region_id)


@varregistry.register_tag("bv", CVMemoryBase)
class CVMemoryBaseBaseVar(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_basevar(self) -> bool:
        return True

    @property
    def variable(self) -> "CXVariable":
        return self.xd.get_variable(self.args[0])

    def __str__(self) -> str:
        return str(self.variable)


@varregistry.register_tag("str", CVMemoryBase)
class CVMemoryBaseStringLiteral(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_string_literal(self) -> bool:
        return True

    @property
    def string(self) -> str:
        return self.cd.get_string(self.args[0])

    def __str__(self) -> str:
        return '&("' + str(self.string) + '")'


@varregistry.register_tag("ui", CVMemoryBase)
class CVMemoryBaseUninterpreted(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_uninterpreted(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return self.cd.get_string(self.args[0])

    def __str__(self) -> str:
        return "uninterpreted-memory-base-" + self.name


@varregistry.register_tag("fr", CVMemoryBase)
class CVMemoryBaseFreed(CVMemoryBase):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVMemoryBase.__init__(self, vd, ixval)

    @property
    def is_freed(self) -> bool:
        return True

    @property
    def region(self) -> "CVMemoryBase":
        return self.vd.get_memory_base(self.args[1])

    def __str__(self) -> str:
        return "freed(" + str(self.region) + ")"
