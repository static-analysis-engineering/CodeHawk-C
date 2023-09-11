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

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CInitInfo import CInitInfo
    from chc.app.CLocation import CLocation
    from chc.app.CVarInfo import CVarInfo

class CGVarDef:
    """Global variable definition."""

    def __init__(
            self,
            varinfo: "CVarInfo",
            location: "CLocation",
            initializer: "CInitInfo" =  None) -> None:
        self._varinfo = varinfo
        self._location = location
        self._initializer = initializer

    @property
    def varinfo(self) -> "CVarInfo":
        return self._varinfo

    @property
    def location(self) -> "CLocation":
        return self._location

    def has_initializer(self) -> bool:
        return self._initializer is not None

    @property
    def initializer(self) -> "CInitInfo":
        if self._initializer is not None:
            return self._initializer
        else:
            raise UF.CHCError(
                "Variable definition: "
                + str(self.varinfo)
                + " without initializer")

    def __str__(self) -> str:
        return str(self.varinfo)
