# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2021-2022 Henny Sipma
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
"""Supporting proof obligation types generated to provide evidence for assumptions.
"""

from typing import TYPE_CHECKING

from chc.proof.CFunPODictionaryRecord import CFunPODictionaryRecord, podregistry

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue


if TYPE_CHECKING:
    from chc.api.XPredicate import XPredicate
    from chc.app.CContext import ProgramContext
    from chc.app.CLocation import CLocation
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.CPOPredicate import CPOPredicate


class SPOType(CFunPODictionaryRecord):
    """Base class for supporting proof obligation types."""

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        CFunPODictionaryRecord.__init__(self, pod, ixval)

    @property
    def is_local_spo(self) -> bool:
        return False

    @property
    def is_callsite_spo(self) -> bool:
        return False

    @property
    def is_returnsite_spo(self) -> bool:
        return False

    def __str__(self) -> str:
        return "spo-type:" + self.tags[0]


@podregistry.register_tag("ls", SPOType)
class LocalSPOType(SPOType):
    """Proof obligation that supports an assumption within a function.

    args[0]: index of location in cdeclarations
    args[1]: index of context in contexts
    args[2]: index of predicate in predicate dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        SPOType.__init__(self, pod, ixval)

    @property
    def is_local_spo(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.cdecls.get_location(self.args[0])

    @property
    def context(self) -> "ProgramContext":
        return self.cxd.get_program_context(self.args[1])

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[2])

    def __str__(self) -> str:
        return (
            "spo("
            + str(self.location)
            + ", "
            + str(self.context)
            + ", "
            + str(self.predicate)
            + ")")


@podregistry.register_tag("cs", SPOType)
class CallsiteSPOType(SPOType):
    """Proof obligation that supports an assumption on a function call argument.

    args[0]: index of location in cdeclarations
    args[1]: index of context in contexts
    args[2]: index of predicate in predicate dictionary
    args[3]: api-id
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        SPOType.__init__(self, pod, ixval)

    @property
    def is_callsite_spo(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.cdecls.get_location(self.args[0])

    @property
    def context(self) -> "ProgramContext":
        return self.cxd.get_program_context(self.args[1])

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[2])

    @property
    def external_id(self) -> int:
        return self.args[3]

    def __str__(self) -> str:
        return (
            "spo("
            + str(self.location)
            + ", "
            + str(self.context)
            + ", "
            + str(self.predicate)
            + ")")
    

@podregistry.register_tag("cs", SPOType)
class ReturnsiteSPOType(SPOType):
    """Proof obligation that supports an assumption on a return value.

    args[0]: index of location in cdeclarations
    args[1]: index of context in contexts
    args[2]: index of predicate in predicate dictionary
    args[3]: index of xpredicate in interface dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        SPOType.__init__(self, pod, ixval)

    @property
    def is_returnsite_spo(self) -> bool:
        return True

    @property
    def location(self) -> "CLocation":
        return self.cdecls.get_location(self.args[0])

    @property
    def context(self) -> "ProgramContext":
        return self.cxd.get_program_context(self.args[1])

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[2])

    @property
    def postcondition(self) -> "XPredicate":
        return self.id.get_xpredicate(self.args[3])

    @property
    def external_id(self) -> int:
        return self.args[3]

    def __str__(self) -> str:
        return (
            "spo("
            + str(self.location)
            + ", "
            + str(self.context)
            + ", "
            + str(self.predicate)
            + ", "
            + str(self.postcondition)
            + ")")
    
