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


class ContractAssumption(object):
    def __init__(self, capi, id, callee, xpredicate, ppos, spos):
        self.id = id
        self.callee = callee
        self.capi = capi  # api/CFunctionAPI
        self.cfun = self.capi.cfun
        self.xpredicate = xpredicate
        self.ppos = ppos
        self.spos = spos

    def __str__(self):
        strppos = ""
        strspos = ""
        calleename = "global"
        if self.callee >= 0:
            calleename = self.capi.cfile.declarations.get_global_varinfo(
                self.callee
            ).vname
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
