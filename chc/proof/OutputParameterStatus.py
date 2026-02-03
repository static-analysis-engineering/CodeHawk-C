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
    from chc.app.CDictionary import CDictionary
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.OutputParameterRejectionReason import OutputParameterRejectionReason


class OutputParameterStatus(CFunPODictionaryRecord):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        CFunPODictionaryRecord.__init__(self, pod, ixval)

    @property
    def is_unknown(self) -> bool:
        return False

    @property
    def is_rejected(self) -> bool:
        return False

    @property
    def is_written(self) -> bool:
        return False

    @property
    def is_unaltered(self) -> bool:
        return False

    @property
    def is_viable(self) -> bool:
        return False


@podregistry.register_tag("u", OutputParameterStatus)
class OutputParameterStatusUnknown(OutputParameterStatus):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterStatus.__init__(self, pod, ixval)

    @property
    def is_unknown(self) -> bool:
        return True

    def __str__(self) -> str:
        return "Unknown"


@podregistry.register_tag("v", OutputParameterStatus)
class OutputParameterStatusViable(OutputParameterStatus):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterStatus.__init__(self, pod, ixval)

    @property
    def is_viable(self) -> bool:
        return True

    def __str__(self) -> str:
        return "Viable"


@podregistry.register_tag("r", OutputParameterStatus)
class OutputParameterStatusRejected(OutputParameterStatus):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterStatus.__init__(self, pod, ixval)

    @property
    def is_rejected(self) -> bool:
        return True

    @property
    def reasons(self) -> List["OutputParameterRejectionReason"]:
        return [self.pod.get_output_parameter_rejection_reason(arg) for arg in self.args]

    def __str__(self) -> str:
        return "Rejected: " + "; ".join(str(reason) for reason in self.reasons)


@podregistry.register_tag("w", OutputParameterStatus)
class OutputParameterStatusWritten(OutputParameterStatus):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterStatus.__init__(self, pod, ixval)

    @property
    def is_written(self) -> bool:
        return True

    def __str__(self) -> str:
        return "Written"


@podregistry.register_tag("a", OutputParameterStatus)
class OutputParameterStatusUnaltered(OutputParameterStatus):

    def __init__(
            self, pod: "CFunPODictionary", ixval: IndexedTableValue
    ) -> None:
        OutputParameterStatus.__init__(self, pod, ixval)

    @property
    def is_unaltered(self) -> bool:
        return True

    def __str__(self) -> str:
        return "Unaltered"
