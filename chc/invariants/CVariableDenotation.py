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

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

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
    from chc.invariants.CVConstantValueVariable import CVConstantValueVariable
    from chc.invariants.CVMemoryBase import CVMemoryBase
    from chc.invariants.CVMemoryReferenceData import CVMemoryReferenceData


class CVariableDenotation(CFunVarDictionaryRecord):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CFunVarDictionaryRecord.__init__(self, vd, ixval)

    @property
    def is_library_variable(self) -> bool:
        return False

    @property
    def is_local_variable(self) -> bool:
        return False

    @property
    def is_global_variable(self) -> bool:
        return False

    @property
    def is_memory_variable(self) -> bool:
        return False

    @property
    def is_memory_region_variable(self) -> bool:
        return False

    @property
    def is_return_variable(self) -> bool:
        return False

    @property
    def is_field_variable(self) -> bool:
        return False

    @property
    def is_check_variable(self) -> bool:
        return False

    @property
    def is_auxiliary_variable(self) -> bool:
        return False

    def __str_(self) -> str:
        return "c-variable-denotation " + self.tags[0]


@varregistry.register_tag("lv", CVariableDenotation)
class CVLocalVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_local_variable(self) -> bool:
        return True

    @property
    def varinfo(self) -> "CVarInfo":
        return self.fdecls.get_varinfo(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    def __str__(self) -> str:
        return "lv:" + str(self.varinfo) + str(self.offset)


@varregistry.register_tag("gv", CVariableDenotation)
class CVGlobalVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_global_variable(self) -> bool:
        return True

    @property
    def varinfo(self) -> "CVarInfo":
        return self.fdecls.get_varinfo(self.args[0])

    def __str__(self) -> str:
        return "gv:" + str(self.varinfo)


@varregistry.register_tag("mv", CVariableDenotation)
class CVMemoryVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_memory_variable(self) -> bool:
        return True

    @property
    def memory_reference_id(self) -> int:
        return self.args[0]

    @property
    def memory_reference_data(self) -> "CVMemoryReferenceData":
        return self.vd.get_memory_reference_data(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    def has_offset(self) -> bool:
        return self.offset.has_offset()

    def __str__(self) -> str:
        return (
            "memvar-"
            + str(self.memory_reference_id)
            + "{"
            + str(self.memory_reference_data)
            + "}"
            + str(self.offset))


@varregistry.register_tag("mrv", CVariableDenotation)
class CVMemoryRegionVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_memory_region_variable(self) -> bool:
        return True

    @property
    def memory_region_id(self) -> int:
        return self.args[0]

    @property
    def memory_base(self) -> "CVMemoryBase":
        return self.vd.get_memory_base(self.args[0])

    def __str__(self) -> str:
        return (
            "memreg-"
            + str(self.memory_region_id)
            + "{"
            + str(self.memory_base)
            + "}")


@varregistry.register_tag("rv", CVariableDenotation)
class CVReturnVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_return_variable(self) -> bool:
        return True

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    def __str__(self) -> str:
        return "returnval"


@varregistry.register_tag("fv", CVariableDenotation)
class CVFieldVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_field_variable(self) -> bool:
        return True

    @property
    def fieldname(self) -> str:
        return self.tags[1]

    @property
    def ckey(self) -> int:
        return self.args[0]

    def __str__(self) -> str:
        return "field-" + self.fieldname + "(" + str(self.ckey) + ")"


@varregistry.register_tag("cv", CVariableDenotation)
class CVCheckVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_check_variable(selkf) -> bool:
        return True

    @property
    def po_isppo_expnr_ids(self) -> List[Tuple[int, int, int]]:
        return list(zip(self.args[1::3], self.args[2::3], self.args[3::3]))

    @property
    def po_ids(self) -> List[int]:
        return [x for (_, x, _) in self.po_isppo_expnr_ids]

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    def __str__(self) -> str:
        return (
            "check("
            + ";".join(
                [
                    (("ppo:" if x[0] == 1 else "spo:") + str(x[1]) + "," + str(x[2]))
                    for x in self.po_isppo_expnr_ids
                ]
            )
            + ")")


@varregistry.register_tag("xv", CVariableDenotation)
class CVAugmentationVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_augmentation_variable(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "augv:" + str(self.name)


@varregistry.register_tag("av", CVariableDenotation)
class CVAuxiliaryVariable(CVariableDenotation):

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        CVariableDenotation.__init__(self, vd, ixval)

    @property
    def is_auxiliary_variable(self) -> bool:
        return True

    @property
    def cvv(self) -> "CVConstantValueVariable":
        return self.vd.get_constant_value_variable(self.args[0])

    def __str__(self) -> str:
        return "aux-" + str(self.cvv)
