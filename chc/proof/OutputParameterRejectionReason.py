# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2025  Aarno Labs LLC
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

from typing import List, TYPE_CHECKING

from chc.proof.CFunPODictionaryRecord import CFunPODictionaryRecord, podregistry


from chc.util.IndexedTable import IndexedTableValue


if TYPE_CHECKING:
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CDictionary import CDictionary
    from chc.app.CTyp import CTyp
    from chc.proof.CFunPODictionary import CFunPODictionary


class OutputParameterRejectionReason(CFunPODictionaryRecord):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        CFunPODictionaryRecord.__init__(self, pod, ixval)


@podregistry.register_tag("a", OutputParameterRejectionReason)
class OutputParameterRejectionReasonArrayStruct(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def compinfo(self) -> "CCompInfo":
        return self.cdecls.get_compinfo(self.args[0])

    def __str__(self) -> str:
        return "Struct with embedded array: " + str(self.compinfo)


@podregistry.register_tag("at", OutputParameterRejectionReason)
class OutputParameterRejectionReasonArrayType(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cdictionary.get_typ(self.args[0])

    def __str__(self) -> str:
        return "array type: " + str(self.typ)


@podregistry.register_tag("c", OutputParameterRejectionReason)
class OutputParameterRejectionReasonConstQualifier(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cdictionary.get_typ(self.args[0])

    def __str__(self) -> str:
        return "Const qualifier: " + str(self.typ)


@podregistry.register_tag("o", OutputParameterRejectionReason)
class OutputParameterRejectionReasonOtherReason(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def reason(self) -> str:
        return self.cdictionary.get_string(self.args[0])

    def __str__(self) -> str:
        return "Other: " + str(self.reason)


@podregistry.register_tag("p", OutputParameterRejectionReason)
class OutputParameterRejectionReasonPointerPointer(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cdictionary.get_typ(self.args[0])

    def __str__(self) -> str:
        return "Pointer to pointer: " + str(self.typ)


@podregistry.register_tag("r", OutputParameterRejectionReason)
class OutputParameterRejectionReasonParameterRead(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def linenumber(self) -> int:
        return self.args[0]

    def __str__(self) -> str:
        return "Parameter is read at line " + str(self.linenumber)


@podregistry.register_tag("s", OutputParameterRejectionReason)
class OutputParameterRejectionReasonSystemStruct(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    @property
    def compinfo(self) -> "CCompInfo":
        return self.cdecls.get_compinfo(self.args[0])

    def __str__(self) -> str:
        return "Target type is a system struct: " + str(self.compinfo)


@podregistry.register_tag("v", OutputParameterRejectionReason)
class OutputParameterRejectionReasonVoidPointer(OutputParameterRejectionReason):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterRejectionReason.__init__(self, pod, ixval)

    def __str__(self) -> str:
        return "Void pointer"
