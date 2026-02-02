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

from typing import cast, List, Optional, TYPE_CHECKING

from chc.proof.CandidateOutputParameter import CandidateOutputParameter
from chc.proof.OutputParameterCalleeCallsite import OutputParameterCalleeCallsite

from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.OutputParameterStatus import OutputParameterStatusRejected


class CFunctionAnalysisDigest:

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        self.xnode = xnode   # analysis-digest node in adg file
        self._cfun = cfun

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def is_active(self) -> bool:
        return True

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    def viable_parameters(self) -> List[CandidateOutputParameter]:
        return []

    def outputparameters(self) -> List[CandidateOutputParameter]:
        return []

    def maybe_parameters(self) -> List[CandidateOutputParameter]:
        return []


class CFunctionOutputParameterAnalysisDigest(CFunctionAnalysisDigest):

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        CFunctionAnalysisDigest.__init__(self, cfun, xnode)
        self._candidate_parameters: Optional[List[CandidateOutputParameter]] = None
        self._callee_callsites: Optional[List[OutputParameterCalleeCallsite]] = None
        self._caller_callsites: Optional[List[OutputParameterCalleeCallsite]] = None

    @property
    def parameters(self) -> List[CandidateOutputParameter]:
        if self._candidate_parameters is None:
            self._candidate_parameters = []
            xparams = self.xnode.find("candidate-parameters")
            if xparams is not None:
                for xparam in xparams.findall("param"):
                    cparam = CandidateOutputParameter(self, xparam)
                    self._candidate_parameters.append(cparam)
        return self._candidate_parameters

    def has_parameters(self) -> bool:
        return len(self.parameters) > 0

    @property
    def callee_callsites(self) -> List[OutputParameterCalleeCallsite]:
        if self._callee_callsites is None:
            self._callee_callsites = []
            xsites = self.xnode.find("callee-callsites")
            if xsites is not None:
                for xsite in xsites.findall("ccs"):
                    ccsite = OutputParameterCalleeCallsite(self, xsite)
                    self._callee_callsites.append(ccsite)
        return self._callee_callsites

    @property
    def caller_callsites(self) -> List[OutputParameterCalleeCallsite]:
        if self._caller_callsites is None:
            self._caller_callsites = []
            callinstrs = self.capp.get_callinstrs()
            for callinstr in callinstrs:
                if str(callinstr.callee) == self.cfun.name:
                    caller = callinstr.cfun
                    cfunadgs = caller.analysis_digests
                    if len(cfunadgs.digests) == 1:
                        cfunadg = cfunadgs.digests[0]
                        cfunadg = cast(
                            "CFunctionOutputParameterAnalysisDigest", cfunadg)
                        callsites = cfunadg.callee_callsites
                        callsites = [
                            callsite for callsite in callsites
                            if str(callsite.callee) == self.cfun.name]
                        self._caller_callsites = callsites
        return self._caller_callsites

    @property
    def is_active(self) -> bool:
        if self.has_parameters():
            if all(p.status.is_rejected for p in self.parameters):
                return False
            else:
                return True
        else:
            return False

    def outputparameters(self) -> List[CandidateOutputParameter]:
        return self.parameters

    def viable_parameters(self) -> List[CandidateOutputParameter]:
        return [p for p in self.parameters if p.is_viable()]

    def maybe_parameters(self) -> List[CandidateOutputParameter]:
        return [p for p in self.parameters if not (p.status.is_rejected or p.is_viable())]

    def __str__(self) -> str:
        lines: List[str] = []
        for p in self.parameters:
            if p.status.is_rejected:
                pstatus = cast("OutputParameterStatusRejected", p.status)
                lines.append(
                    " X " + str(p.parameter_index) + " " + str(p.parameter))
                lines.append(
                    "Reasons: " + "\n".join(str(r) for r in pstatus.reasons))
            elif p.is_viable():
                lines.append(" v " + str(p.parameter_index) + " " + str(p))
            else:
                lines.append(" ? " + str(p.parameter_index) + " " + str(p))
        if any(p.is_viable() for p in self.parameters):
            if len(self.caller_callsites) > 0:
                lines.append("\nCaller-callsites:")
                for ccs in self.caller_callsites:
                    lines.append("  " + str(ccs))
        return "\n".join(lines)


class CFunctionAnalysisDigests:

    def __init__(self, cfun: "CFunction", xnode: Optional[ET.Element]) -> None:
        self._cfun = cfun
        self.xnode = xnode    # analysis-digests node
        self._digests: Optional[List[CFunctionAnalysisDigest]] = None

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def digests(self) -> List[CFunctionAnalysisDigest]:
        if self._digests is None:
            self._digests = []
            if self.xnode is not None:
                for xdigest in self.xnode.findall("analysis-digest"):
                    digestkind = xdigest.get("name", "none")
                    if digestkind == "output parameters":
                        digest = CFunctionOutputParameterAnalysisDigest(
                            self.cfun, xdigest)
                        self._digests.append(digest)
            else:
                chklogger.logger.warning("Adg xnode is None")
        return self._digests

    def outputparameters(self) -> List[CandidateOutputParameter]:
        result: List[CandidateOutputParameter] = []
        for d in self.digests:
            result.extend(d.outputparameters())
        return result

    def viable_outputparameters(self) -> List[CandidateOutputParameter]:
        result: List[CandidateOutputParameter] = []
        for d in self.digests:
            result.extend(d.viable_parameters())
        return result

    def maybe_outputparameters(self) -> List[CandidateOutputParameter]:
        result: List[CandidateOutputParameter] = []
        for d in self.digests:
            result.extend(d.maybe_parameters())
        return result

    @property
    def is_active(self) -> bool:
        if len(self.digests) == 1:
            return self.digests[0].is_active
        return False

    def __str__(self) -> str:
        lines: List[str] = []
        for digest in self.digests:
            lines.append(str(digest))
        return "\n".join(lines)
