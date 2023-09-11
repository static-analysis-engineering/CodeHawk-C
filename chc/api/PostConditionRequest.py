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

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.app.CFunction import CFunction
    from chc.api.CFunctionApi import CFunctionApi
    from chc.api.PostRequest import PostRequest
    from chc.api.XPredicate import XPredicate
    from chc.app.CVarInfo import CVarInfo
    

class PostConditionRequest:

    def __init__(
            self,
            capi: "CFunctionApi",
            postrequest: "PostRequest",
            ppos: List[int],
            spos: List[int]) -> None:
        self._capi = capi
        self._postrequest = postrequest
        self.ppos = ppos
        self.spos = spos

    @property
    def capi(self) -> "CFunctionApi":
        return self._capi

    @property
    def cfun(self) -> "CFunction":
        return self.capi.cfun

    @property
    def postrequest(self) -> "PostRequest":
        return self._postrequest

    @property
    def postcondition(self) -> "XPredicate":
        return self.postrequest.postcondition

    @property
    def callee(self) -> "CVarInfo":
        return self.postrequest.callee

    def has_open_pos(self) -> bool:
        return (len(self.get_open_ppos()) + len(self.get_open_spos())) > 0

    def get_open_ppos(self) -> List[int]:
        return [i for i in self.ppos if self.cfun.get_ppo(i).is_open]

    def get_open_spos(self) -> List[int]:
        return [i for i in self.spos if self.cfun.get_spo(i).is_open]

    def __str__(self) -> str:
        dppos = ""
        if len(self.ppos) > 0 and len(self.get_open_ppos()) > 0:
            dppos = (
                "\n        --Dependent ppo's: ["
                + ", ".join(str(i) for i in self.get_open_ppos())
                + "]"
            )
        dspos = ""
        if len(self.spos) > 0 and len(self.get_open_spos()) > 0:
            dspos = (
                "\n        --Dependent spo's: ["
                + ", ".join(str(i) for i in self.get_open_spos())
                + "]"
            )
        return str(self.callee.vname) + ":" + str(self.postcondition) + dppos + dspos
