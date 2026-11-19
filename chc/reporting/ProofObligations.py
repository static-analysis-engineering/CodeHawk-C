# ------------------------------------------------------------------------------
# CodeHawkC Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023-2024 Aarn Labs LLC
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

import time

from typing import (
    Any, Callable, cast, Dict, List, Sequence, Set, Tuple, TYPE_CHECKING)

import chc.util.fileutil as UF

from chc.proof.CFunctionPO import analysis_levels, default_analysis_level
from chc.proof.ConsolidatedStatus import (
    ConsolidatedStatus, consolidated_categories, consolidated_descriptions)

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CContext import ProgramContext
    from chc.invariants.CFunInvDictionary import CFunInvDictionary
    from chc.invariants.CInvariantFact import CInvariantNRVFact
    from chc.proof.CFunctionPO import CFunctionPO

"""Utility functions for reporting proof obligations and their statistics."""

dischargemethods: List[str] = [
    "stmt", "local", "api", "contract", "open", "violated"]


"""Overlay columns for proof obligations whose condition fails, by the
category of behavior that results (issue 15): they are also counted in the
column of their discharge method, and are not included in the totals. The
violated column (undefined behavior) is always present; the other columns are
present at the analysis levels that include them."""
findingmethods: Dict[str, str] = {
    "undefined-behavior": "violated",
    "implementation-defined": "impl-def",
    "value-wrap-around": "wrap"}

overlaymethods: List[str] = list(findingmethods.values())


histogramcolors: Dict[str, str] = {
    "violated": "red",
    "stmt": "green",
    "local": "lightgreen",
    "api": "springgreen",
    "contract": "aquamarine",
    "open": "orange",
    "impl-def": "purple",
    "wrap": "blue",
}


def get_dsmethods(
        extra: List[str], level: str = "undefined-behavior") -> List[str]:
    """Return the column headers: the extra headers, the discharge methods,
    and the overlay columns for the categories above undefined behavior that
    are included in the analysis level."""
    levelmethods = [
        findingmethods[c]
        for c in analysis_levels[1:analysis_levels.index(level) + 1]]
    return extra + dischargemethods + levelmethods


def filter_analysis_level(
        pos: Sequence["CFunctionPO"], level: str) -> List["CFunctionPO"]:
    """Return the proof obligations reported at the given analysis level."""
    return [po for po in pos if po.in_analysis_level(level)]


def get_dsmethod_header(
        indent: int, dsmethods: List[str], header1: str = "") -> str:
    return (
        header1.ljust(indent)
        + "".join([dm.rjust(10) for dm in dsmethods])
        + "total".rjust(10)
    )


def classifypo(po: "CFunctionPO", d: Dict[str, int]) -> None:
    """Classify proof obligation wrt discharge method and update dictionary.

    Args:
      po: proof obligation (CFunctionPO)
      d: dictionary, with discharge methods initialized (is updated)
    """
    if po.is_closed:
        if po.is_violated:
            d["violated"] += 1
        elif po.is_implementation_defined:
            d["impl-def"] = d.get("impl-def", 0) + 1
        elif po.is_value_wrap_around:
            d["wrap"] = d.get("wrap", 0) + 1
        deps = po.dependencies
        if deps.has_external_dependencies():
            deptype = po.get_assumptions_type()
            d[deptype] += 1
        elif deps.is_stmt:
            d["stmt"] += 1
        elif deps.is_local or deps.is_deadcode:
            d["local"] += 1
        else:
            print("Unable to classify " + str(po))
    else:
        d["open"] += 1


def get_method_count(
        pos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True,
        extradsmethods: List[str] = [],
        level: str = default_analysis_level) -> Dict[str, int]:
    """Create dicharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by discharge method
    """
    result: Dict[str, int] = {}
    for dm in get_dsmethods(extradsmethods, level):
        result[dm] = 0
    for po in pos:
        classifypo(po, result)
    return result


def get_tag_method_count(
        pos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True,
        extradsmethods: List[str] = [],
        level: str = default_analysis_level) -> Dict[str, Dict[str, int]]:
    """Create predicate tag, discharge method count dictionary.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by predicate and discharge method
    """
    result: Dict[str, Dict[str, int]] = {}
    dsmethods = get_dsmethods(extradsmethods, level)
    for po in pos:
        if not filefilter(po.cfile.name):
            continue
        tag = po.predicate_name
        if tag not in result:
            result[tag] = {}
            for dm in dsmethods:
                result[tag][dm] = 0
        classifypo(po, result[tag])
    return result


def get_file_method_count(
        pos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True,
        extradsmethods: List[str] = [],
        level: str = default_analysis_level) -> Dict[str, Dict[str, int]]:
    """Create file, discharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by file and discharge method
    """
    result: Dict[str, Dict[str, int]] = {}
    dsmethods = get_dsmethods(extradsmethods, level)
    for po in pos:
        pofile = po.cfile.name
        if not filefilter(pofile):
            continue
        if pofile not in result:
            result[pofile] = {}
            for dm in dsmethods:
                result[pofile][dm] = 0
        classifypo(po, result[pofile])
    return result


def get_function_method_count(
        pos: Sequence["CFunctionPO"],
        extradsmethods: List[str] = [],
        level: str = default_analysis_level) -> Dict[str, Dict[str, int]]:
    """Create function, discharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or supporting)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by function and discharge method
    """
    result: Dict[str, Dict[str, int]] = {}
    dsmethods = get_dsmethods(extradsmethods, level)
    for po in pos:
        pofunction = po.cfun.name
        if pofunction not in result:
            result[pofunction] = {}
            for dm in dsmethods:
                result[pofunction][dm] = 0
        classifypo(po, result[pofunction])
    return result


def row_method_count_tostring(
        d: Dict[str, Dict[str, int]],
        perc: bool = False,
        extradsmethods: List[str] = [],
        rhlen: int = 25,
        header1: str = "") -> str:
    """Display a dictionary with row-header - discharge method - count.

    Args:
      d: dictionary (row header -> discharge method -> count
      perc: boolean that indicates whether to print discharge method percentages
      extradsmethods: list of additional column headers (will be prepended)
      rhlen: maximum length of the row header (default 25)
    Returns:
      table of discharge method counts represented as a string
    """

    lines: List[str] = []
    width: int = 10
    dsmethods = get_dsmethods(extradsmethods) + [
        dm for dm in overlaymethods[1:] if any(dm in d[t] for t in d)]
    lines.append(get_dsmethod_header(rhlen, dsmethods, header1=header1))
    barlen = 10 * (len(dsmethods) + 1) + rhlen
    lines.append("-" * barlen)
    for t in sorted(d):
        r = [d[t].get(dm, 0) for dm in dsmethods]
        total = sum(
            [d[t].get(dm, 0) for dm in dsmethods if dm not in overlaymethods])
        lines.append(
            t.ljust(rhlen)
            + "".join([str(x).rjust(width) for x in r])
            + str(total).rjust(width)
        )
    lines.append("-" * barlen)

    totals: Dict[str, int] = {}
    for dm in dsmethods:
        totals[dm] = sum([d[t].get(dm, 0) for t in d])
    totalcount: int = sum(
        [totals[dm] for dm in totals if dm not in overlaymethods])
    lines.append(
        "total".ljust(rhlen)
        + "".join([str(totals[dm]).rjust(width) for dm in dsmethods])
        + str(totalcount).rjust(width)
    )
    if perc and totalcount > 0:
        scale = float(totalcount) / 100.0
        lines.append(
            "percent".ljust(rhlen)
            + "".join(
                [
                    str("{:.2f}".format(float(totals[dm]) / scale)).rjust(width)
                    for dm in dsmethods
                ]
            )
        )
    return "\n".join(lines)


class FunctionDisplay:

    def __init__(
            self,
            cfunction: "CFunction",
            sourcecodeavailable: bool) -> None:
        self._cfunction = cfunction
        self._sourcecodeavailable = sourcecodeavailable
        self._currentline = self._cfunction.get_location().line + 1

    @property
    def cfunction(self) -> "CFunction":
        return self._cfunction

    @property
    def cfinvd(self) -> "CFunInvDictionary":
        return self.cfunction.invdictionary

    @property
    def sourcecodeavailable(self) -> bool:
        return self._sourcecodeavailable

    @property
    def cfile(self) -> "CFile":
        return self.cfunction.cfile

    @property
    def fline(self) -> int:
        return self.cfunction.get_location().line

    def get_source_line(self, line: int) -> str:
        srcline = self.cfile.get_source_line(line)
        if srcline is not None:
            return self.cfile.get_source_line(line).strip()
        return "?"

    def pos_no_code_to_string(
            self,
            pos: Sequence["CFunctionPO"],
            pofilter: Callable[["CFunctionPO"], bool] = lambda po: True) -> str:
        lines: List[str] = []
        for po in sorted(pos, key=lambda po: po.line):
            if not pofilter(po):
                continue
            delegated: str = ""
            indent: int = 18 if po.is_ppo else 24
            if po.is_closed:
                expl = po.explanation
                prefix = po.get_display_prefix()
                lines.append(prefix + " " + str(po))
                lines.append((" " * indent) + str(expl))
                deps = po.dependencies.invs
                lines.append(
                    ("\n" + " " * indent).join(
                        str(self.cfunction.invdictionary.get_invariant_fact(i)
                            for i in deps)))
            else:
                lines.append("\n<?> " + str(po))
                if po.has_diagnostic():
                    amsgs = po.diagnostic.argument_msgs
                    if len(amsgs) > 0:
                        for arg in sorted(amsgs):
                            for amsg in amsgs[arg]:
                                lines.append((" " * indent) + str(amsg))
                    kmsgs = po.diagnostic.keyword_msgs
                    if len(kmsgs) > 0:
                        for key in sorted(kmsgs):
                            for s in sorted(kmsgs[key]):
                                lines.append((" " * indent) + key + ": " + s)
                    msgs = po.diagnostic.msgs
                    if len(msgs) > 0:
                        for m in msgs:
                            lines.append((" " * indent) + str(m))
                    keys = po.diagnostic.argument_indices
                    for k in sorted(keys):
                        invids = po.diagnostic.get_invariant_ids(k)
                        for id in invids:
                            inv = self.cfinvd.get_invariant_fact(id)
                            if inv.is_nrv_fact:
                                inv = cast("CInvariantNRVFact", inv)
                                nrv = inv.non_relational_value
                                lines.append(
                                    (" " * indent) + str(k) + ": " + str(nrv))
                else:
                    lines.append((" " * indent) + "---> no diagnostic found")
        return "\n".join(lines)

    def pos_on_code_tostring(
            self,
            pos: Sequence["CFunctionPO"],
            pofilter: Callable[["CFunctionPO"], bool] = lambda po: True,
            showinvs: bool = False) -> str:
        lines: List[str] = []
        contexts: Set["ProgramContext"] = set([])
        for po in sorted(pos, key=lambda po: po.line):
            if not pofilter(po):
                if po.line >= self._currentline:
                    if self.sourcecodeavailable:
                        for n in range(self._currentline, po.line + 1):
                            lines.append(self.get_source_line(n))
                self._currentline = po.line + 1
                continue
            line = po.line
            indent: int = 18 if po.is_ppo else 24
            if line >= self._currentline:
                if len(contexts) > 0 and showinvs:
                    lines.append(
                        "\n"
                        + (" " * indent)
                        + "-------- context invariants --------")
                    for c in contexts:
                        lines.append((" " * indent) + str(c))
                        lines.append((" " * indent) + ("-" * len(str(c))))
                        lines.append(str(self._get_context_invariants(c)))
                        lines.append(" ")
                lines.append("-" * 80)
                if self.sourcecodeavailable:
                    for n in range(self._currentline, line + 1):
                        lines.append(self.get_source_line(n))
                else:
                    if self._currentline == line:
                        lines.append("source line " + str(line))
                    else:
                        lines.append(
                            "source lines "
                            + str(self._currentline)
                            + " - " + str(line))
                lines.append("-" * 80)
                contexts = set([])
            self._currentline = line + 1
            delegated = ""
            indent = 18 if po.is_ppo else 24
            if po.is_closed:
                # contexts.add(po.context)    (uncomment to see all invariants)
                expl = po.explanation
                prefix = po.get_display_prefix()
                lines.append(prefix + " " + str(po))
                lines.append((" " * indent) + str(expl))
                deps = po.dependencies.invs
                lines.append(
                    ("\n" + " " * indent).join(str(
                        self.cfunction.invdictionary.get_invariant_fact(i))
                                               for i in deps))
            else:
                contexts.add(po.context)
                lines.append("\n<?> " + str(po))
                if po.has_diagnostic():
                    amsgs = po.diagnostic.argument_msgs
                    if len(amsgs) > 0:
                        for arg in sorted(amsgs):
                            for amsg in amsgs[arg]:
                                lines.append((" " * indent) + str(amsg))
                    kmsgs = po.diagnostic.keyword_msgs
                    if len(kmsgs) > 0:
                        for key in sorted(kmsgs):
                            for s in sorted(kmsgs[key]):
                                lines.append((" " * indent) + key + ": " + s)
                    msgs = po.diagnostic.msgs
                    if len(msgs) > 0:
                        for m in msgs:
                            lines.append((" " * indent) + str(m))
                    keys = po.diagnostic.argument_indices
                    for k in sorted(keys):
                        invids = po.diagnostic.get_invariant_ids(k)
                        for id in invids:
                            inv = self.cfinvd.get_invariant_fact(id)
                            if inv.is_nrv_fact:
                                inv = cast("CInvariantNRVFact", inv)
                                nrv = inv.non_relational_value
                                lines.append(
                                    (" " * indent) + str(k) + ": " + str(nrv))
                else:
                    lines.append((" " * indent) + "---> no diagnostic found")
                lines.append(" ")

                if showinvs and (not po.has_diagnostic()):
                    lines.append((" " * 18) + "--")
                    lines.append(self._get_po_invariants(po.context, po.po_index))

        if len(contexts) > 0 and showinvs:
            lines.append(
                "\n" + (" " * indent) + "-------- context invariants --------")
            for c in contexts:
                lines.append((" " * indent) + "=== " + str(c) + " ===")
                lines.append(str(self._get_context_invariants(c)))
                lines.append(" ")

        self._currentline = self.fline + 1
        return "\n".join(lines)

    def _get_po_invariants(self, context: "ProgramContext", poId: int) -> str:
        lines: List[str] = []
        invs = self.cfunction.invarianttable.get_po_invariants(context, poId)
        for inv in invs:
            lines.append((" " * 18) + str(inv))
        return "\n".join(lines)

    def _get_context_invariants(self, context: "ProgramContext") -> str:
        lines: List[str] = []
        invs = self.cfunction.invarianttable.get_sorted_invariants(context)
        for inv in invs:
            lines.append((" " * 18) + str(inv))
        return "\n".join(lines)


def function_pos_to_string(
        fn: "CFunction",
        pofilter: Callable[["CFunctionPO"], bool] = lambda po: True) -> str:
    lines: List[str] = []
    ppos = fn.get_ppos()
    ppos = [x for x in ppos if pofilter(x)]
    spos = fn.get_spos()
    fd = FunctionDisplay(fn, False)
    if len(ppos) + len(spos) > 0:
        lines.append("\nFunction " + fn.name)
        lines.append(fd.pos_no_code_to_string(ppos, pofilter=pofilter))
        lines.append(fd.pos_no_code_to_string(spos, pofilter=pofilter))
    return "\n".join(lines)


def function_code_tostring(
        fn: "CFunction",
        pofilter: Callable[["CFunctionPO"], bool] = lambda po: True,
        showinvs: bool = False,
        showpreamble: bool = True) -> str:
    lines: List[str] = []
    ppos = fn.get_ppos()
    # ppos = [x for x in ppos if pofilter(x)]
    spos = fn.get_spos()
    if fn.has_line_number():
        fnstartlinenr = fn.get_line_number()
        fnstartline = fn.cfile.get_source_line(fnstartlinenr)
        lines.append("\nFunction " + fn.name)
        lines.append("-" * 80)
        lines.append(fnstartline.strip())
        fd = FunctionDisplay(fn, True)
    else:
        lines.append(
            "\nFunction "
            + fn.name
            + " (source code not available, included from "
            + str(fn.get_source_code_file())
            + ")"
        )
        fd = FunctionDisplay(fn, False)

    if showpreamble:
        lines.append("-" * 80)
        lines.append(str(fn.api))
        lines.append("-" * 80)
    if len(ppos) > 0:
        lines.append("Primary Proof Obligations:")
        lines.append(
            fd.pos_on_code_tostring(ppos, pofilter=pofilter, showinvs=showinvs)
        )
        lines.append("-" * 80)
    if len(spos) > 0:
        lines.append("Supporting Proof Obligations:")
        lines.append(
            fd.pos_on_code_tostring(spos, pofilter=pofilter, showinvs=showinvs)
        )
        lines.append("-" * 80)
    return "\n".join(lines)


def function_code_open_tostring(
        fn: "CFunction", showinvs: bool = False) -> str:

    def pofilter(po: "CFunctionPO") -> bool:
        return po.is_finding or (not po.is_closed)

    return function_code_tostring(fn, pofilter=pofilter, showinvs=showinvs)


def function_code_violation_tostring(
        fn: "CFunction", showinvs: bool = False) -> str:

    def pofilter(po: "CFunctionPO") -> bool:
        return po.is_finding

    return function_code_tostring(fn, pofilter=pofilter, showinvs=showinvs)


def function_code_predicate_tostring(
        fn: "CFunction", p: str, showinvs: bool = False) -> str:

    def pofilter(po: "CFunctionPO") -> bool:
        return po.predicate_name == p

    return function_code_tostring(fn, pofilter=pofilter, showinvs=showinvs)


def file_pos_violations_to_string(cfile: "CFile") -> str:
    lines: List[str] = []

    def pofilter(po: "CFunctionPO") -> bool:
        return po.is_violated

    def f(fn: "CFunction") -> None:
        lines.append(function_pos_to_string(fn, pofilter=pofilter))

    cfile.iter_functions(f)
    return "\n".join(lines)


def file_code_tostring(
        cfile: "CFile",
        pofilter: Callable[["CFunctionPO"], bool] = lambda po: True,
        showinvs: bool = False) -> str:
    lines: List[str] = []

    def f(fn: "CFunction") -> None:
        lines.append(
            function_code_tostring(fn, pofilter=pofilter, showinvs=showinvs))

    cfile.iter_functions(f)
    return "\n".join(lines)


def file_code_open_tostring(cfile: "CFile", showinvs: bool = False) -> str:

    def pofilter(po: "CFunctionPO") -> bool:
        return po.is_finding or (not po.is_closed)

    return file_code_tostring(cfile, pofilter=pofilter, showinvs=showinvs)


def unreachable_locations(
        ppos: Sequence["CFunctionPO"],
        spos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True
) -> List[Dict[str, Any]]:
    """Return the locations of open proof obligations proven unreachable.

    Unreachability does not discharge proof obligations (unless the analyzer
    is run with -unreachability); the proof obligations stay open and are
    reported separately, because unreachable code is rare in real code and
    usually points to an imprecision or error in the analysis.

    Returns:
      list of records (file, function, line, domains, ppos, spos), one per
      source line, sorted by file, function, and line
    """
    locs: Dict[Tuple[str, str, int], Dict[str, Any]] = {}

    def add(po: "CFunctionPO", kind: str) -> None:
        domains = po.unreachable_domains
        if len(domains) == 0 or not filefilter(po.cfile.name):
            return
        key = (po.cfile.name, po.cfun.name, po.line)
        if key not in locs:
            locs[key] = {
                "file": key[0], "function": key[1], "line": key[2],
                "domains": [], "ppos": 0, "spos": 0}
        locs[key][kind] += 1
        for d in domains:
            if d not in locs[key]["domains"]:
                locs[key]["domains"].append(d)

    for po in ppos:
        add(po, "ppos")
    for po in spos:
        add(po, "spos")
    return [locs[k] for k in sorted(locs)]


def out_of_level_counts(
        ppos: Sequence["CFunctionPO"],
        spos: Sequence["CFunctionPO"],
        level: str,
        filefilter: Callable[[str], bool] = lambda f: True
) -> Dict[str, Dict[str, Dict[str, int]]]:
    """Return the status counts of the proof obligations that are not
    reported at the given analysis level.

    Returns:
      dictionary: category of behavior -> ppos/spos -> status -> count
    """
    result: Dict[str, Dict[str, Dict[str, int]]] = {}
    for (kind, pos) in [("ppos", ppos), ("spos", spos)]:
        for po in pos:
            if po.in_analysis_level(level) or not filefilter(po.cfile.name):
                continue
            catd = result.setdefault(po.behavior_category, {})
            kindd = catd.setdefault(kind, {})
            kindd[po.status] = kindd.get(po.status, 0) + 1
    return result


def out_of_level_tostring(
        counts: Dict[str, Dict[str, Dict[str, int]]], level: str) -> str:
    """Return a summary of the proof obligations not reported at the given
    analysis level (empty if there are none)."""
    if len(counts) == 0:
        return ""

    def kindstr(d: Dict[str, int], name: str) -> str:
        return (
            str(sum(d.values())) + " " + name + " ("
            + ", ".join(k + ": " + str(d[k]) for k in sorted(d)) + ")")

    lines: List[str] = []
    lines.append(
        "\n\nNot reported at analysis level " + level
        + " (these proof obligations are checked at every level):")
    for cat in analysis_levels:
        if cat not in counts:
            continue
        parts = [
            kindstr(counts[cat][k], name)
            for (k, name) in [("ppos", "primary"), ("spos", "supporting")]
            if k in counts[cat]]
        lines.append("  " + cat + ": " + "; ".join(parts))
    lines.append(
        "  (use --analysis-level " + analysis_levels[-1]
        + " to report them)")
    return "\n".join(lines)


def unreachable_locations_tostring(
        locations: List[Dict[str, Any]],
        openppos: int,
        openspos: int) -> str:
    """Return a report of the locations of open proof obligations proven
    unreachable (empty if there are none)."""
    if len(locations) == 0:
        return ""
    nppos = sum(loc["ppos"] for loc in locations)
    nspos = sum(loc["spos"] for loc in locations)
    lines: List[str] = []
    lines.append(
        "\n\nOpen proof obligations at locations proven unreachable: "
        + str(nppos) + " of " + str(openppos) + " open primary, "
        + str(nspos) + " of " + str(openspos) + " open supporting")
    lines.append(
        "(unreachability does not discharge proof obligations; unreachable"
        + " code is rare and may point to an imprecision or error in the"
        + " analysis)")
    lines.append("-" * 80)
    fnlen = max(len(loc["function"]) for loc in locations) + 2
    filelen = max(len(loc["file"]) for loc in locations) + 2
    lines.append(
        "file".ljust(filelen) + "function".ljust(fnlen) + "line".rjust(6)
        + "ppos".rjust(6) + "spos".rjust(6) + "  domains")
    for loc in locations:
        lines.append(
            loc["file"].ljust(filelen)
            + loc["function"].ljust(fnlen)
            + str(loc["line"]).rjust(6)
            + str(loc["ppos"]).rjust(6)
            + str(loc["spos"]).rjust(6)
            + "  " + ", ".join(loc["domains"]))
    return "\n".join(lines)


def consolidated_counts(
        cons: ConsolidatedStatus,
        pos: Sequence["CFunctionPO"],
        rowkey: Callable[["CFunctionPO"], str],
        filefilter: Callable[[str], bool] = lambda f: True
) -> Dict[str, Dict[str, int]]:
    """Return row -> consolidated category -> count (issue 43)."""
    result: Dict[str, Dict[str, int]] = {}
    for po in pos:
        if not filefilter(po.cfile.name):
            continue
        row = result.setdefault(
            rowkey(po), {c: 0 for c in consolidated_categories})
        row[cons.category(po)] += 1
    return result


def consolidated_tostring(
        d: Dict[str, Dict[str, int]],
        rhlen: int = 28,
        header1: str = "") -> str:
    """Return a table of consolidated category counts with totals and
    percentages."""
    width = 12
    lines: List[str] = []
    lines.append(
        header1.ljust(rhlen)
        + "".join(c.rjust(width) for c in consolidated_categories)
        + "total".rjust(width))
    barlen = width * (len(consolidated_categories) + 1) + rhlen
    lines.append("-" * barlen)
    for t in sorted(d):
        r = [d[t].get(c, 0) for c in consolidated_categories]
        lines.append(
            t.ljust(rhlen)
            + "".join(str(x).rjust(width) for x in r)
            + str(sum(r)).rjust(width))
    lines.append("-" * barlen)
    totals = [
        sum(d[t].get(c, 0) for t in d) for c in consolidated_categories]
    total = sum(totals)
    lines.append(
        "total".ljust(rhlen)
        + "".join(str(x).rjust(width) for x in totals)
        + str(total).rjust(width))
    if total > 0:
        lines.append(
            "percent".ljust(rhlen)
            + "".join(
                "{:.2f}".format(100.0 * x / total).rjust(width)
                for x in totals))
    return "\n".join(lines)


def _split_top_level(s: str) -> List[str]:
    """Split s at the commas that are not nested in (), [], or {}."""
    parts: List[str] = []
    depth = 0
    start = 0
    for (k, c) in enumerate(s):
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(s[start:k])
            start = k + 1
    parts.append(s[start:])
    return [p.strip() for p in parts]


def _matching_paren(s: str, start: int) -> int:
    """Return the index of the parenthesis that closes the one opened just
    before start (len(s) if there is none)."""
    depth = 1
    for k in range(start, len(s)):
        if s[k] in "([{":
            depth += 1
        elif s[k] in ")]}":
            depth -= 1
            if depth == 0:
                return k
    return len(s)


def compact_expression_str(s: str) -> str:
    """Return a compact rendering of the string representation of a CIL
    expression, for display only: casts (caste(t, e) -> e), type annotations
    (e:(t)) and qualifiers are removed, string constants str(..) are quoted,
    and sizeofe(..) is shown as sizeof(..)."""
    while True:
        k = s.find("caste(")
        if k < 0:
            break
        end = _matching_paren(s, k + 6)
        args = _split_top_level(s[k + 6:end])
        inner = args[-1] if len(args) > 0 else ""
        s = s[:k] + inner + s[end + 1:]
    pos = 0
    while True:
        k = s.find("str(", pos)
        if k < 0:
            break
        if k > 0 and (s[k - 1].isalnum() or s[k - 1] == "_"):
            pos = k + 4
            continue
        end = _matching_paren(s, k + 4)
        s = s[:k] + '"' + s[k + 4:end] + '"' + s[end + 1:]
        pos = k + 1
    s = s.replace("sizeofe(", "sizeof(")
    # type annotations of expressions: e:(t)
    while True:
        k = s.find(":(")
        if k < 0:
            break
        end = _matching_paren(s, k + 2)
        s = s[:k] + s[end + 1:]
    s = s.replace("[const: ,pconst: ]", "")
    # type annotation of a parenthesized expression: (e):t
    if s.startswith("(") and _matching_paren(s, 1) < len(s) - 1:
        end = _matching_paren(s, 1)
        if s[end + 1] == ":" and "(" not in s[end + 1:]:
            s = s[:end + 1]
    return s


"""Predicate arguments that are omitted from the compact rendering: they
describe how the analyzer represents the operation, not the condition."""
_internal_predicate_args = ("op:", "typ:", "ikind:")


def compact_predicate_str(po: "CFunctionPO") -> str:
    """Return a compact, readable rendering of the predicate of a proof
    obligation (for display only; see compact_expression_str)."""
    s = str(po.predicate)
    k = s.find("(")
    if k < 0 or not s.endswith(")"):
        return compact_expression_str(s)
    name = s[:k]
    args = [
        compact_expression_str(a)
        for a in _split_top_level(s[k + 1:-1])
        if not a.startswith(_internal_predicate_args)]
    return name + "(" + ", ".join(args) + ")"


def _source_line(po: "CFunctionPO") -> str:
    """Return the source line of the proof obligation, if available."""
    try:
        line = po.cfile.sourcefile.lines.get(po.line)
    except Exception:
        return ""
    return line.strip() if line is not None else ""


def _po_record(po: "CFunctionPO") -> Dict[str, Any]:
    return {
        "kind": "ppo" if po.is_ppo else "spo",
        "file": po.cfile.name + ".c",
        "function": po.cfun.name,
        "line": po.line,
        "predicate": compact_predicate_str(po),
        "status": po.status,
        "source": _source_line(po)}


def pending_findings(
        cons: ConsolidatedStatus,
        pos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True
) -> List[Dict[str, Any]]:
    """Return the locally safe proof obligations that depend on a supporting
    proof obligation that fails, with the failing supporting proof
    obligations (records, serializable)."""
    result: List[Dict[str, Any]] = []
    for po in pos:
        if not filefilter(po.cfile.name):
            continue
        if cons.category(po) != "dep-fail":
            continue
        record = _po_record(po)
        record["findings"] = sorted(
            [_po_record(spo) for spo in cons.blocking_pos(po)
             if spo.is_finding],
            key=lambda r: (r["file"], r["function"], r["line"]))
        result.append(record)
    return sorted(result, key=lambda r: (r["file"], r["function"], r["line"]))


def pending_findings_tostring(pendingfindings: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    nppos = len([r for r in pendingfindings if r["kind"] == "ppo"])
    nspos = len(pendingfindings) - nppos
    lines.append(
        "\nSafe locally, depending on a failing supporting proof obligation"
        + " (dep-fail; "
        + str(nppos) + " primary, " + str(nspos) + " supporting):")
    for r in pendingfindings:
        kind = "primary" if r["kind"] == "ppo" else "supporting"
        lines.append("")
        lines.append(
            "  " + r["function"] + " (" + r["file"] + ":" + str(r["line"])
            + ", " + kind + ")")
        lines.append("      " + r["predicate"])
        if r.get("source", "") != "":
            lines.append("      " + str(r["line"]) + ": " + r["source"])
        findings = r["findings"]
        lines.append(
            "    fails at " + str(len(findings)) + " call site"
            + ("" if len(findings) == 1 else "s") + ":")
        for f in findings:
            lines.append(
                "    - " + f["function"] + " (" + f["file"] + ":"
                + str(f["line"]) + "): " + f["status"])
            lines.append("        " + f["predicate"])
            if f.get("source", "") != "":
                lines.append("        " + str(f["line"]) + ": " + f["source"])
    return "\n".join(lines)


def ext_callers(
        cons: ConsolidatedStatus,
        ppos: Sequence["CFunctionPO"],
        spos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True
) -> Dict[str, Any]:
    """Return the functions whose external or indirect callers are assumed
    to establish the delegated conditions of the proof obligations in the
    trust-ext category, with their number of call sites in the analyzed code,
    and the number of trust-ext proof obligations that rely only on functions
    without call sites in the analyzed code (serializable)."""
    fns: Dict[Tuple[int, str], Dict[str, Any]] = {}
    summary = {"ppos-uncalled": 0, "ppos-called": 0,
               "spos-uncalled": 0, "spos-called": 0}
    for (kind, pos) in [("ppos", ppos), ("spos", spos)]:
        for po in pos:
            if not filefilter(po.cfile.name):
                continue
            if cons.category(po) != "trust-ext":
                continue
            origins = [
                fn for fn in cons.ext_callers(po)
                if "uncalled" not in cons.ext_caller_linkage(fn)]
            called = False
            for fn in origins:
                callsites = cons.ext_caller_callsites(fn)
                called = called or callsites > 0
                if fn not in fns:
                    fns[fn] = {
                        "file": cons.capp.get_file_by_index(fn[0]).name + ".c",
                        "function": fn[1],
                        "linkage": sorted(cons.ext_caller_linkage(fn)),
                        "callsites": callsites,
                        "ppos": 0,
                        "spos": 0}
                fns[fn][kind] += 1
            summary[kind + ("-called" if called else "-uncalled")] += 1
    result: Dict[str, Any] = dict(summary)
    result["functions"] = sorted(
        fns.values(), key=lambda r: (r["file"], r["function"]))
    return result


def ext_callers_tostring(
        extfns: Dict[str, Any], showfunctions: bool = False) -> str:
    """Return the summary of the trust-ext category; with showfunctions, also
    the table of functions (ext-callers option)."""
    functions: List[Dict[str, Any]] = extfns["functions"]
    if len(functions) == 0:
        return ""
    uncalled = [f for f in functions if f["callsites"] == 0]
    lines: List[str] = []
    lines.append(
        "\nRelies on external or indirect callers (trust-ext): preconditions"
        + " of functions that\nmay be called from outside the analyzed code"
        + " (extern; entry in closed-program mode)\nor indirectly (addrof);"
        + " all their direct call sites in the analyzed code have\nproven"
        + " supporting proof obligations.")
    lines.append(
        "  " + str(len(functions)) + " functions, "
        + str(len(uncalled)) + " without call sites in the analyzed code")
    for kind in ["ppos", "spos"]:
        name = "primary" if kind == "ppos" else "supporting"
        lines.append(
            "  " + name + ": " + str(extfns[kind + "-uncalled"])
            + " rely only on functions without call sites in the analyzed code, "
            + str(extfns[kind + "-called"]) + " (also) on functions with"
            + " call sites")
    if not showfunctions:
        lines.append(
            "  (use --ext-callers to list the " + str(len(functions))
            + " functions with their call sites)")
        return "\n".join(lines)
    fnlen = max(len(f["function"]) for f in functions) + 2
    filelen = max(len(f["file"]) for f in functions) + 2
    lines.append("")
    lines.append(
        "  " + "function".ljust(fnlen) + "file".ljust(filelen)
        + "linkage".ljust(15) + "call sites".rjust(11)
        + "ppos".rjust(7) + "spos".rjust(7))
    lines.append("  " + "-" * (fnlen + filelen + 40))
    for f in functions:
        lines.append(
            "  " + f["function"].ljust(fnlen) + f["file"].ljust(filelen)
            + "+".join(f["linkage"]).ljust(15)
            + str(f["callsites"]).rjust(11)
            + str(f["ppos"]).rjust(7) + str(f["spos"]).rjust(7))
    lines.append(
        "  (ppos/spos: trust-ext proof obligations that rely on the function; a"
        + " proof obligation may\n   rely on several functions)")
    return "\n".join(lines)



def uncalled_functions(
        cons: ConsolidatedStatus,
        ppos: Sequence["CFunctionPO"],
        spos: Sequence["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True
) -> List[Dict[str, Any]]:
    """Return the functions without callers on which the proof obligations
    in the uncalled category rely, with the number of those proof
    obligations (serializable)."""
    fns: Dict[Tuple[int, str], Dict[str, Any]] = {}
    for (kind, pos) in [("ppos", ppos), ("spos", spos)]:
        for po in pos:
            if not filefilter(po.cfile.name):
                continue
            if cons.category(po) != "uncalled":
                continue
            for fn in cons.ext_callers(po):
                if "uncalled" not in cons.ext_caller_linkage(fn):
                    continue
                if fn not in fns:
                    fns[fn] = {
                        "file": cons.capp.get_file_by_index(fn[0]).name + ".c",
                        "function": fn[1],
                        "ppos": 0,
                        "spos": 0}
                fns[fn][kind] += 1
    return sorted(fns.values(), key=lambda r: (r["file"], r["function"]))


def uncalled_functions_tostring(functions: List[Dict[str, Any]]) -> str:
    if len(functions) == 0:
        return ""
    lines: List[str] = []
    lines.append(
        "\nRelies on functions without callers (uncalled): no direct call"
        + " sites, address not\ntaken, not an entry point; the delegated"
        + " conditions hold vacuously (dead code).")
    fnlen = max(len(f["function"]) for f in functions) + 2
    filelen = max(len(f["file"]) for f in functions) + 2
    lines.append(
        "  " + "function".ljust(fnlen) + "file".ljust(filelen)
        + "ppos".rjust(7) + "spos".rjust(7))
    lines.append("  " + "-" * (fnlen + filelen + 14))
    for f in functions:
        lines.append(
            "  " + f["function"].ljust(fnlen) + f["file"].ljust(filelen)
            + str(f["ppos"]).rjust(7) + str(f["spos"]).rjust(7))
    return "\n".join(lines)

def consolidated_status_tostring(
        pporesults: Dict[str, Dict[str, int]],
        sporesults: Dict[str, Dict[str, int]],
        pendingfindings: List[Dict[str, Any]],
        extfns: Dict[str, Any] = {},
        rhlen: int = 28,
        header1: str = "",
        showextcallers: bool = False,
        uncalledfns: List[Dict[str, Any]] = [],
        closedprogram: bool = False,
        entrypoints: List[str] = []) -> str:
    """Return the consolidated-status section of a report (issue 43)."""
    lines: List[str] = []
    lines.append(
        "\n\nConsolidated status"
        + (" (closed program, entry points: " + ", ".join(entrypoints) + ")"
           if closedprogram else ""))
    lines.append("~" * 80)
    lines.append(
        "A proof obligation discharged by an assumption is safe locally; it"
        + " is proven only if\nthe assumption is discharged inside the"
        + " analyzed code, transitively, by proven\nsupporting proof"
        + " obligations. Discharge method api delegates the condition to the"
        + "\ncallers of the function (function precondition): the call sites"
        + " in the analyzed\ncode are checked; only callers outside it or"
        + " indirect callers remain (trust-ext).")
    for c in consolidated_categories:
        lines.append("  " + c.ljust(11) + ": " + consolidated_descriptions[c])
    lines.append("\nPrimary Proof Obligations")
    lines.append(consolidated_tostring(pporesults, rhlen, header1))
    if len(sporesults) > 0:
        lines.append("\nSupporting Proof Obligations")
        lines.append(consolidated_tostring(sporesults, rhlen, header1))
    if len(extfns) > 0:
        lines.extend(_nonempty(
            ext_callers_tostring(extfns, showextcallers)))
    lines.extend(_nonempty(uncalled_functions_tostring(uncalledfns)))
    if len(pendingfindings) > 0:
        lines.append(pending_findings_tostring(pendingfindings))
    return "\n".join(lines)


def consolidated_to_dict(
        cons: ConsolidatedStatus,
        ppos: Sequence["CFunctionPO"],
        spos: Sequence["CFunctionPO"],
        rowkey: Callable[["CFunctionPO"], str],
        filefilter: Callable[[str], bool] = lambda f: True
) -> Dict[str, Any]:
    """Return the consolidated-status results (serializable)."""
    return {
        "closedprogram": cons.closedprogram,
        "entrypoints": cons.entrypoints,
        "ppos": consolidated_counts(cons, ppos, rowkey, filefilter),
        "spos": consolidated_counts(cons, spos, rowkey, filefilter),
        "pendingfindings": pending_findings(
            cons, list(ppos) + list(spos), filefilter),
        "extcallers": ext_callers(cons, ppos, spos, filefilter),
        "uncalled": uncalled_functions(cons, ppos, spos, filefilter)}


def consolidated_dict_tostring(
        consd: Dict[str, Any],
        rhlen: int = 28,
        header1: str = "",
        showextcallers: bool = False) -> str:
    return consolidated_status_tostring(
        consd["ppos"],
        consd["spos"],
        consd["pendingfindings"],
        consd.get("extcallers", {}),
        rhlen=rhlen,
        header1=header1,
        showextcallers=showextcallers,
        uncalledfns=consd.get("uncalled", []),
        closedprogram=consd.get("closedprogram", False),
        entrypoints=consd.get("entrypoints", []))


def _nonempty(s: str) -> List[str]:
    return [s] if len(s) > 0 else []


def proofobligation_stats_tostring(
        pporesults: Dict[str, Dict[str, int]],
        sporesults: Dict[str, Dict[str, int]],
        rhlen: int = 28,
        header1: str = "",
        extradsmethods: List[str] = []) -> str:
    lines: List[str] = []
    lines.append("\nPrimary Proof Obligations")
    lines.append(
        row_method_count_tostring(
            pporesults, perc=True, rhlen=rhlen, header1=header1))
    if len(sporesults) > 0:
        lines.append("\nSupporting Proof Obligations")
        lines.append(
            row_method_count_tostring(
                sporesults, perc=True, rhlen=rhlen, header1=header1))
    return "\n".join(lines)


def project_proofobligation_stats_tostring(
        capp: "CApplication",
        filefilter: Callable[[str], bool] = lambda f: True,
        extradsmethods: List[str] = [],
        level: str = default_analysis_level,
        showextcallers: bool = False,
        closedprogram: bool = False,
        entrypoints: List[str] = ["main"],
        showconsolidated: bool = False) -> str:
    lines: List[str] = []
    allppos = capp.get_ppos()
    allspos = capp.get_spos()
    ppos = filter_analysis_level(allppos, level)
    spos = filter_analysis_level(allspos, level)
    pporesults = get_file_method_count(
        ppos, extradsmethods=extradsmethods, filefilter=filefilter,
        level=level)
    sporesults = get_file_method_count(
        spos, extradsmethods=extradsmethods, filefilter=filefilter,
        level=level)

    rhlen = capp.get_max_filename_length() + 3
    lines.append(
        proofobligation_stats_tostring(
            pporesults,
            sporesults,
            rhlen=rhlen,
            header1="c files",
            extradsmethods=extradsmethods))
    tagpporesults = get_tag_method_count(
        ppos, filefilter=filefilter, extradsmethods=extradsmethods,
        level=level)
    tagsporesults = get_tag_method_count(
        spos, filefilter=filefilter, extradsmethods=extradsmethods,
        level=level)

    lines.append("\n\nProof Obligation Statistics")
    lines.append("~" * 80)
    lines.append(
        proofobligation_stats_tostring(
            tagpporesults, tagsporesults, extradsmethods=extradsmethods))
    if showconsolidated:
        cons = ConsolidatedStatus(capp, closedprogram, entrypoints)
        lines.append(
            consolidated_dict_tostring(
                consolidated_to_dict(
                    cons, ppos, spos, lambda po: po.predicate_name,
                    filefilter),
                showextcallers=showextcallers))
    lines.extend(_nonempty(
        out_of_level_tostring(
            out_of_level_counts(
                allppos, allspos, level, filefilter=filefilter), level)))
    lines.extend(_nonempty(
        unreachable_locations_tostring(
            unreachable_locations(ppos, spos, filefilter=filefilter),
            sum(r["open"] for r in pporesults.values()),
            sum(r["open"] for r in sporesults.values()))))
    return "\n".join(lines)


def project_proofobligation_stats_to_dict(
        capp: "CApplication",
        filefilter: Callable[[str], bool] = lambda f: True,
        extradsmethods: List[str] = [],
        level: str = default_analysis_level,
        closedprogram: bool = False,
        entrypoints: List[str] = ["main"]) -> Dict[str, Any]:
    allppos = capp.get_ppos()
    allspos = capp.get_spos()
    ppos = filter_analysis_level(allppos, level)
    spos = filter_analysis_level(allspos, level)
    pporesults = get_file_method_count(
        ppos, extradsmethods=extradsmethods, filefilter=filefilter,
        level=level)
    sporesults = get_file_method_count(
        spos, extradsmethods=extradsmethods, filefilter=filefilter,
        level=level)
    tagpporesults = get_tag_method_count(
        ppos, filefilter=filefilter, extradsmethods=extradsmethods,
        level=level)
    tagsporesults = get_tag_method_count(
        spos, filefilter=filefilter, extradsmethods=extradsmethods,
        level=level)

    result: Dict[str, Any] = {}
    result["tagresults"] = {}
    result["fileresults"] = {}
    result["stats"] = capp.get_project_counts(filefilter=filefilter)
    result["tagresults"]["ppos"] = tagpporesults
    result["tagresults"]["spos"] = tagsporesults
    result["fileresults"]["ppos"] = pporesults
    result["fileresults"]["spos"] = sporesults
    result["unreachable"] = unreachable_locations(
        ppos, spos, filefilter=filefilter)
    result["analysislevel"] = level
    result["outoflevel"] = out_of_level_counts(
        allppos, allspos, level, filefilter=filefilter)
    cons = ConsolidatedStatus(capp, closedprogram, entrypoints)
    result["consolidated"] = consolidated_to_dict(
        cons, ppos, spos, lambda po: po.predicate_name, filefilter)
    return result


def project_proofobligation_stats_dict_to_string(
        stats_dict: Dict[str, Any],
        showextcallers: bool = False,
        showconsolidated: bool = False) -> str:
    lines: List[str] = []

    pporesults = stats_dict["fileresults"]["ppos"]
    sporesults = stats_dict["fileresults"]["spos"]

    if len(pporesults) > 0:
        rhlen = max([len(x) for x in pporesults])
        lines.append(
            proofobligation_stats_tostring(
                pporesults, sporesults, rhlen=rhlen, header1="c files"))

        lines.append("\n\nProof Obligation Statistics")

        tagpporesults = stats_dict["tagresults"]["ppos"]
        tagsporesults = stats_dict["tagresults"]["spos"]
        lines.append(proofobligation_stats_tostring(tagpporesults, tagsporesults))

        if showconsolidated and "consolidated" in stats_dict:
            lines.append(
                consolidated_dict_tostring(
                    stats_dict["consolidated"],
                    showextcallers=showextcallers))

        lines.extend(_nonempty(
            out_of_level_tostring(
                stats_dict.get("outoflevel", {}),
                str(stats_dict.get("analysislevel", default_analysis_level)))))

        lines.extend(_nonempty(
            unreachable_locations_tostring(
                stats_dict.get("unreachable", []),  # type: ignore
                sum(r["open"] for r in pporesults.values()),
                sum(r["open"] for r in sporesults.values()))))

    else:
        lines.append("Zero primary proof obligations")

    return "\n".join(lines)


def file_proofobligation_stats_tostring(
        cfile: "CFile",
        extradsmethods: List[str] = [],
        level: str = default_analysis_level,
        showextcallers: bool = False,
        closedprogram: bool = False,
        entrypoints: List[str] = ["main"],
        showconsolidated: bool = False) -> str:
    lines: List[str] = []
    allppos = cfile.get_ppos()
    allspos = cfile.get_spos()
    ppos = filter_analysis_level(allppos, level)
    spos = filter_analysis_level(allspos, level)
    pporesults = get_function_method_count(
        ppos, extradsmethods=extradsmethods, level=level)
    sporesults = get_function_method_count(
        spos, extradsmethods=extradsmethods, level=level)

    rhlen = cfile.get_max_functionname_length() + 3
    lines.append(
        proofobligation_stats_tostring(
            pporesults, sporesults, rhlen=rhlen, header1="functions"))

    tagpporesults = get_tag_method_count(
        ppos, extradsmethods=extradsmethods, level=level)
    tagsporesults = get_tag_method_count(
        spos, extradsmethods=extradsmethods, level=level)

    lines.append("\n\nProof Obligation Statistics for file " + cfile.name)
    lines.append("~" * 80)

    lines.append(proofobligation_stats_tostring(tagpporesults, tagsporesults))

    if showconsolidated:
        cons = ConsolidatedStatus(cfile.capp, closedprogram, entrypoints)
        lines.append(
            consolidated_dict_tostring(
                consolidated_to_dict(
                    cons, ppos, spos, lambda po: po.cfun.name),
                rhlen=rhlen,
                header1="functions",
                showextcallers=showextcallers))

    lines.extend(_nonempty(
        out_of_level_tostring(
            out_of_level_counts(allppos, allspos, level), level)))

    lines.extend(_nonempty(
        unreachable_locations_tostring(
            unreachable_locations(ppos, spos),
            sum(r["open"] for r in pporesults.values()),
            sum(r["open"] for r in sporesults.values()))))

    return "\n".join(lines)


def file_global_assumptions_tostring(cfile: "CFile") -> str:
    lines: List[str] = []
    lines.append("\nGlobal assumptions")
    lines.append(("-" * 80))
    polines = set([])
    ppos = cfile.get_ppos()
    spos = cfile.get_spos()
    for po in ppos + spos:
        for a in po.get_global_assumptions():
            polines.add(str(a))
    return "\n".join(sorted(lines) + sorted(list(polines)))


def file_postcondition_assumptions_tostring(cfile: "CFile") -> str:
    lines: List[str] = []
    lines.append("\nPostcondition assumptions")
    lines.append(("-" * 80))
    polines = set([])
    ppos = cfile.get_ppos()
    spos = cfile.get_spos()
    for po in ppos + spos:
        for a in po.get_postcondition_assumptions():
            polines.add(str(a))
    return "\n".join(lines + sorted(list(polines)))


def function_proofobligation_stats_tostring(
        cfunction: "CFunction",
        extradsmethods: List[str] = [],
        level: str = default_analysis_level) -> str:
    lines: List[str] = []
    ppos = filter_analysis_level(cfunction.get_ppos(), level)
    spos = filter_analysis_level(cfunction.get_spos(), level)
    tagpporesults = get_tag_method_count(
        ppos, extradsmethods=extradsmethods, level=level)
    tagsporesults = get_tag_method_count(
        spos, extradsmethods=extradsmethods, level=level)

    lines.append(
        "\n\nProof Obligation Statistics for function " + cfunction.name)
    lines.append("~" * 80)

    lines.append(proofobligation_stats_tostring(tagpporesults, tagsporesults))
    return "\n".join(lines)


def make_po_tag_dict(
        pos: List["CFunctionPO"],
        pofilter: Callable[["CFunctionPO"], bool] = lambda po: True
) -> Dict[str, List["CFunctionPO"]]:
    """Create a predicate tag dictionary from a a list of proof obligations.

    Args:
      pos: list of proof obligations (primary or supporting)
      pofilter: predicate that specifies which proof obligations to include
    Returns:
      dictionary that organizes the proof obligations by predicate tag
    """
    result: Dict[str, List["CFunctionPO"]] = {}
    for po in pos:
        if pofilter(po):
            tag = po.predicate_name
            if tag not in result:
                result[tag] = []
            result[tag].append(po)
    return result


def make_po_file_function_dict(
        pos: List["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True
) -> Dict[str, Dict[str, List["CFunctionPO"]]]:
    """Create a file, function dictionary from a list of proof obligations.

    Args:
      pos: list of proof obligations (primary or supporting)
      filefilter: predicate that specifies which c files to include
    Returns:
      dictionary that organizes the proof obligations by c file
    """
    result: Dict[str, Dict[str, List["CFunctionPO"]]] = {}
    for po in pos:
        cfile = po.cfile.name
        if filefilter(cfile):
            if cfile not in result:
                result[cfile] = {}
            cfun = po.cfun.name
            if cfun not in result[cfile]:
                result[cfile][cfun] = []
            result[cfile][cfun].append(po)
    return result


def tag_file_function_pos_tostring(
        pos: List["CFunctionPO"],
        filefilter: Callable[[str], bool] = lambda f: True,
        pofilter: Callable[["CFunctionPO"], bool] = lambda po: True) -> str:
    lines: List[str] = []
    tagdict = make_po_tag_dict(pos, pofilter=pofilter)
    for tag in sorted(tagdict):
        fundict = make_po_file_function_dict(tagdict[tag], filefilter=filefilter)
        lines.append("\n\n" + tag + "\n" + ("-" * 80))
        for f in sorted(fundict):
            lines.append("\n  File: " + f)
            for ff in sorted(fundict[f]):
                lines.append("    Function: " + ff)
                for po in sorted(fundict[f][ff], key=lambda po: po.line):
                    lines.append((" " * 6) + str(po))
                    if po.is_closed:
                        lines.append((" " * 14) + str(po.explanation))

                    if po.has_diagnostic():
                        amsgs = po.diagnostic.argument_msgs
                        if len(amsgs) > 0:
                            for arg in sorted(amsgs):
                                for amsg in amsgs[arg]:
                                    lines.append((" " * 14) + str(amsg))
                        msgs = po.diagnostic.msgs
                        if len(msgs) > 0:
                            lines.append((" " * 8) + " ---> " + str(msgs[0]))
                            for msg in msgs[1:]:
                                lines.append((" " * 14) + str(msg))
                            lines.append(" ")
                        keys = po.diagnostic.argument_indices
                        try:
                            invd = po.cfun.invdictionary
                            for k in keys:
                                invids = po.diagnostic.get_invariant_ids(k)
                                for id in invids:
                                    inv = invd.get_invariant_fact(id)
                                    if inv.is_nrv_fact:
                                        inv = cast("CInvariantNRVFact", inv)
                                        nrv = inv.non_relational_value
                                        lines.append(
                                            (" " * 14)
                                            + str(k)
                                            + ": "
                                            + str(nrv))
                        except UF.CHCError:
                            pass

                        lines.append(" ")

    return "\n".join(lines)


def get_totals_from_tagtotals(
        tagtotals: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    dsmethods = get_dsmethods([])
    for dm in dsmethods:
        totals[dm] = sum(
            [tagtotals[t][dm] for t in tagtotals if dm in tagtotals[t]])
    return totals


def totals_to_string(
        tagtotals: Dict[str, Dict[str, int]],
        absolute: bool = True,
        do_totals: bool = True) -> List[str]:
    lines: List[str] = []
    rhlen = max([max([len(t) for t in tagtotals]), 12])
    header1 = ""
    dsmethods = get_dsmethods([])
    width = 10
    lines.append(
        get_dsmethod_header(rhlen, dsmethods, header1=header1) + "    %closed")
    barlen = 80 + rhlen
    lines.append("-" * barlen)
    for t in sorted(tagtotals):
        r = [tagtotals[t][dm] for dm in dsmethods]
        rsum = sum(r)
        if rsum == 0:
            continue
        tagopenpct = (1.0 - (float(tagtotals[t]["open"]) / float(rsum))) * 100.0
        s_tagopenpct = str("{:.1f}".format(tagopenpct))
        if absolute:
            lines.append(
                t.ljust(rhlen)
                + "".join([str(x).rjust(width) for x in r])
                + str(sum(r)).rjust(10)
                + s_tagopenpct.rjust(width))
        else:
            lines.append(
                t.ljust(rhlen)
                + "".join(
                    [str("{:.2f}".format(float(x) / float(rsum) * 100.0)).rjust(
                        width)
                     for x in r]))
    if do_totals:
        lines.append("-" * barlen)
        totals = get_totals_from_tagtotals(tagtotals)
        totalcount = sum(totals.values())
        if totalcount > 0:
            tagopenpct = (
                1.0 - (float(totals["open"]) / float(totalcount))) * 100.0
            s_tagopenpct = str("{:.1f}".format(tagopenpct))
            if absolute:
                lines.append(
                    "total".ljust(rhlen)
                    + "".join([str(totals[dm]).rjust(width) for dm in dsmethods])
                    + str(totalcount).rjust(10)
                    + s_tagopenpct.rjust(width))
            scale = float(totalcount) / 100.0
            lines.append(
                "percent".ljust(rhlen)
                + "".join(
                    [str("{:.2f}".format(float(totals[dm]) / scale)).rjust(width)
                        for dm in dsmethods]))
    return lines


def totals_to_presentation_string(
        ppototals: Dict[str, Dict[str, int]],
        spototals: Dict[str, Dict[str, int]],
        projectstats: Dict[str, Tuple[int, int, int]],
        absolute: bool = True,
        totals: bool = True) -> List[str]:
    lines: List[str] = []
    rhlen = max([max([len(t) for t in ppototals]), 12])
    header1 = ""
    dsmethods = get_dsmethods([])
    lines.append(
        " ".rjust(rhlen)
        + "line count".rjust(10)
        + "total ppo's".rjust(15)
        + "%closed".rjust(10)
        + "total spo's".rjust(15)
        + "%closed".rjust(10))
    barlen = 64 + rhlen
    lines.append("-" * barlen)
    for t in sorted(ppototals):
        (lc, _, _) = projectstats[t]
        rppo = [ppototals[t][dm] for dm in dsmethods]
        rspo = [spototals[t][dm] for dm in dsmethods]
        rpposum = sum(rppo)
        rsposum = sum(rspo)
        if rpposum == 0:
            continue
        ppoopenpct = (1.0 - (float(ppototals[t]["open"]) / float(rpposum))) * 100.0
        s_ppoopenpct = str("{:.1f}".format(ppoopenpct))
        if rsposum == 0:
            continue
        spoopenpct = (1.0 - (float(spototals[t]["open"]) / float(rsposum))) * 100.0
        s_spoopenpct = str("{:.1f}".format(spoopenpct))

        if absolute:
            lines.append(
                t.ljust(rhlen)
                + str(lc).rjust(10)
                + str(sum(rppo)).rjust(15)
                + s_ppoopenpct.rjust(10)
                + str(sum(rspo)).rjust(15)
                + s_spoopenpct.rjust(10))
            """
            lines.append(t.ljust(rhlen) + ''.join([str(x).rjust(8) for x in r])
                            + str(sum(r)).rjust(10) + ppoopenpct.rjust(8))
            """
        else:
            rsum = rpposum  # TBD: check
            r = rppo  # TBD: check
            lines.append(
                t.ljust(rhlen)
                + "".join(
                    [str("{:.2f}".format(float(x) / float(rsum) * 100.0)).rjust(8)
                     for x in r]))
    if totals:
        lines.append("-" * barlen)
        lctotal = sum([projectstats[t][0] for t in projectstats])
        dmppototals: Dict[str, int] = {}
        dmspototals: Dict[str, int] = {}
        for dm in dsmethods:
            dmppototals[dm] = sum([ppototals[t][dm] for t in ppototals])
            dmspototals[dm] = sum([spototals[t][dm] for t in spototals])
        ppototalcount = sum(dmppototals.values())
        spototalcount = sum(dmspototals.values())
        if ppototalcount > 0:
            ppotagopenpct = (
                1.0 - (float(dmppototals["open"]) / float(ppototalcount))
            ) * 100.0
            s_ppotagopenpct = str("{:.1f}".format(ppotagopenpct))
            spotagopenpct = (
                1.0 - (float(dmspototals["open"]) / float(spototalcount))
            ) * 100.0
            s_spotagopenpct = str("{:.1f}".format(spotagopenpct))
            if absolute:
                lines.append(
                    "total".ljust(rhlen)
                    + str(lctotal).rjust(10)
                    + str(ppototalcount).rjust(15)
                    + s_ppotagopenpct.rjust(10)
                    + str(spototalcount).rjust(15)
                    + s_spotagopenpct.rjust(10))
            """
            scale = float(totalcount)/100.0
            lines.append('percent'.ljust(rhlen) +
                            ''.join([str('{:.2f}'.format(float(totals[dm])/scale)).rjust(8)
                                        for dm in dsmethods]))
            """
    return lines
