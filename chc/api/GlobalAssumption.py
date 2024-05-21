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
"""Assumption on a global variable at a particular location."""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.api.CFunctionApi import CFunctionApi
    from chc.api.XPredicate import XPredicate
    from chc.app.CFunction import CFunction


class GlobalAssumption:
    """
    Assumption on the value of a global variable at a particular location.

    Args:
       capi (CFunctionApi): the function api of the function that requests
           the assumption
       id (int): the identification number of the assumption
       predicate (XPredicate): predicate on global variable representing the
           assumption
       ppos (List[int]): id's of the primary proof obligations that require this
           assumption for discharge
       spos (List[int]): id's of the supporting proof obligations that require
           this assumption for discharge
    """
    def __init__(
            self,
            capi: "CFunctionApi",
            id: int,
            predicate: "XPredicate",
            ppos: List[int],
            spos: List[int]) -> None:
        self._id = id
        self._capi = capi
        self._predicate = predicate
        self._ppos = ppos
        self._spos = spos

    @property
    def id(self) -> int:
        return self._id

    @property
    def capi(self) -> "CFunctionApi":
        return self._capi

    @property
    def cfun(self) -> "CFunction":
        return self.capi.cfun

    @property
    def predicate(self) -> "XPredicate":
        return self._predicate

    @property
    def ppos(self) -> List[int]:
        return self._ppos

    @property
    def spos(self) -> List[int]:
        return self._spos

    def has_open_pos(self) -> bool:
        return (len(self.get_open_ppos()) + len(self.get_open_spos())) > 0

    def get_open_ppos(self) -> List[int]:
        return [i for i in self.ppos if self.cfun.get_ppo(i).is_open]

    def get_open_spos(self) -> List[int]:
        return [i for i in self.spos if self.cfun.get_spo(i).is_open]

    def __str__(self) -> str:
        strppos = ""
        strspos = ""
        if len(self.ppos) > 0:
            strppos = (
                "\n      --Dependent ppo's: ["
                + ",".join(str(i) for i in self.get_open_ppos())
                + "]"
            )
        if len(self.spos) > 0:
            strspos = (
                "\n      --Dependent spo's: ["
                + ",".join(str(i) for i in self.get_open_spos())
                + "]"
            )
        return str(self.id) + "  " + str(self.predicate) + strppos + strspos
