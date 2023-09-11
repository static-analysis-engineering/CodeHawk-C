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

from chc.api.InterfaceDictionaryRecord import InterfaceDictionaryRecord

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.XPredicate import XPredicate
    from chc.app.CVarInfo import CVarInfo


class PostAssume(InterfaceDictionaryRecord):
    """Assumption on the postcondition of a function.

    args[0]: function vid
    args[1]: index of predicate in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue) -> None:
        InterfaceDictionaryRecord.__init__(self, ifd, ixval)

    @property
    def callee(self) -> "CVarInfo":
        return self.ifd.cfile.declarations.get_global_varinfo(int(self.args[0]))

    @property
    def postcondition(self) -> "XPredicate":
        return self.ifd.get_xpredicate(int(self.args[1]))

    def __str__(self) -> str:
        return str(self.callee) + ":" + str(self.postcondition)
