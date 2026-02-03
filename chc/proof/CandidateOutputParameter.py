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
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.CFunctionAnalysisDigest import (
        CFunctionOutputParameterAnalysisDigest)
    from chc.proof.OutputParameterCalleeCallsite import (
        OutputParameterCalleeCallsiteArg,
        OutputParameterCalleeCallsite)
    from chc.proof.OutputParameterStatus import OutputParameterStatus


class COpParamReturnsite:

    def __init__(self, cop: "CandidateOutputParameter", xnode: ET.Element) -> None:
        self._cop = cop
        self.xnode = xnode

    @property
    def cop(self) -> "CandidateOutputParameter":
        return self._cop

    @property
    def cfun(self) -> "CFunction":
        return self.cop.cfun

    @property
    def cfile(self) -> "CFile":
        return self.cop.cfile

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def location(self) -> "CLocation":
        return self.fdecls.read_xml_location(self.xnode)

    @property
    def status(self) -> "OutputParameterStatus":
        return self.podictionary.read_xml_output_parameter_status(self.xnode)

    def is_viable(self) -> bool:
        return self.status.is_written or self.status.is_unaltered

    def __str__(self) -> str:
        return str(self.location.line) + ": " + str(self.status)


class CandidateOutputParameter:

    def __init__(
            self, adg: "CFunctionOutputParameterAnalysisDigest", xnode: ET.Element
    ) -> None:
        self._adg = adg
        self.xnode = xnode    # param node
        self._returnsites: Optional[List[COpParamReturnsite]] = None
        self._caller_callsite_args: Optional[List["OutputParameterCalleeCallsiteArg"]] = None
        # self._calldeps: Optional[List[CopParamCallDependency]] = None

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
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def parameter(self) -> "CVarInfo":
        return self.fdecls.read_xml_varinfo(self.xnode)

    @property
    def parameter_index(self) -> int:
        """1-based index."""
        return int(self.xnode.get("paramindex", -1))

    @property
    def status(self) -> "OutputParameterStatus":
        return self.podictionary.read_xml_output_parameter_status(self.xnode)

    @property
    def returnsites(self) -> List[COpParamReturnsite]:
        if self._returnsites is None:
            self._returnsites = []
            xreturns = self.xnode.find("returnsites")
            if xreturns is not None:
                for xreturn in xreturns.findall("rs"):
                    returnsite = COpParamReturnsite(self, xreturn)
                    self._returnsites.append(returnsite)
        return self._returnsites

    @property
    def caller_callsite_args(self) -> List["OutputParameterCalleeCallsiteArg"]:
        if self._caller_callsite_args is None:
            self._caller_callsite_args = []
            callsites = self.adg.caller_callsites
            for callsite in callsites:
                for callarg in callsite.callargs:
                    if callarg.arg_index == self.parameter_index:
                        self._caller_callsite_args.append(callarg)
        return self._caller_callsite_args

    def is_viable(self) -> bool:
        if self.status.is_rejected:
            return False
        returns_viable = (
            all(returnsite.is_viable() for returnsite in self.returnsites))
        callers_viable = (
            all(callarg.status.is_viable for callarg in self.caller_callsite_args))
        return returns_viable and callers_viable

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append(str(self.parameter) + ": " + str(self.status))
        if not self.status.is_rejected:
            lines.append("   Return sites")
            for returnsite in self.returnsites:
                lines.append("       " + str(returnsite))
            lines.append("   Call arguments")
            for callsite_arg in self.caller_callsite_args:
                lines.append("       " + str(callsite_arg))
        return "\n".join(lines)
