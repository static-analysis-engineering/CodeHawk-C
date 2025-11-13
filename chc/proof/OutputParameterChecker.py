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

from typing import List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction, CAnalysisInfo, CandidateOutputParameter
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFunctionPO import CFunctionPO


class OutputParameterChecker:
    """Interpret the proof obligation results for output parameters."""

    def __init__(self, cfun: "CFunction") -> None:
        self._cfun = cfun

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def analysis_info(self) -> "CAnalysisInfo":
        return self.cfun.analysis_info

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    def has_output_parameters(self) -> bool:
        return self.cfun.analysis_info.analysis == "output-parameters"

    @property
    def candidate_parameters(self) -> List["CandidateOutputParameter"]:
        if self.has_output_parameters():
            return self.analysis_info.candidate_parameters
        else:
            return []

    def context_candidate_output_ppos(
            self, candidate: "CVarInfo", ctxtid: int) -> List["CFunctionPO"]:
        """Return po's for a given parameter at a particular location in the ast."""

        return [po for po in self.candidate_ppos(candidate)
                if po.context.index == ctxtid
                and (po.predicate.is_output_parameter_initialized
                     or po.predicate.is_output_parameter_unaltered)]

    def candidate_ppos(self, candidate: "CVarInfo") -> List["CFunctionPO"]:
        """Return all po's for a given parameter."""

        return self.cfun.proofs.get_output_parameter_ppos(candidate.vname)

    def is_pure_output_parameter(self, candidate: "CVarInfo") -> Optional[str]:
        """Evaluate the status of the proof obligations related to the parameter.

        An output parameter is pure (that is, it can be safely converted to
        a Rust return value) if:

        1) its dereference is not read within the function
        2) it is fully written at some return site
        3) it is either fully written or not written at all at all return sites

        The first condition is represented by proof obligations with predicate
        PLocallyInitialized, which should all be safe.

        The second and third condition are represented by proof obligations with
        POutputParameterInitialized and POutputParameterUnaltered.

        Note:
        There are more conditions to come that have not yet been implemented.
        """

        ppos = self.candidate_ppos(candidate)
        ctxts = {ctxt.index for ctxt in [po.context for po in ppos]}

        notread = all(
            po.is_safe for po in ppos if po.predicate.is_locally_initialized)

        def allwritten(po_s: List["CFunctionPO"]) -> bool:
            return all(po.is_safe for po in po_s
                       if po.predicate.is_output_parameter_initialized)

        def allunaltered(po_s: List["CFunctionPO"]) -> bool:
            return all(po.is_safe for po in po_s
                       if po.predicate.is_output_parameter_unaltered)

        writtenonce = False
        must_parameter = True
        all_or_nothing_written = True
        for ctxtid in ctxts:
            ctxtppos = self.context_candidate_output_ppos(candidate, ctxtid)
            if len(ctxtppos) > 0:
                ctxt_allwritten = allwritten(ctxtppos)
                ctxt_allunaltered = allunaltered(ctxtppos)
                if not (ctxt_allwritten or ctxt_allunaltered):
                    all_or_nothing_written = False
                elif ctxt_allunaltered:
                    must_parameter = False
                elif ctxt_allwritten:
                    writtenonce = True

        issafe = notread and all_or_nothing_written and writtenonce

        if issafe:
            if must_parameter:
                return "must-output-parameter"
            else:
                return "may-output-parameter"

        else:
            return None

    def diagnostic(self, candidate: "CVarInfo") -> str:
        if self.is_pure_output_parameter(candidate):
            return "valid"

        lines: List[str] = []

        ppos = self.candidate_ppos(candidate)
        readppos = [po for po in ppos if po.predicate.is_locally_initialized]
        readviolations = [po for po in readppos if po.is_violated]
        readunknowns = [po for po in readppos if po.is_open]
        if len(readviolations) + len(readunknowns) > 0:
            lines.append("\nread violations and/or unknowns")
            for po in (readviolations + readunknowns):
                lines.append(str(po))

        writeppos = [po for po in ppos
                     if po.predicate.is_output_parameter_initialized
                     or po.predicate.is_output_parameter_unaltered]
        ctxts = {ctxt.index for ctxt in [po.context for po in ppos]}

        lines.append("\nfully written/unaltered violations and/or unknowns")
        for index in ctxts:
            output_po_s = self.context_candidate_output_ppos(candidate, index)
            output_violations = [po for po in output_po_s if po.is_violated]
            output_unknowns = [po for po in output_po_s if po.is_open]
            if len(output_po_s) + len(output_unknowns) > 0:
                ctxt = self.contextdictionary.get_program_context(index)
                lines.append(str(ctxt))
                for po in (output_violations + output_unknowns):
                    lines.append(str(po))

        return "\n".join(lines)

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("\n\nOutput parameters for function " + self.cfun.name)

        for candidate in self.candidate_parameters:
            if self.is_pure_output_parameter(candidate.parameter) is not None:
                lines.append("\n- " + str(candidate.parameter.vname) + ": "
                             + str(self.is_pure_output_parameter(
                                 candidate.parameter)))
            else:
                lines.append("- " + str(candidate.parameter.vname) + ": diagnostics:")
                lines.append(self.diagnostic(candidate.parameter))

        return "\n".join(lines)
