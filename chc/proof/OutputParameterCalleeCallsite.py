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

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.app.CContext import ProgramContext
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFunctionAnalysisDigest import (
        CFunctionOutputParameterAnalysisDigest)
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.OutputParameterStatus import OutputParameterStatus


class OutputParameterCalleeCallsiteArg:

    def __init__(
            self, opcallsite: "OutputParameterCalleeCallsite", xnode: ET.Element
    ) -> None:
        self._opcallsite = opcallsite
        self.xnode = xnode

    @property
    def opcallsite(self) -> "OutputParameterCalleeCallsite":
        return self._opcallsite

    @property
    def adg(self) -> "CFunctionOutputParameterAnalysisDigest":
        return self.opcallsite.adg

    @property
    def cfun(self) -> "CFunction":
        return self.adg.cfun

    @property
    def cfile(self) -> "CFile":
        return self.adg.cfile

    @property
    def cdictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def status(self) -> "OutputParameterStatus":
        return self.podictionary.read_xml_output_parameter_status(self.xnode)

    @property
    def argument(self) -> "CExp":
        return self.cdictionary.read_xml_exp(self.xnode)

    @property
    def context(self) -> "ProgramContext":
        return self.contextdictionary.read_xml_context(self.xnode)

    @property
    def arg_index(self) -> int:
        expctxt = self.context.exp_context
        lastnode = expctxt.nodes[-1]
        if str(lastnode).startswith("arg:"):
            index = int(str(lastnode)[4:])
            return index
        else:
            return -1

    def __str__(self) -> str:
        return (
            str(self.status)
            + " " + str(self.argument) + " (argindex: " + str(self.arg_index))


class OutputParameterCalleeCallsite:

    def __init__(
            self, adg: "CFunctionOutputParameterAnalysisDigest", xnode: ET.Element
    ) -> None:
        self._adg = adg
        self.xnode = xnode
        self._callargs: Optional[List[OutputParameterCalleeCallsiteArg]] = None

    @property
    def adg(self) -> "CFunctionOutputParameterAnalysisDigest":
        return self._adg

    @property
    def cfun(self) -> "CFunction":
        return self.adg.cfun

    @property
    def cfile(self) -> "CFile":
        return self.adg.cfile

    @property
    def cdictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def callargs(self) -> List[OutputParameterCalleeCallsiteArg]:
        if self._callargs is None:
            self._callargs = []
            xcallargs = self.xnode.find("callee-callsite-args")
            if xcallargs is not None:
                for xcallarg in xcallargs.findall("callarg"):
                    callarg = OutputParameterCalleeCallsiteArg(self, xcallarg)
                    self._callargs.append(callarg)
        return self._callargs

    @property
    def status(self) -> "OutputParameterStatus":
        return self.podictionary.read_xml_output_parameter_status(self.xnode)

    @property
    def location(self) -> "CLocation":
        return self.fdecls.read_xml_location(self.xnode)

    @property
    def callee(self) -> "CExp":
        return self.cdictionary.read_xml_exp(self.xnode)

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append(
            str(self.location.line)
            + ": "
            + "; callee: "
            + str(self.callee))
        for callarg in self.callargs:
            lines.append("    " + str(callarg))
        return "\n".join(lines)
