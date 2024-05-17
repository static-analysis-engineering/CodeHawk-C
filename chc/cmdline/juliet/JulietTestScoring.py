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
"""Utility functions for printing a score report for a Juliet Test."""

from typing import Any, cast, Dict, List, Optional, Tuple, TYPE_CHECKING

from chc.cmdline.juliet.JulietTestSetRef import JulietTestSetRef

from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.cmdline.juliet.JulietTestFileRef import JulietTestFileRef, JulietPpo
    from chc.cmdline.juliet.JulietTestRef import JulietTestRef
    from chc.cmdline.juliet.JulietTestSetRef import JulietTestSetRef
    from chc.proof.AssumptionType import (
        ApiAssumptionType, GlobalApiAssumptionType)
    from chc.proof.CFunctionCallsiteSPO import CFunctionCallsiteSPO
    from chc.proof.CFunctionPO import CFunctionPO


violationcategories = ["V", "S", "D", "U", "O"]
safecontrolcategories = ["S", "D", "X", "U", "O"]


def scoreheader(name: str, width: int) -> str:
    header1 = (
        name.ljust(width + 10) + "violations                 safe-controls")
    header2 = (
        (" " * (width + 3))
        + " V    S    D    U    O         S    D    X    U    O")
    return header1 + "\n" + header2



def keymatches(tppo: "JulietPpo", ppo: "CFunctionPO") -> bool:
    """Return true if a ppo matches a ppo listed in the test set reference.

    A ppo listed in a test set reference is always characterized by the ppo
    predicate, and may additionally be characterized (if multiple ppo's with
    the same predicate appear on the same line) by a set of variable names,
    one of which has to appear in the ppo, or an expression context.
    """

    return (
        tppo.line == ppo.line
        and tppo.predicate == ppo.predicate_name
        and tppo.matches_exp_ctxt(ppo)
        and tppo.matches_variable_names(ppo)
        and tppo.matches_variable_names_plus(ppo)
        and tppo.matches_variable_deref(ppo)
        and tppo.matches_target_type(ppo)
        and tppo.matches_pred_arg(ppo)
        and tppo.matches_reference_type(ppo)
    )


def classify_tgt_violation(
        po: Optional["CFunctionPO"], capp: "CApplication") -> str:
    if po is None:
        return "U"  # unknown
    if po.is_open:
        return "U"  # unknown
    if po.is_violated:
        return "V"  # violation reported
    dm = po.dependencies.level
    if dm == "f" or dm == "s":
        return "S"  # found safe
    if po.is_delegated:
        spos = get_associated_spos(po, capp)
        if len(spos) > 0:
            classifications = [classify_tgt_violation(spo, capp) for spo in spos]
            if "V" in classifications:
                return "V"  # violation reported
            if all([x == "S" for x in classifications]):
                return "S"  # found safe
        else:
            return "O"  # no callsite found
        return "D"  # found deferred
    return "O"  # other


def classify_tgt_safecontrol_contract_assumption(
        po: Optional["CFunctionPO"], capp: "CApplication") -> str:
    return "S"


def classify_tgt_safecontrol(
        po: Optional["CFunctionPO"], capp: "CApplication") -> str:
    if po is None:
        return "U"  # unknown
    if po.is_open:
        return "U"  # unknown
    if po.is_violated:
        return "O"  # violation
    dm = po.dependencies.level
    if dm == "s" or dm == "f":
        return "S"  # safe
    if po.is_delegated:
        dependencies_type = po.get_assumptions_type()
        if po.get_assumptions_type() == "contract":
            return classify_tgt_safecontrol_contract_assumption(po, capp)
        spos = get_associated_spos(po, capp)
        if len(spos) > 0:
            classifications = [
                classify_tgt_safecontrol(spo, capp) for spo in spos]
            if all([x == "S" for x in classifications]):
                return "S"  # safe
            if "O" in classifications:
                return "O"
            return "D"  # deferred
        else:
            return "O"
    if po.is_deadcode:
        return "X"  # dead code
    return "O"  # other


def get_associated_spos(
        ppo: "CFunctionPO", capp: "CApplication") -> List["CFunctionPO"]:
    result: List["CFunctionPO"] = []
    if ppo.has_dependencies():
        cfun = ppo.cfun
        cfile = ppo.cfile
        callsites = capp.get_callsites(cfile.index, cfun.svar.vid)
        assumption_ids = ppo.dependencies.ids
        assumptions = [
            cfun.podictionary.get_assumption_type(i) for i in assumption_ids]
        assumption_predids: List[int] = []
        for a in assumptions:
            if a.is_api_assumption:
                a = cast("ApiAssumptionType", a)
                assumption_predids.append(a.predicate.index)
            elif a.is_global_api_assumption:
                a = cast("GlobalApiAssumptionType", a)
                assumption_predids.append(a.predicate.index)
        if len(callsites) > 0:
            for ((fid, vid), cs) in callsites:

                def f(spo: "CFunctionPO") -> None:
                    spo = cast("CFunctionCallsiteSPO", spo)
                    if spo.apiid in assumption_predids:
                        result.append(spo)

                cs.iter(f)
    return result


def testppo_calls_tostring(ppo: "CFunctionPO", capp: "CApplication") -> str:
    lines: List[str] = []
    cfun = ppo.cfun
    cfile = ppo.cfile
    callsites = capp.get_callsites(cfile.index, cfun.svar.vid)
    if len(callsites) > 0:
        lines.append("    calls:")
        for ((fid, vid), cs) in callsites:

            def f(spo: "CFunctionPO") -> None:
                sev = spo.explanation
                if sev is None:
                    sevtxt = "?"
                else:
                    sevtxt = spo.get_display_prefix() + "  " + sev
                lines.append(
                    "     C:"
                    + str(spo.line).rjust(3)
                    + "  "
                    + spo.predicate_name.ljust(25)
                    + sevtxt
                )

            cs.iter(f)
    return "\n".join(lines)


def testppo_results_tostring(
        pairs: Dict[str, Dict[str, List[Tuple["JulietPpo", "CFunctionPO"]]]],
        capp: "CApplication") -> str:
    lines: List[str] = []
    for filename in sorted(pairs):
        lines.append("\n" + filename)
        for fn in sorted(pairs[filename]):
            if len(pairs[filename][fn]) == 0:
                continue
            lines.append("\n  " + fn)
            for (jppo, ppo) in pairs[filename][fn]:
                ev = ppo.explanation
                if ev is None:
                    evstr = "?"
                else:
                    evstr = ppo.get_display_prefix() + "  " + ev
                lines.append(
                    "    "
                    + str(ppo.line).rjust(3)
                    + "  "
                    + str(ppo.po_index).rjust(3)
                    + ": "
                    + ppo.predicate_name.ljust(25)
                    + evstr
                )
                if (ev is not None) and ppo.is_delegated:
                    lines.append(testppo_calls_tostring(ppo, capp))
    return "\n".join(lines)


def get_julietppos(testset: "JulietTestSetRef") -> Dict[str, List["JulietPpo"]]:
    """Returns the reference ppos indexed by filename.

    Note: the reference ppos are function agnostic
    """

    ppos: Dict[str, List["JulietPpo"]] = {}

    def g(filename: str, fileref: "JulietTestFileRef") -> None:
        filename = filename[:-2]
        if filename not in ppos:
            ppos[filename] = []

        def h(line: int, jppo: "JulietPpo") -> None:
            ppos[filename].append(jppo)

        fileref.iter(h)

    def f(tindex: str, test: "JulietTestRef") -> None:
        test.iter(g)

    testset.iter(f)
    return ppos


def get_ppo_pairs(
        julietppos: Dict[str, List["JulietPpo"]],
        capp: "CApplication"
) -> Dict[str, Dict[str, List[Tuple["JulietPpo", "CFunctionPO"]]]]:
    """Returns a pairing of reference ppos with actual ppos by function."""

    pairs: Dict[str, Dict[str, List[Tuple["JulietPpo", "CFunctionPO"]]]] = {}
    for filename in julietppos:
        chklogger.logger.info("Get ppo pairs for %s", filename)
        pairs.setdefault(filename, {})
        julietfileppos = julietppos[filename]
        cfile = capp.get_file(filename)

        fileppos = cfile.get_ppos()
        for ppo in fileppos:
            fnname = ppo.cfun.name
            chklogger.logger.info(
                "Get ppo pairs for function %s in file %s", fnname, filename)
            pairs[filename].setdefault(fnname, [])
            for jppo in julietfileppos:
                if keymatches(jppo, ppo):
                    pairs[filename][fnname].append((jppo, ppo))
    return pairs


def initialize_testsummary(
        testset: "JulietTestSetRef",
        d: Dict[str, Dict[str, Dict[str, int]]]) -> None:

    def f(tindex: str, test: "JulietTestRef") -> None:
        d[tindex] = {}
        d[tindex]["vs"] = {}
        for c in violationcategories:
            d[tindex]["vs"][c] = 0
        d[tindex]["sc"] = {}
        for c in safecontrolcategories:
            d[tindex]["sc"][c] = 0

    testset.iter(f)


def fill_testsummary(
        pairs: Dict[str, Dict[str, List[Tuple["JulietPpo", "CFunctionPO"]]]],
        d: Dict[str, Dict[str, Dict[str, int]]],
        capp: "CApplication") -> None:
    for filename in pairs:
        for fn in pairs[filename]:
            for (jppo, ppo) in pairs[filename][fn]:
                tindex = jppo.test
                tsummary = d[tindex]
                if jppo.is_violation:
                    classification = classify_tgt_violation(ppo, capp)
                    tsummary["vs"][classification] += 1
                else:
                    classification = classify_tgt_safecontrol(ppo, capp)
                    tsummary["sc"][classification] += 1


def get_testsummary_totals(d: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """Returns the totals per category summed over all tests in the testset."""
    totals: Dict[str, Dict[str, int]] = {}
    totals["vs"] = {}
    totals["sc"] = {}
    for c in violationcategories:
        totals["vs"][c] = sum([d[x]["vs"][c] for x in d])
    for c in safecontrolcategories:
        totals["sc"][c] = sum([d[x]["sc"][c] for x in d])
    return totals


def testsummary_tostring(d: Dict[str, Dict[str, Dict[str, int]]]) -> str:

    def dataline(cats: List[str], d: Dict[str, int]) -> str:
        return ("".join([str(d[c]).rjust(5) for c in cats]))

    lines: List[str] = []
    lines.append("\nSummary\n")
    lines.append(scoreheader("test", 5))
    lines.append("-" * 80)
    for tindex in sorted(d):
        sv = d[tindex]["vs"]
        ss = d[tindex]["sc"]
        lines.append(
            tindex.ljust(5)
            + dataline(violationcategories, sv)
            + "  |  "
            + dataline(safecontrolcategories, ss))
    lines.append("-" * 80)
    totals = get_testsummary_totals(d)
    lines.append(
        "total"
        + dataline(violationcategories, totals["vs"])
        + "  |  "
        + dataline(safecontrolcategories, totals["sc"]))
    return "\n".join(lines)
