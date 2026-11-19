# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2026 Aarno Labs LLC
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
"""Verification report for users who verify a system (issue 15, part A).

The developer report (chkc c-project report) gives detailed proof-obligation
statistics per file, predicate and discharge method. This report answers the
questions of a user who wants to verify a system, in this order:

1. System boundary: what was analyzed, what information is missing (calls to
   functions that are neither defined nor summarized, indirect calls), what
   is part of the analyzer's model (the summaries of the C standard library
   and POSIX, on a par with the semantics of the language itself), and what
   is assumed across the boundary (summaries of other libraries, user
   contracts, preconditions on callers outside the analyzed code). The
   verification is only as complete as this boundary.
2. Results: the primary proof obligations by property class and consolidated
   status (proven, proven under assumptions, open, violation,
   implementation-defined, value wrap-around); the consolidated status takes
   the supporting proof obligations at call sites into account (issue 43).
3. Open proof obligations by remedy: open because a precondition is not
   established at a call site; because a property of an unmodeled function
   is missing (an assumption only the user can provide, grouped per function
   and phrased as a property the user can confirm from the function's
   documentation); because a
   postcondition of a program function is missing (an intermediate condition,
   to be derived or conjectured and checked, issue 44); because they depend on
   the state of global variables (global/data-structure invariant); or not
   classified (invariant too weak, or a possible defect).
4. Findings: violations individually; implementation-defined and value
   wrap-around findings grouped by predicate.

The classification of open proof obligations by remedy is a heuristic based
on the analyzer's diagnostics (postcondition requests, global variables in
the predicate).
"""

import re

from typing import (
    Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING, cast)

from chc.app.IndexManager import FileVarReference
from chc.proof.ConsolidatedStatus import ConsolidatedStatus
from chc.proof.CFunctionPO import analysis_levels
from chc.reporting.ProofObligations import (
    _po_record, filter_analysis_level, out_of_level_counts,
    unreachable_locations)

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CExp import CExpLval
    from chc.app.CFile import CFile
    from chc.app.CLHost import CLHostVar
    from chc.proof.CFunctionPO import CFunctionPO


"""Property classes (rows of the results table) and their predicates."""
property_classes: List[Tuple[str, List[str]]] = [
    ("memory bounds", [
        "index-lower-bound", "index-upper-bound", "lower-bound",
        "upper-bound", "ptr-lower-bound", "ptr-upper-bound",
        "ptr-upper-bound-deref", "common-base", "common-base-type",
        "null-terminated"]),
    ("pointer validity", [
        "not-null", "null", "valid-mem", "in-scope", "stack-address-escape",
        "allocation-base", "new-memory", "heap-address", "global-address",
        "distinct-region"]),
    ("initialization", ["initialized", "initialized-range"]),
    ("integer arithmetic", [
        "int-overflow", "int-underflow", "uint-overflow", "uint-underflow",
        "not-zero", "non-negative", "width-overflow"]),
    ("conversions", [
        "cast", "pointer-cast", "signed-to-signed-cast-lb",
        "signed-to-signed-cast-ub", "unsigned-to-signed-cast",
        "signed-to-unsigned-cast-lb", "signed-to-unsigned-cast-ub",
        "unsigned-to-unsigned-cast"]),
    ("library call requirements", [
        "no-overlap", "format-string", "format-cast", "var-args",
        "value-constraint", "controlled-resource", "output-parameter",
        "buffer"]),
]

other_class = "other"


def property_class(predicate: str) -> str:
    for (name, predicates) in property_classes:
        if predicate in predicates:
            return name
    return other_class


"""Result columns, in order; the finding columns depend on the level."""
result_columns: List[str] = [
    "proven", "assumed", "no-callers", "open", "violation",
    "implementation-defined", "value-wrap-around"]

result_column_headers: Dict[str, str] = {
    "proven": "proven",
    "assumed": "assumed",
    "no-callers": "no callers",
    "open": "open",
    "violation": "violation",
    "implementation-defined": "impl-def",
    "value-wrap-around": "wrap",
}

"""Remedy groups for open proof obligations, in order."""
remedy_groups: List[Tuple[str, Tuple[str, str]]] = [
    ("call-site",
     ("a precondition is not established at a call site",
      "(fix or strengthen the callers)")),
    ("external-condition",
     ("need a property of a function outside the analyzed code",
      "(an assumption only you can provide; confirm from its documentation)")),
    ("program-postcondition",
     ("need a postcondition of a program function",
      "(to be derived or conjectured; checked)")),
    ("global-state",
     ("depend on the state of global variables",
      "(global or data-structure invariant)")),
    ("unclassified",
     ("not classified (invariant too weak, or a possible defect)", "")),
]

"""User-facing phrasing of the conditions requested from functions outside the
analyzed code, with the contract term. The analyzer requests a sufficient
condition, which may be stronger than what the open proof obligation needs
(issue 47); the phrasing states what the condition means, so that the user
can confirm it as a property of the function itself."""
external_condition_text: Dict[str, Tuple[str, str]] = {
    "preserves-all-memory": (
        "frees nothing",
        "does not deallocate memory (memory valid before the call remains"
        + " valid)"),
    "not-null(return-value)": (
        "returns non-null",
        "the return value is not a null pointer"),
    "initialized((*return-value)))": (
        "returns initialized",
        "the return value points to initialized memory"),
    "initialized(*return-value)": (
        "returns initialized",
        "the return value points to initialized memory"),
    "null-terminated(return-value)": (
        "returns a string",
        "the return value points to a null-terminated string"),
}


def external_condition_property(cond: str) -> str:
    return external_condition_text.get(cond, (cond, ""))[0]


_postrequest_re = re.compile(
    r"submitted postrequest for condition (.+) to (\S+)\s*$")

_identifier_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class VerificationReport:

    def __init__(
            self,
            capp: "CApplication",
            level: str,
            closedprogram: bool = False,
            entrypoints: List[str] = ["main"]) -> None:
        self._capp = capp
        self._level = level
        self._cons = ConsolidatedStatus(capp, closedprogram, entrypoints)
        self._closedprogram = closedprogram
        self._entrypoints = list(entrypoints)
        self._appfunctions: Optional[Set[str]] = None
        self._globals: Dict[int, Set[str]] = {}

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def cons(self) -> ConsolidatedStatus:
        return self._cons

    @property
    def level(self) -> str:
        return self._level

    # --------------------------------------------------------- helpers -----

    @property
    def appfunctions(self) -> Set[str]:
        """Names of the functions defined in the analyzed code."""
        if self._appfunctions is None:
            self._appfunctions = set(
                fn.name
                for cfile in self.capp.cfiles
                for fn in cfile.get_functions())
        return self._appfunctions

    def _is_application_function(self, cfile: "CFile", vid: int) -> bool:
        defref = self.capp.indexmanager.resolve_vid(
            FileVarReference(cfile.index, vid))
        if defref is None or not self.capp.has_file_index(defref.fid):
            return False
        return self.capp.get_file_by_index(defref.fid).has_function_by_index(
            defref.vid)

    def _global_names(self, cfile: "CFile") -> Set[str]:
        """Names of the global variables (not functions) of a file."""
        if cfile.index not in self._globals:
            names: Set[str] = set([])
            for vinfo in cfile.declarations.get_global_varinfos():
                try:
                    if vinfo.vtype.is_function:
                        continue
                except Exception:
                    pass
                names.add(vinfo.vname)
            self._globals[cfile.index] = names
        return self._globals[cfile.index]

    @staticmethod
    def _diagnostic_msgs(po: "CFunctionPO") -> List[str]:
        if not po.has_diagnostic():
            return []
        d = po.diagnostic
        msgs = list(d.msgs_txt)
        for ml in d.argument_msgs_txt.values():
            msgs.extend(ml)
        for ml in d.keyword_msgs.values():
            msgs.extend(ml)
        return msgs

    def _ppos(self) -> List["CFunctionPO"]:
        return filter_analysis_level(self.capp.get_ppos(), self.level)

    # ------------------------------------------------------- boundary -----

    def boundary(self) -> Dict[str, Any]:
        """Return what was analyzed, what is missing, and what is assumed."""
        nfunctions = 0
        missing: Set[str] = set([])
        missingheaders: Dict[str, str] = {}
        unmodeled: Dict[str, Dict[str, Any]] = {}
        summarized: Dict[str, int] = {}
        stdlib: Dict[str, int] = {}
        indirect: List[Dict[str, Any]] = []
        asm: List[Dict[str, Any]] = []
        for cfile in self.capp.cfiles:
            for cfun in cfile.get_functions():
                nfunctions += 1
                for m in cfun.api.missing_summaries:
                    names = m.split("/")
                    missing.add(names[-1])
                    if len(names) == 2:
                        missingheaders[names[-1]] = names[0]
        for cfile in self.capp.cfiles:
            for cfun in cfile.get_functions():
                for ci in cfun.call_instrs:
                    e = ci.callee
                    lval = cast("CExpLval", e).lval if e.is_lval else None
                    if (
                            lval is not None
                            and lval.lhost.is_var
                            and lval.offset.is_no_offset):
                        lhost = cast("CLHostVar", lval.lhost)
                        vid = lhost.vid
                        name = lhost.name
                        if self._is_application_function(cfile, vid):
                            continue
                        if name in missing:
                            r = unmodeled.setdefault(name, {
                                "function": name,
                                "header": missingheaders.get(name, ""),
                                "callsites": 0,
                                "callers": set([])})
                            r["callsites"] += 1
                            r["callers"].add(cfun.name)
                        elif self.cons.is_standard_library_function(name):
                            stdlib[name] = stdlib.get(name, 0) + 1
                        else:
                            summarized[name] = summarized.get(name, 0) + 1
                    else:
                        indirect.append({
                            "file": cfile.name + ".c",
                            "function": cfun.name,
                            "line": ci.location.line})
        for cfile in self.capp.cfiles:
            for cfun in cfile.get_functions():
                for instr in _instrs(cfun):
                    if instr.is_asm:
                        asm.append({
                            "file": cfile.name + ".c",
                            "function": cfun.name,
                            "line": instr.location.line})
        for r in unmodeled.values():
            r["callers"] = len(r["callers"])

        ppos = self._ppos()
        extfns: Dict[Tuple[int, str], Dict[str, Any]] = {}
        uncalled: Dict[Tuple[int, str], int] = {}
        nuser = 0
        for po in ppos + filter_analysis_level(
                self.capp.get_spos(), self.level):
            cat = self.cons.category(po)
            if cat == "trust-user":
                nuser += 1
            if cat not in ["trust-ext", "uncalled"]:
                continue
            for fn in self.cons.ext_callers(po):
                linkage = self.cons.ext_caller_linkage(fn)
                if cat == "uncalled" and "uncalled" in linkage:
                    uncalled[fn] = uncalled.get(fn, 0) + 1
                elif cat == "trust-ext" and "uncalled" not in linkage:
                    if fn not in extfns:
                        extfns[fn] = {
                            "file": self.capp.get_file_by_index(
                                fn[0]).name + ".c",
                            "function": fn[1],
                            "linkage": sorted(linkage),
                            "callsites": self.cons.ext_caller_callsites(fn),
                            "pos": 0}
                    extfns[fn]["pos"] += 1

        nfncontracts = 0
        ngvcontracts = 0
        for cfile in self.capp.cfiles:
            try:
                contracts = cfile.contracts
                nfncontracts += len(contracts.functions)
                ngvcontracts += len(contracts.globalvariables)
            except Exception:
                pass

        unreachable = unreachable_locations(
            ppos, filter_analysis_level(self.capp.get_spos(), self.level))

        return {
            "files": len(list(self.capp.cfiles)),
            "functions": nfunctions,
            "wordsize": self.capp.target_wordsize,
            "level": self.level,
            "closedprogram": self._closedprogram,
            "entrypoints": self._entrypoints,
            "unmodeled": sorted(
                unmodeled.values(),
                key=lambda r: (-r["callsites"], r["function"])),
            "indirect": indirect,
            "asm": asm,
            "unreachable": unreachable,
            "stdlib": stdlib,
            "summarized": summarized,
            "extcallers": sorted(
                extfns.values(), key=lambda r: (r["file"], r["function"])),
            "uncalled": [
                {"file": self.capp.get_file_by_index(fn[0]).name + ".c",
                 "function": fn[1],
                 "pos": n}
                for (fn, n) in sorted(uncalled.items())],
            "functioncontracts": nfncontracts,
            "globalcontracts": ngvcontracts,
            "trustuserpos": nuser,
        }

    # -------------------------------------------------------- results -----

    def result_column(self, po: "CFunctionPO") -> str:
        cat = self.cons.category(po)
        if cat == "proven":
            return "proven"
        if cat in ["trust-lib", "trust-user", "trust-ext"]:
            return "assumed"
        if cat == "uncalled":
            return "no-callers"
        if cat in ["open", "dep-open", "dep-fail"]:
            return "open"
        if po.is_violated:
            return "violation"
        if po.is_implementation_defined:
            return "implementation-defined"
        if po.is_value_wrap_around:
            return "value-wrap-around"
        return "open"

    def results(self) -> Dict[str, Any]:
        """Return the primary proof obligations by property class and result
        column, and the function-level summary."""
        rows: Dict[str, Dict[str, int]] = {}
        fnstatus: Dict[Tuple[str, str], Set[str]] = {}
        for po in self._ppos():
            col = self.result_column(po)
            row = rows.setdefault(
                property_class(po.predicate_name),
                {c: 0 for c in result_columns})
            row[col] += 1
            fnstatus.setdefault((po.cfile.name, po.cfun.name), set([])).add(col)
        functions = {"total": len(fnstatus), "proven": 0, "assumed": 0,
                     "open": 0, "violation": 0, "other-finding": 0}
        for cols in fnstatus.values():
            if "violation" in cols:
                functions["violation"] += 1
            elif cols & set(["implementation-defined", "value-wrap-around"]):
                functions["other-finding"] += 1
            elif cols & set(["open", "no-callers"]):
                functions["open"] += 1
            elif "assumed" in cols:
                functions["assumed"] += 1
            else:
                functions["proven"] += 1
        return {
            "rows": rows,
            "functions": functions,
            "outoflevel": out_of_level_counts(
                self.capp.get_ppos(), [], self.level)}

    # --------------------------------------------------------- remedy -----

    def remedy_group(
            self, po: "CFunctionPO") -> Tuple[str, List[Tuple[str, str]]]:
        """Return the remedy group of an open primary proof obligation, with
        the (function, condition) pairs it would need, if any."""
        if self.cons.category(po) in ["dep-open", "dep-fail"]:
            return ("call-site", [(po.cfun.name, "")])
        requests: List[Tuple[str, str]] = []
        for m in self._diagnostic_msgs(po):
            r = _postrequest_re.match(m)
            if r is not None:
                requests.append((r.group(2), r.group(1)))
        external = [r for r in requests if r[0] not in self.appfunctions]
        if len(external) > 0:
            return ("external-condition", external)
        if len(requests) > 0:
            return ("program-postcondition", requests)
        globalnames = self._global_names(po.cfile)
        used = [
            n for n in _identifier_re.findall(str(po.predicate))
            if n in globalnames]
        if len(used) > 0:
            return ("global-state", [(n, "") for n in sorted(set(used))])
        return ("unclassified", [])

    def remedies(self) -> Dict[str, Any]:
        """Return the open primary proof obligations grouped by remedy, with
        per group the most frequent (function, condition) items."""
        groups: Dict[str, Dict[str, Any]] = {
            g: {"count": 0, "items": {}, "classes": {}}
            for (g, _) in remedy_groups}
        for po in self._ppos():
            if self.result_column(po) != "open":
                continue
            (g, items) = self.remedy_group(po)
            groups[g]["count"] += 1
            pclass = property_class(po.predicate_name)
            groups[g]["classes"][pclass] = (
                groups[g]["classes"].get(pclass, 0) + 1)
            if g == "external-condition":
                # one entry per function, with the properties requested
                conds = groups[g].setdefault("conditions", {})
                for (fn, cond) in items:
                    conds.setdefault(fn, set([])).add(cond)
                keys = set(fn for (fn, _) in items)
            else:
                keys = set(
                    fn + ("|" + cond if cond else "") for (fn, cond) in items)
            for key in keys:
                groups[g]["items"][key] = groups[g]["items"].get(key, 0) + 1
        for grp in groups.values():
            grp["items"] = sorted(
                grp["items"].items(), key=lambda x: (-x[1], x[0]))
            if "conditions" in grp:
                grp["conditions"] = {
                    fn: sorted(c) for (fn, c) in grp["conditions"].items()}
        return groups

    # ------------------------------------------------------- findings -----

    def findings(self) -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []
        grouped: Dict[str, Dict[str, Any]] = {}
        for po in self._ppos():
            col = self.result_column(po)
            if col == "violation":
                violations.append(_po_record(po))
            elif col in ["implementation-defined", "value-wrap-around"]:
                key = col + "|" + po.predicate_name
                g = grouped.setdefault(key, {
                    "category": col, "predicate": po.predicate_name,
                    "count": 0, "examples": []})
                g["count"] += 1
                if len(g["examples"]) < 3:
                    g["examples"].append(_po_record(po))
        violations.sort(key=lambda r: (r["file"], r["line"]))
        return {
            "violations": violations,
            "grouped": sorted(
                grouped.values(), key=lambda g: (-g["count"], g["predicate"]))}

    def counts(self) -> Dict[str, int]:
        """Return the main counts of the report as a flat dictionary (used by
        the regression tests)."""
        b = self.boundary()
        result: Dict[str, int] = {
            "unmodeled-functions": len(b["unmodeled"]),
            "unmodeled-callsites": sum(
                r["callsites"] for r in b["unmodeled"]),
            "indirect-calls": len(b["indirect"]),
            "summarized-functions": len(b["summarized"]) + len(b["stdlib"]),
            "stdlib-functions": len(b["stdlib"]),
            "ext-callers": len(b["extcallers"]),
        }
        rows = self.results()["rows"]
        for c in result_columns:
            result[c] = sum(row[c] for row in rows.values())
        for (g, grp) in self.remedies().items():
            result[g] = grp["count"]
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary": self.boundary(),
            "results": self.results(),
            "remedies": self.remedies(),
            "findings": self.findings()}


def _instrs(cfun: Any) -> List[Any]:
    """Return all instructions of a function (instruction statements, found
    recursively through the sub-statements, as in CStmt.call_instrs)."""
    result: List[Any] = []

    def walk(stmt: Any) -> None:
        if hasattr(stmt, "instrs"):
            result.extend(stmt.instrs)
        for s in stmt.stmts.values():
            walk(s)

    walk(cfun.sbody)
    return result


# ----------------------------------------------------------- rendering -----

def _num(n: int) -> str:
    return f"{n:,}"


def _n(n: int, singular: str, plural: Optional[str] = None) -> str:
    """Return the number with the singular or plural noun."""
    return _num(n) + " " + (
        singular if n == 1 else (plural or singular + "s"))


def _pct(n: int, total: int) -> str:
    return "0.0%" if total == 0 else f"{100.0 * n / total:.1f}%"


def boundary_tostring(b: Dict[str, Any], showall: bool = False) -> str:
    lines: List[str] = []
    lines.append("SYSTEM BOUNDARY")
    ws = b.get("wordsize")
    lines.append(
        "  Analyzed: " + _n(b["files"], "file") + ", "
        + _n(b["functions"], "function")
        + ("" if ws is None else " (" + str(ws) + "-bit target)"))
    lines.append(
        "  Only this build configuration (preprocessor settings) is"
        + " verified.")
    if b["closedprogram"]:
        lines.append(
            "  Closed program: entry points " + ", ".join(b["entrypoints"]))

    unmodeled = b["unmodeled"]
    indirect = b["indirect"]
    asm = b["asm"]
    if len(unmodeled) + len(indirect) + len(asm) > 0:
        lines.append("")
        lines.append(
            "  VERIFICATION IS INCOMPLETE: information is missing for")
        if len(unmodeled) > 0:
            nsites = sum(r["callsites"] for r in unmodeled)
            lines.append(
                "    " + _n(len(unmodeled), "function") + " called ("
                + _n(nsites, "call site") + ") that are neither defined"
                + " in the")
            lines.append(
                "    analyzed code nor summarized: their effects are"
                + " havocked (sound),")
            lines.append(
                "    their preconditions are NOT checked.")
            shown = unmodeled if showall else unmodeled[:10]
            fnlen = max(len(r["function"]) for r in shown) + 2
            for r in shown:
                lines.append(
                    "      " + r["function"].ljust(fnlen)
                    + _n(r["callsites"], "call site").rjust(14)
                    + (("  (declared in " + r["header"] + ")")
                       if r["header"] else ""))
            if len(shown) < len(unmodeled):
                lines.append(
                    "      ... and " + str(len(unmodeled) - len(shown))
                    + " more (use --all)")
        if len(indirect) > 0:
            nfns = len(set((r["file"], r["function"]) for r in indirect))
            lines.append(
                "    " + _n(len(indirect), "indirect call") + " in "
                + _n(nfns, "function") + ": callees unknown; effects"
                + " havocked,")
            lines.append(
                "    callee preconditions not checked.")
        if len(asm) > 0:
            lines.append(
                "    " + _n(len(asm), "inline assembly statement")
                + ": not analyzed.")
    else:
        lines.append(
            "  No calls to unmodeled functions, indirect calls, or inline"
            + " assembly.")
    lines.append(
        "    Not modeled: concurrency (interrupts, signal handlers,"
        + " threads) and")
    lines.append(
        "    changes of volatile objects by other agents.")

    stdlib = b.get("stdlib", {})
    if len(stdlib) > 0:
        lines.append("")
        lines.append("  Part of the analyzer's model of C:")
        lines.append(
            "    " + _n(len(stdlib), "C standard library / POSIX function")
            + " (" + _n(sum(stdlib.values()), "call site") + "), as"
            + " specified")
        lines.append(
            "    by the analyzer's library summaries (assumes a hosted"
            + " implementation,")
        lines.append(
            "    C11 4p6, that conforms to the standard); counted as proven")

    lines.append("")
    lines.append("  Assumed (trusted):")
    summarized = b["summarized"]
    if len(summarized) > 0:
        lines.append(
            "    " + _n(len(summarized), "other external function")
            + " (" + _n(sum(summarized.values()), "call site")
            + "), as specified by library")
        lines.append("    summaries or declared attributes")
    ext = b["extcallers"]
    if len(ext) > 0:
        uncalledinside = len([f for f in ext if f["callsites"] == 0])
        lines.append(
            "    " + _n(len(ext), "function") + " callable from outside the"
            + " analyzed code or indirectly:")
        lines.append(
            "      their preconditions are assumed at those call sites ("
            + _num(uncalledinside)
            + (" has" if uncalledinside == 1 else " have"))
        lines.append(
            "      no call site in the analyzed code)")
    lines.append(
        "    user contracts: " + _n(b["functioncontracts"], "function contract")
        + ", " + _n(b["globalcontracts"], "global-variable contract"))

    notes: List[str] = []
    if len(b["uncalled"]) > 0:
        notes.append(
            "    " + _n(len(b["uncalled"]), "function") + " without callers:"
            + " their delegated conditions hold")
        notes.append(
            "    vacuously and are not counted as proven")
    unreachable = b["unreachable"]
    if len(unreachable) > 0:
        notes.append(
            "    " + _n(len(unreachable), "location") + " proven"
            + " unreachable; this is rare in real code")
        notes.append(
            "    and may point to an analysis imprecision (see chkc"
            + " c-project report)")
    if len(notes) > 0:
        lines.append("")
        lines.append("  Attention:")
        lines.extend(notes)
    return "\n".join(lines)


def results_tostring(r: Dict[str, Any], level: str) -> str:
    rows: Dict[str, Dict[str, int]] = r["rows"]
    levelcols = {
        "undefined-behavior": ["violation"],
        "implementation-defined": ["violation", "implementation-defined"],
        "value-wrap-around": [
            "violation", "implementation-defined", "value-wrap-around"]}
    columns = ["proven", "assumed"]
    if any(row["no-callers"] > 0 for row in rows.values()):
        columns.append("no-callers")
    columns.append("open")
    columns.extend(levelcols[level])
    totals = {c: sum(row[c] for row in rows.values()) for c in columns}
    total = sum(totals.values())

    lines: List[str] = []
    lines.append(
        "RESULTS (" + _num(total) + " primary proof obligations, level "
        + level + ")")
    rhlen = 26
    width = 11
    lines.append(
        "  " + "".ljust(rhlen)
        + "".join(result_column_headers[c].rjust(width) for c in columns))
    order = [name for (name, _) in property_classes] + [other_class]
    for name in order:
        if name not in rows:
            continue
        row = rows[name]
        lines.append(
            "  " + name.ljust(rhlen)
            + "".join(
                (_num(row[c]) if row[c] > 0 else "-").rjust(width)
                for c in columns))
    lines.append("  " + "-" * (rhlen + width * len(columns)))
    lines.append(
        "  " + "total".ljust(rhlen)
        + "".join(_num(totals[c]).rjust(width) for c in columns))
    lines.append(
        "  " + "".ljust(rhlen)
        + "".join(
            (_pct(totals[c], total) if c in ["proven", "assumed", "open"]
             else "").rjust(width)
            for c in columns))
    lines.append(
        "  proven: no assumptions, or all discharged inside the analyzed"
        + " code, transitively;")
    lines.append(
        "  assumed: relies on the assumptions listed under SYSTEM BOUNDARY")

    fns = r["functions"]
    lines.append(
        "  Functions (" + _num(fns["total"]) + " with proof obligations):"
        + " all proven " + _num(fns["proven"])
        + ", proven under assumptions " + _num(fns["assumed"]) + ",")
    lines.append(
        "    with violations " + _num(fns["violation"])
        + ", with other findings only " + _num(fns["other-finding"])
        + ", with open " + _num(fns["open"]))

    outoflevel = r.get("outoflevel", {})
    for cat in analysis_levels:
        if cat not in outoflevel or "ppos" not in outoflevel[cat]:
            continue
        d = outoflevel[cat]["ppos"]
        nfound = sum(n for (s, n) in d.items() if s == cat)
        lines.append(
            "  Not shown at this level: " + cat + " ("
            + _num(sum(d.values())) + " checked, " + _num(nfound)
            + " occur;")
        lines.append(
            "    use --analysis-level " + analysis_levels[-1] + ")")
    return "\n".join(lines)


def remedies_tostring(
        groups: Dict[str, Any], showall: bool = False) -> str:
    total = sum(g["count"] for g in groups.values())
    lines: List[str] = []
    lines.append("OPEN PROOF OBLIGATIONS BY REMEDY (" + _num(total) + ")")
    nitems = 1000000 if showall else 5
    for (name, description) in remedy_groups:
        g = groups[name]
        if g["count"] == 0:
            continue
        lines.append(
            "  " + _num(g["count"]).rjust(7) + "  " + description[0])
        if description[1]:
            lines.append("           " + description[1])
        if name == "unclassified":
            classes = sorted(g["classes"].items(), key=lambda x: -x[1])
            for (c, n) in classes:
                lines.append("           " + _num(n).rjust(6) + "  " + c)
            continue
        if name == "external-condition":
            conds: Dict[str, List[str]] = g.get("conditions", {})
            shown = g["items"][:nitems]
            fnlen = max([len(fn) for (fn, _) in shown] + [0]) + 2
            used: Set[str] = set([])
            for (fn, n) in shown:
                cl = conds.get(fn, [])
                used |= set(cl)
                lines.append(
                    "           " + _num(n).rjust(6) + "  " + fn.ljust(fnlen)
                    + ", ".join(external_condition_property(c) for c in cl))
            if len(g["items"]) > nitems:
                lines.append(
                    "           ... " + _num(len(g["items"]) - nitems)
                    + " more functions (use --all)")
            legend = sorted(set(
                external_condition_text[c] for c in used
                if c in external_condition_text))
            for (prop, meaning) in legend:
                lines.append("           " + prop + ":")
                lines.append("             " + meaning)
            continue
        for (key, n) in g["items"][:nitems]:
            if "|" in key:
                (fn, cond) = key.split("|", 1)
                text = fn + ": " + cond
            else:
                text = key
            label = {
                "call-site": "precondition of ",
                "global-state": "global ",
            }.get(name, "")
            lines.append(
                "           " + _num(n).rjust(6) + "  " + label + text)
        if len(g["items"]) > nitems:
            lines.append(
                "           ... " + _num(len(g["items"]) - nitems)
                + " more (use --all)")
    lines.append(
        "  (classification heuristic, based on the analyzer's"
        + " diagnostics)")
    return "\n".join(lines)


def no_violations_caveat(
        results: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    """Return the qualification of 'no violations found': absence of
    undefined behavior is established only if no proof obligations are open
    and no information is missing, and then only under the assumptions
    across the system boundary."""
    rows: Dict[str, Dict[str, int]] = results["rows"]
    nopen = sum(row["open"] for row in rows.values())
    nassumed = sum(row["assumed"] for row in rows.values())
    missing = len(b["unmodeled"]) + len(b["indirect"]) + len(b["asm"])
    lines: List[str] = []
    if nopen > 0 or missing > 0:
        lines.append(
            "  This does NOT establish the absence of undefined behavior:")
        if nopen > 0:
            lines.append(
                "    - " + _n(nopen, "proof obligation") + " "
                + ("is open; it" if nopen == 1 else "are open; any of them")
                + " may be a violation")
            lines.append(
                "      (see OPEN PROOF OBLIGATIONS BY REMEDY)")
        if missing > 0:
            lines.append(
                "    - verification is incomplete: information is missing"
                + " (calls to unmodeled")
            lines.append(
                "      functions, indirect calls, or inline assembly; see"
                + " SYSTEM BOUNDARY)")
        lines.append(
            "  Absence of undefined behavior is established only when no"
            + " proof")
        lines.append(
            "  obligations are open and no information is missing.")
    else:
        lines.append(
            "  All proof obligations are discharged and no information is"
            + " missing:")
        lines.append(
            "  the analyzed code has no undefined behavior for this build"
            + " configuration,")
        lines.append(
            "  within the limits stated under SYSTEM BOUNDARY"
            + (" (including the assumptions)." if nassumed > 0 else "."))
    return lines


def violations_caveat(
        results: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    """Return the qualification of a list of violations: it is not
    exhaustive while proof obligations are open or information is missing."""
    rows: Dict[str, Dict[str, int]] = results["rows"]
    nopen = sum(row["open"] for row in rows.values())
    missing = len(b["unmodeled"]) + len(b["indirect"]) + len(b["asm"])
    lines: List[str] = []
    if nopen > 0 or missing > 0:
        lines.append("  This list may be incomplete:")
    if nopen > 0:
        lines.append(
            "    - " + _n(nopen, "proof obligation") + " "
            + ("is open; it" if nopen == 1 else "are open; any of them")
            + " may be a further violation")
    if missing > 0:
        lines.append(
            "    - information is missing (see SYSTEM BOUNDARY)")
    return lines


def findings_tostring(
        f: Dict[str, Any],
        showall: bool = False,
        results: Optional[Dict[str, Any]] = None,
        boundary: Optional[Dict[str, Any]] = None) -> str:
    lines: List[str] = []
    violations = f["violations"]
    lines.append("FINDINGS")
    if len(violations) == 0:
        lines.append("  No violations (undefined behavior) found.")
        if results is not None and boundary is not None:
            lines.extend(no_violations_caveat(results, boundary))
    else:
        lines.append(
            "  " + _n(len(violations), "violation") + " (undefined"
            + " behavior on every execution reaching the")
        lines.append(
            "  location, or a witness exists):")
        shown = violations if showall else violations[:20]
        for v in shown:
            lines.append(
                "    " + v["file"] + ":" + str(v["line"]) + " ("
                + v["function"] + ")  " + v["predicate"])
            if v["source"]:
                lines.append("        " + v["source"])
        if len(shown) < len(violations):
            lines.append(
                "    ... " + str(len(violations) - len(shown))
                + " more (use --all)")
        if results is not None and boundary is not None:
            lines.extend(violations_caveat(results, boundary))
    for g in f["grouped"]:
        lines.append(
            "  " + _num(g["count"]) + " " + g["category"] + ": "
            + g["predicate"] + ", e.g.")
        for e in g["examples"]:
            lines.append(
                "    " + e["file"] + ":" + str(e["line"]) + " ("
                + e["function"] + ")  " + e["predicate"])
    return "\n".join(lines)


def verification_report_tostring(
        d: Dict[str, Any], projectname: str, showall: bool = False) -> str:
    b = d["boundary"]
    title = "CodeHawk-C verification report: " + projectname
    lines: List[str] = []
    lines.append(title)
    lines.append("=" * 80)
    lines.append(boundary_tostring(b, showall=showall))
    lines.append("")
    lines.append(results_tostring(d["results"], b["level"]))
    lines.append("")
    lines.append(remedies_tostring(d["remedies"], showall=showall))
    lines.append("")
    lines.append(findings_tostring(
        d["findings"], showall=showall, results=d["results"], boundary=b))
    return "\n".join(lines)
