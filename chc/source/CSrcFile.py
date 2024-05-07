# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2023 Henny B. Sipma
# Copyright (c) 2024      Aarno Labs LLC
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

import os
from typing import Dict, TYPE_CHECKING, Optional

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication


class CSrcFile:
    """Represents the text file that holds the C source code."""

    def __init__(self, capp: "CApplication", fname: str) -> None:
        self._capp = capp
        self._fname = fname
        self._lines: Optional[Dict[int, str]] = None

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def fname(self) -> str:
        """Returns the absolute c filename relative to the project directory."""

        return self._fname

    @property
    def lines(self) -> Dict[int, str]:
        if self._lines is None:
            self._lines = {}
            if os.path.isfile(self.fname):
                n: int = 1
                with open(self.fname) as fp:
                    for line in fp:
                        self._lines[n] = line
                        n += 1
            else:
                chklogger.logger.warning(
                    "Source file %s not found", self.fname)
        return self._lines

    def get_line_count(self) -> int:
        return len(self.lines)

    def get_line(self, n: int) -> Optional[str]:
        if self.get_line_count() > n:
            return str(n) + "  " + self.lines[n]
        return None
