# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2025  Aarno Labs LLC
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

import xml.etree.ElementTree as ET

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.app.CContext import ProgramContext
    from chc.app.CContext import CContextDictionary
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation


class CFunctionReturnSite:

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        self._cfun = cfun
        self._xnode = xnode

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cdictionary(self) -> "CDictionary":
        return self.cfun.cdictionary

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def cfiledeclarations(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def xnode(self) -> ET.Element:
        return self._xnode

    @property
    def location(self) -> "CLocation":
        return self.cfiledeclarations.read_xml_location(self.xnode)

    @property
    def returnexp(self) -> Optional["CExp"]:
        return self.cdictionary.read_xml_exp_o(self.xnode)

    @property
    def context(self) -> "ProgramContext":
        return self.contextdictionary.read_xml_program_context(self.xnode)

    def __str__(self):
        rexp = str(self.returnexp) if self.returnexp else ""
        return (
            "return " + rexp + " ("
            + str(self.location.line) + ", " + str(self.location.byte)
            + ") ("
            + str(self.context)
        )
