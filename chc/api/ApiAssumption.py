# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
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
	from chc.api.CFunctionApi import CFunctionApi
	from chc.app.CFunction import CFunction
	from chc.proof.CPOPredicate import CPOPredicate

class ApiAssumption(object):

    def __init__(
            self,
            capi: 'CFunctionApi',
            id: int,
            predicate: 'CPOPredicate',
            ppos: List[int],
            spos: List[int],
            isglobal:bool = False,
            isfile:bool = False):
        self.id = id
        self.capi = capi                           # api/CFunctionAPI
        self.cfun: 'CFunction' = self.capi.cfun    # app/CFunction
        self.predicate = predicate                 # proof/CPOPredicate
        self.ppos = ppos
        self.spos = spos
        self.isglobal = isglobal                   # assumption includes global variable
        self.isfile = isfile

    def __str__(self) -> str:
        strppos = ''
        strspos = ''
        if len(self.ppos) > 0:
            strppos = "\n      --Dependent ppo's: [" + ','.join(str(i) for i in self.ppos) + ']'
        if len(self.spos) > 0:
            strspos = "\n      --Dependent spo's: [" + ','.join(str(i) for i in self.spos) + ']'
        if self.isglobal:
            isglobal = ' (global)'
        else:
            isglobal = ''
        return (str(self.id) + '  ' + str(self.predicate) + isglobal + strppos + strspos)
