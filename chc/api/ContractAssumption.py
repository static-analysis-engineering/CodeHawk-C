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
"""Assumption on the return value of a function represented by a predicate.

Assumptions about return values of functions are never 'imposed' like those on
function arguments by the receiving function. The reason is that different
functions may have different expectations about the postcondition of a function,
or the transfer relation of the function.

Necessary postconditions may be suggested with the open proof obligation as a
hint towards conditions that can then be imposed deliberately via a contract
assumption.

"""

from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.api.CFunctionApi import CFunctionApi
    from chc.api.XPredicate import XPredicate
    from chc.app.CFunction import CFunction


class ContractAssumption:
    """Post condition assumption or assumption on global variable.

    Args:
        capi (CFunctionApi): the function api of the function that
           requests the assumption
        id (int): identification number of the assumption
        callee (int): (local) id of the function for which the
           postcondition is requested (-1 for a request on a global
           variable)
        xpredicate (XPredicate): predicate representing the assumption
        ppos (List[int]): id's of the primary proof obligations that
           require this assumption for discharge
        spos (List[int]): id's of the supporting proof obligations that
           require this assumption for discharge
    """

    def __init__(
        self,
        capi: "CFunctionApi",
        id: int,
        callee: int,
        xpredicate: "XPredicate",
        ppos: List[int],
        spos: List[int]
    ) -> None:
        self._id = id
        self._callee = callee
        self._capi = capi
        self._cfun = self.capi.cfun
        self._xpredicate = xpredicate
        self._ppos = ppos
        self._spos = spos

    @property
    def id(self) -> int:
        return self._id

    @property
    def callee(self) -> int:
        return self._callee

    @property
    def capi(self) -> "CFunctionApi":
        return self._capi

    @property
    def xpredicate(self) -> "XPredicate":
        return self._xpredicate

    @property
    def ppos(self) -> List[int]:
        return self._ppos

    @property
    def spos(self) -> List[int]:
        return self._spos

    def __str__(self) -> str:
        strppos = ""
        strspos = ""
        calleename = "global"
        if self.callee >= 0:
            calleename = self.capi.cfile.get_global_varinfo(self.callee).vname
        if len(self.ppos) > 0:
            strppos = (
                "\n      --Dependent ppo's: ["
                + ",".join(str(i) for i in self.ppos)
                + "]"
            )
        if len(self.spos) > 0:
            strspos = (
                "\n      --Dependent spo's: ["
                + ",".join(str(i) for i in self.spos)
                + "]"
            )
        return calleename + ": " + str(self.xpredicate) + strppos + strspos
