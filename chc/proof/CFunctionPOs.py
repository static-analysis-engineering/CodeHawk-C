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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionProofs import CFunctionProofs
    from chc.proof.CFunPODictionary import CFunPODictionary


class CFunctionPOs(object):
    """Superclass of CFunctionPPOs and CFunctionSPOs."""

    def __init__(self, cproofs: "CFunctionProofs") -> None:
        self._cproofs = cproofs

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def cfun(self) -> "CFunction":
        return self.cproofs.cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    def is_ppo_discharged(self, id: int) -> bool:
        return self.cproofs.is_ppo_discharged(id)

    def is_spo_discharged(self, id: int) -> bool:
        return self.cproofs.is_spo_discharged(id)

    def is_ppo_violated(self, id: int) -> bool:
        return self.cproofs.is_ppo_violated(id)

    def is_spo_violated(self, id: int) -> bool:
        return self.cproofs.is_spo_violated(id)

    def get_ppo_evidence(self, id: int):
        return self.cproofs.get_ppo_evidence(id)

    def get_spo_evidence(self, id: int):
        return self.cproofs.get_spo_evidence(id)
