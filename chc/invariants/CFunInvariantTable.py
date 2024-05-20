# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs LLC
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
"""Table of invariant facts for an individual function."""

import xml.etree.ElementTree as ET

from typing import cast, Dict, List, Tuple, TYPE_CHECKING

from chc.invariants.CInvariantFact import CInvariantFact, CInvariantNRVFact
from chc.invariants.CNonRelationalValue import (
    CNonRelationalValue, CNRVRegionSet)
from chc.invariants.CVariableDenotation import (
    CVariableDenotation, CVCheckVariable)

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CContext import ProgramContext
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.invariants.CFunInvDictionary import CFunInvDictionary
    from chc.invariants.CFunVarDictionary import CFunVarDictionary
    from chc.invariants.CXVariable import CXVariable


class CFunInvariantTable:
    """Function-level invariants."""

    def __init__(self, cfun: "CFunction", xnode: ET.Element):
        self._cfun = cfun
        self.xnode = xnode
        self._invariants: Dict[int, List[CInvariantFact]] = {}

        # self.invariants = {}  # context -> CInvariantFact list

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def ctxtd(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def invd(self) -> "CFunInvDictionary":
        return self.cfun.invdictionary

    @property
    def vard(self) -> "CFunVarDictionary":
        return self.cfun.vardictionary

    @property
    def invariants(self) -> Dict[int, List[CInvariantFact]]:
        if len(self._invariants) == 0:
            for xloc in self.xnode.findall("loc"):
                xctxt = xloc.get("ictxt")
                if xctxt is not None:
                    ictxt = int(xctxt)
                    self._invariants[ictxt] = []
                    xifacts = xloc.get("ifacts")
                    if xifacts is not None:
                        indices: List[int] = [int(x) for x in xifacts.split(",")]
                        for findex in indices:
                            self._invariants[ictxt].append(
                                self.invd.get_invariant_fact(findex))
        return self._invariants

    def context_invariants(
            self, context: "ProgramContext") -> List[CInvariantFact]:
        ictxt = self.ctxtd.index_cfg_projection(context)
        if ictxt in self.invariants:
            return self.invariants[ictxt]
        else:
            return []

    def get_sorted_invariants(
            self, context: "ProgramContext") -> List[CInvariantFact]:
        invs = self.context_invariants(context)
        nrvinvs = [inv for inv in invs if inv.is_nrv_fact]
        otherinvs = [inv for inv in invs if not inv.is_nrv_fact]
        nrvinvs = sorted(
            nrvinvs, key=lambda i: str(cast(CInvariantNRVFact, i).variable))
        return otherinvs + nrvinvs

    def get_po_invariants(
            self, context: "ProgramContext", poId: int) -> List[CInvariantFact]:
        invs = self.context_invariants(context)

        def filter(inv: CInvariantFact) -> bool:
            if inv.is_nrv_fact:
                inv = cast(CInvariantNRVFact, inv)
                var = inv.variable
                cvar = self.vard.get_c_variable_denotation(var.seqnr)
                if cvar.is_check_variable:
                    cvar = cast(CVCheckVariable, cvar)
                    return poId in cvar.po_ids
                else:
                    return True
            else:
                return True

        invs = [inv for inv in invs if filter(inv)]
        unrinvs = [inv for inv in invs if inv.is_unreachable_fact]
        nonrsinvs = [
            inv
            for inv in invs
            if inv.is_nrv_fact
            and (not cast(CInvariantNRVFact, inv).non_relational_value.is_region_set)
        ]
        rsinvs: List[CInvariantNRVFact] = [
            cast(CInvariantNRVFact, inv)
            for inv in invs
            if (inv.is_nrv_fact
                and cast(CInvariantNRVFact, inv).non_relational_value.is_region_set)
        ]
        varsets: Dict[int, CInvariantNRVFact] = {}
        for r in rsinvs:
            cvar = r.variable
            if cvar.seqnr not in varsets:
                varsets[cvar.seqnr] = r
            else:
                if (
                    cast(CNRVRegionSet, r.non_relational_value).size
                    < cast(CNRVRegionSet,
                           varsets[cvar.seqnr].non_relational_value).size
                ):
                    varsets[cvar.seqnr] = r
        invs = unrinvs + sorted(
            nonrsinvs
            + list(varsets.values()),
            key=lambda i: str(cast(CInvariantNRVFact, i).variable)
        )
        return invs

    def __str__(self) -> str:
        contexts: List[Tuple[str, List[CInvariantFact]]] = []
        lines: List[str] = []
        for i in self.invariants:
            ctxt = self.ctxtd.get_program_context(i)
            sctxt = ctxt.cfg_context.reverse_repr
            contexts.append((sctxt, self.invariants[i]))
        for (sctxt, invs) in sorted(contexts):
            lines.append("\n" + sctxt)
            for inv in invs:
                lines.append("  " + str(inv))
        return "\n".join(lines)
