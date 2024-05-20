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
"""Supporting proof obligation for a call site."""

import xml.etree.ElementTree as ET

from typing import cast, Optional, TYPE_CHECKING

from chc.proof.CFunctionPO import CFunctionPO

if TYPE_CHECKING:
    from chc.proof.CFunctionSPOs import CFunctionSPOs
    from chc.proof.CFunPODictionaryRecord import CFunPOType
    from chc.proof.CFunctionProofs import CFunctionProofs
    from chc.proof.CProofDependencies import CProofDependencies
    from chc.proof.CProofDiagnostic import CProofDiagnostic
    from chc.proof.SPOType import CallsiteSPOType


class CFunctionCallsiteSPO(CFunctionPO):
    """Represents a supporting proof obligation associated with a call site."""

    def __init__(
            self,
            cproofs: "CFunctionProofs",
            potype: "CFunPOType",
            status: str = "open",
            deps: Optional["CProofDependencies"] = None,
            expl: Optional[str] = None,
            diag: Optional["CProofDiagnostic"] = None) -> None:
        CFunctionPO.__init__(self, cproofs, potype, status, deps, expl, diag)

    @property
    def apiid(self) -> int:
        """Returns the predicate id of the callee."""

        return cast("CallsiteSPOType", self.potype).external_id

    @property
    def is_spo(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            str(self.po_index).rjust(4)
            + " "
            + str(self.apiid).rjust(4)
            + " "
            + str(self.location.line).rjust(4)
            + "   "
            + str(self.predicate)
            + " ("
            + self.status
            + ")"
        )
