# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2021-2022 Henny B. Sipma
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
"""External assumption on a function."""

from typing import TYPE_CHECKING

from chc.proof.CFunPODictionaryRecord import CFunPODictionaryRecord, podregistry

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue


if TYPE_CHECKING:
    from chc.api.XPredicate import XPredicate
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.CPOPredicate import CPOPredicate


class AssumptionType(CFunPODictionaryRecord):
    """Base class for assumption types."""

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        CFunPODictionaryRecord.__init__(self, pod, ixval)

    @property
    def is_local_assumption(self) -> bool:
        return False

    @property
    def is_api_assumption(self) -> bool:
        return False

    @property
    def is_global_api_assumption(self) -> bool:
        return False

    @property
    def is_contract_assumption(self) -> bool:
        return False

    @property
    def is_global_assumption(self) -> bool:
        return False

    def __str__(self) -> str:
        return "assumption-type:" + self.tags[0]


@podregistry.register_tag("la", AssumptionType)
class LocalAssumptionType(AssumptionType):
    """Assumption on local variables within a function.

    Used in a context where a property can be reduced to local supporting proof
    obligations. An example is assuming that a call to a function preserves all
    memory (e.g., does not free any memory).

    * args[0]: index of predicate in predicate dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        AssumptionType.__init__(self, pod, ixval)

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[0])

    @property
    def is_local_assumption(self) -> bool:
        return True

    def __str__(self) -> str:
        return "local:" + str(self.predicate)


@podregistry.register_tag("aa", AssumptionType)
class ApiAssumptionType(AssumptionType):
    """Assumption on parameters of the function.

    This type of assumption gives rise to the corresponding supporting proof
    obligations on the arguments in the caller of the function.

    The index of the predicate is also used as the api-id for the assumption.

    * args[0]: index of predicate in predicate dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        AssumptionType.__init__(self, pod, ixval)

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[0])

    @property
    def api_id(self) -> int:
        return self.args[0]

    @property
    def is_api_assumption(self) -> bool:
        return True

    def __str__(self) -> str:
        return "api:" + str(self.predicate)


@podregistry.register_tag("gi", AssumptionType)
class GlobalApiAssumptionType(AssumptionType):
    """Assumption on global variable values upon entry of the function.

    Global variables referenced/modified in a function can be viewed as 'ghost'
    parameters to a function, where the function may make some assumption about
    their value upon function start, but then is responsible for tracking its
    value locally (assuming no concurrency, or a form of ownership of the global
    variable throughout function execution.

    * args[0]: index of predicate in predicate dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        AssumptionType.__init__(self, pod, ixval)

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[0])

    @property
    def is_global_api_assumption(self) -> bool:
        return True

    def __str__(self) -> str:
        return "global-api:" + str(self.predicate)


@podregistry.register_tag("ca", AssumptionType)
class PostconditionType(AssumptionType):
    """Assumption on the post-condition of a function called.

    Note: this assumption type is referred to as a contract assumption, because
    these types of assumption are usually introduced by means of an externally
    provided contract.

    * args[0]: vid of the callee (local file vid)
    * args[1]: index of xpredicate in interface dictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        AssumptionType.__init__(self, pod, ixval)

    @property
    def xpredicate(self) -> "XPredicate":
        return self.ifd.get_xpredicate(self.args[1])

    @property
    def callee(self) -> int:
        return self.args[0]

    @property
    def is_contract_assumption(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "post-condition-assumption:("
            + str(self.callee)
            + ", "
            + str(self.xpredicate))


@podregistry.register_tag("ga", AssumptionType)
class GlobalAssumptionType(AssumptionType):
    """Assumption that is asserted globally that is supported globally.

    * args[0]: index of xpredicate in interfacedictionary
    """

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        AssumptionType.__init__(self, pod, ixval)

    @property
    def xpredicate(self) -> "XPredicate":
        return self.ifd.get_xpredicate(self.args[0])

    @property
    def is_global_assumption(self) -> bool:
        return True

    def __str__(self) -> str:
        return "global-assumption:" + str(self.xpredicate)
