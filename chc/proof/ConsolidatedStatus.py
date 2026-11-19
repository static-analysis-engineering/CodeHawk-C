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
"""Consolidated (project-level) status of proof obligations (issue 43).

A proof obligation that is discharged by an assumption is safe *locally*: its
condition holds provided the assumption holds (assume-guarantee reasoning).
Whether the assumption holds is a separate question, answered elsewhere:

- an api assumption (precondition of the function) is delegated to the callers
  of the function, where it becomes a supporting proof obligation at every
  call site; these supporting proof obligations may in turn be discharged by
  assumptions of the caller;
- a postcondition assumption is guaranteed by the callee: by a library summary
  or by a user contract (trusted);
- a global assumption is guaranteed by the global contract (trusted).

The consolidated status follows these dependencies over the whole application,
in the style of Frama-C's report consolidation (Valid / Valid under
hypotheses / Considered valid): only a proof obligation whose assumptions are
all discharged inside the analyzed code, transitively, by proof obligations
that are themselves proven is *proven*. The others rely on trusted
assumptions (library summaries, user contracts, or preconditions on callers
the analysis cannot see: callers outside the analyzed code and indirect
callers) or depend on a supporting proof obligation that is open or fails.

Note the two views of a function precondition: per proof obligation, an api
assumption delegates the condition to the callers of the function (the
discharge method "api"); in the consolidated view, the callers that are
visible (direct call sites in the analyzed code) are checked, so only the
invisible callers remain a trusted assumption (trust-ext). A static function
whose address is not taken has only visible callers; its delegated proof
obligations are proven or depend on open/failing ones, never trusted.

Comparison with Frama-C: proven ~ Valid; dep-open/dep-fail ~ Valid under
hypotheses; open ~ Unknown; finding ~ Invalid (undefined behavior). Frama-C
reports the trust-* categories as Valid, resting on Considered-valid
properties (specifications of functions without body, entry-point
preconditions); here they are kept separate.

The dependencies may be cyclic (recursion). The set of reasons is computed as
a least fixpoint (equivalently, the proven proof obligations form the
greatest fixpoint): a cycle whose proof obligations depend on nothing else is
proven, by induction on the depth of the call.

Library summaries of the C standard library (C11 clause 7) and POSIX are
part of the analyzer's model of the language and its standard environment,
on a par with its model of the semantics of C11 clause 6: a postcondition
from such a summary is not a reason (it is reported once, as part of the
system boundary). The summaries of other libraries (zlib, pcre, Linux- or
glibc-specific functions) depend on the version and configuration of the
library and remain trusted assumptions (lib). With stdlib_proven=False all
library summaries are reasons (developer view).

Reasons (per proof obligation, union over its assumptions and, transitively,
over its supporting proof obligations):

- lib      : postcondition of an external function that is not part of the
             standard library (summary of another library, or attribute)
- contract : user function contract or global contract (trusted)
- extern   : precondition of a function with external linkage: callers
             outside the application are not checked (not in closed-program
             mode, where the analyzed code is the whole program and only the
             entry points are called from outside) (the functions and
             their number of call sites in the analyzed code are recorded,
             see ext_callers)
- entry    : precondition of an entry point of a closed program (default
             main): established by the environment (closed-program mode)
- addrof   : precondition of a function whose address is taken: indirect
             calls have no call-site proof obligations
- uncalled : precondition of a function that has no callers: no direct call
             sites, address not taken, and not an entry point; static
             functions in both modes, and functions with external linkage in
             closed-program mode. The delegated conditions hold vacuously;
             following the unreachability policy, this is reported
             explicitly (category uncalled), never counted as proven
- unlinked : a direct call site of the function has no supporting proof
             obligation for the assumption (yet)
- open     : a supporting proof obligation is open
- finding  : a supporting proof obligation fails (violation,
             implementation-defined, value wrap-around)
"""

from typing import (
    Dict, FrozenSet, List, Optional, Set, Tuple, TYPE_CHECKING)

from chc.app.IndexManager import FileVarReference

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.proof.AssumptionType import (
        ApiAssumptionType, GlobalApiAssumptionType, PostconditionType)
    from chc.proof.CFunctionPO import CFunctionPO


"""Consolidated categories, in the order in which they are reported. Every
proof obligation is in exactly one category:

- proven     : closed without assumptions (stmt, local, dead-code), or safe
               with all assumptions discharged inside the analyzed code,
               transitively, by proven proof obligations
- trust-lib  : relies on library summaries outside the standard library
- trust-user : relies on user function contracts or the global contract (and
               possibly library summaries)
- trust-ext  : relies on preconditions on callers the analysis cannot see:
               callers outside the analyzed code (external linkage) or
               indirect callers (address taken); all visible call sites have
               proven supporting proof obligations
- uncalled   : relies on a function without callers (dead code: the
               delegated conditions hold vacuously)
- dep-open   : safe locally, but depends on a supporting proof obligation that
               is open (or missing)
- dep-fail   : safe locally, but depends on a supporting proof obligation that
               fails
- open       : open
- finding    : violation, implementation-defined, or value wrap-around
"""
consolidated_categories: List[str] = [
    "proven", "trust-lib", "trust-user", "trust-ext", "uncalled", "dep-open",
    "dep-fail", "open", "finding"]

consolidated_descriptions: Dict[str, str] = {
    "proven": (
        "no assumptions, or all discharged inside the analyzed code,"
        + " transitively"),
    "trust-lib": "relies on non-standard library summaries or attributes",
    "trust-user": "relies on user function or global contracts",
    "trust-ext": (
        "relies on preconditions on external or indirect callers, or on"
        + " entry points"),
    "uncalled": "relies on a function without callers (vacuous)",
    "dep-open": "depends on an open supporting proof obligation",
    "dep-fail": "depends on a failing supporting proof obligation",
    "open": "open",
    "finding": "violation / implementation-defined / wrap-around",
}

POKey = Tuple[int, str, bool, int]

"""Function in the application: (file index, function name)."""
FnKey = Tuple[int, str]


"""Headers (as reported in the function api: the declaring header file
without directory and extension) of the C standard library (C11 clause 7),
POSIX (IEEE Std 1003.1-2017), and the compiler builtins, for which the
analyzer has library summaries. A function counts as a standard-library
function only if it is declared in one of these headers and has a summary.
The other summary directories (zlib, pcre, ltdl, libio, epoll, prctl,
sendfile, sigthread, sysmacros, ioctl) are library- or platform-specific."""
standard_library_headers: FrozenSet[str] = frozenset([
    # C11 clause 7
    "assert", "ctype", "errno", "locale", "mathcalls", "signal", "stdio",
    "stdlib", "string", "time", "wchar", "wctype",
    # POSIX.1-2017
    "crypt", "dirent", "dlfcn", "fcntl", "getopt", "grp", "in", "inet",
    "mman", "netdb", "poll", "pthread", "pwd", "regex", "resource", "select",
    "socket", "stat", "syslog", "uio", "unistd", "wait",
    # compiler builtins (part of the implementation)
    "builtins"])


def po_key(po: "CFunctionPO") -> POKey:
    return (po.cfile.index, po.cfun.name, po.is_ppo, po.po_index)


def reasons_category(reasons: FrozenSet[str]) -> str:
    """Return the consolidated category of a locally safe proof obligation
    with the given reasons (the weakest reason determines the category)."""
    if len(reasons) == 0:
        return "proven"
    if "finding" in reasons:
        return "dep-fail"
    if "open" in reasons or "unlinked" in reasons:
        return "dep-open"
    if "extern" in reasons or "addrof" in reasons or "entry" in reasons:
        return "trust-ext"
    if "uncalled" in reasons:
        return "uncalled"
    if "contract" in reasons:
        return "trust-user"
    return "trust-lib"


class ConsolidatedStatus:
    """Consolidated status of all proof obligations of an application."""

    def __init__(
            self,
            capp: "CApplication",
            closedprogram: bool = False,
            entrypoints: List[str] = ["main"],
            stdlib_proven: bool = True) -> None:
        """With closedprogram, the analyzed code is the whole program: only
        the entry points are called from outside it. With stdlib_proven,
        postconditions from standard-library summaries are part of the model
        (not a reason)."""
        self._capp = capp
        self._stdlib_proven = stdlib_proven
        self._libheaders: Dict[str, str] = {}
        self._unsummarized: Set[str] = set([])
        self._closedprogram = closedprogram
        self._entrypoints = list(entrypoints)
        # locally safe proof obligations with external dependencies:
        # key -> (reasons from the assumptions themselves, supporting pos)
        self._deps: Dict[
            POKey, Tuple[Set[str], List["CFunctionPO"]]] = {}
        self._reasons: Dict[POKey, FrozenSet[str]] = {}
        # functions whose callers outside the application (external linkage)
        # or indirect callers (address taken) are assumed to establish the
        # delegated conditions: per function the linkage reasons and the
        # number of direct call sites in the application
        self._extcallers: Dict[FnKey, Tuple[FrozenSet[str], int]] = {}
        self._origins: Dict[POKey, FrozenSet[FnKey]] = {}
        self._iterations = 0
        self._compute()

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def closedprogram(self) -> bool:
        return self._closedprogram

    @property
    def entrypoints(self) -> List[str]:
        return self._entrypoints

    @property
    def iterations(self) -> int:
        """Number of fixpoint iterations (including the final stable one)."""
        return self._iterations

    def _address_taken_functions(self) -> Set[str]:
        result: Set[str] = set([])
        for cfile in self.capp.cfiles:
            for vinfo in cfile.declarations.get_global_varinfos():
                if vinfo.vaddrof:
                    result.add(vinfo.vname)
        return result

    def _is_application_function(self, cfile: "CFile", vid: int) -> bool:
        """Return true if the function with local vid in cfile is defined in
        the application."""
        defref = self.capp.indexmanager.resolve_vid(
            FileVarReference(cfile.index, vid))
        if defref is None or not self.capp.has_file_index(defref.fid):
            return False
        return self.capp.get_file_by_index(defref.fid).has_function_by_index(
            defref.vid)

    def library_header(self, fname: str) -> Optional[str]:
        """Return the declaring header of an external function called in the
        application (without directory and extension)."""
        return self._libheaders.get(fname)

    def is_standard_library_function(self, fname: str) -> bool:
        """Return true if the function is declared in a standard header and
        the analyzer has a summary for it."""
        return (
            self.library_header(fname) in standard_library_headers
            and fname not in self._unsummarized)

    def _callee_name(self, cfile: "CFile", vid: int) -> Optional[str]:
        try:
            return cfile.get_global_varinfo(vid).vname
        except Exception:
            return None

    def _compute(self) -> None:
        addrof = self._address_taken_functions()
        for cfile in self.capp.cfiles:
            for cfun in cfile.get_functions():
                for (header, fname) in cfun.api.library_calls:
                    self._libheaders[fname] = header
                for m in cfun.api.missing_summaries:
                    self._unsummarized.add(m.split("/")[-1])
        origins: Dict[POKey, Set[FnKey]] = {}
        for po in self.capp.get_ppos() + self.capp.get_spos():
            if not (po.is_safe and po.is_delegated):
                continue
            fixed: Set[str] = set([])
            origin: Set[FnKey] = set([])
            support: List["CFunctionPO"] = []
            cfun = po.cfun
            cfile = po.cfile
            for a in po.get_assumptions():
                if a.is_contract_assumption:
                    pa: "PostconditionType" = a   # type: ignore
                    if self._is_application_function(cfile, pa.callee):
                        fixed.add("contract")
                    else:
                        name = self._callee_name(cfile, pa.callee)
                        if not (
                                self._stdlib_proven
                                and name is not None
                                and self.is_standard_library_function(name)):
                            fixed.add("lib")
                elif a.is_global_assumption or a.is_global_api_assumption:
                    fixed.add("contract")
                elif a.is_api_assumption:
                    aa: "ApiAssumptionType" = a   # type: ignore
                    apiid = aa.predicate.index
                    callsites = self.capp.get_callsites(
                        cfile.index, cfun.svar.vid)
                    linkage: Set[str] = set([])
                    if self.closedprogram:
                        if cfun.name in self.entrypoints:
                            linkage.add("entry")
                    elif cfun.svar.vstorage != "s":
                        linkage.add("extern")
                    if cfun.name in addrof:
                        linkage.add("addrof")
                    if len(linkage) == 0 and len(callsites) == 0:
                        linkage.add("uncalled")
                    if len(linkage) > 0:
                        fixed |= linkage
                        fnkey = (cfile.index, cfun.name)
                        origin.add(fnkey)
                        self._extcallers[fnkey] = (
                            frozenset(linkage), len(callsites))
                    for (_, cs) in callsites:
                        if apiid in cs.spos:
                            support.extend(cs.spos[apiid])
                        else:
                            fixed.add("unlinked")
            self._deps[po_key(po)] = (fixed, support)
            origins[po_key(po)] = origin

        reasons: Dict[POKey, Set[str]] = {
            k: set(v[0]) for (k, v) in self._deps.items()}
        changed = True
        while changed:
            changed = False
            self._iterations += 1
            for (k, (_, support)) in self._deps.items():
                r = reasons[k]
                o = origins[k]
                n = len(r) + len(o)
                for spo in support:
                    if spo.is_open:
                        r.add("open")
                    elif spo.is_finding:
                        r.add("finding")
                    else:
                        r |= reasons.get(po_key(spo), set([]))
                        o |= origins.get(po_key(spo), set([]))
                if len(r) + len(o) != n:
                    changed = True
        self._reasons = {k: frozenset(v) for (k, v) in reasons.items()}
        self._origins = {k: frozenset(v) for (k, v) in origins.items()}

    def reasons(self, po: "CFunctionPO") -> FrozenSet[str]:
        """Return the reasons why a closed proof obligation is not proven
        (empty if it is proven, or not locally safe)."""
        return self._reasons.get(po_key(po), frozenset([]))

    def ext_callers(self, po: "CFunctionPO") -> FrozenSet[FnKey]:
        """Return the functions, reached through the delegated conditions of
        the proof obligation (transitively), whose callers outside the
        application or indirect callers are assumed to establish them."""
        return self._origins.get(po_key(po), frozenset([]))

    def ext_caller_linkage(self, fn: FnKey) -> FrozenSet[str]:
        """Return the reasons (extern, addrof, entry) why the function may
        have callers that are not checked, or uncalled if it has none."""
        return self._extcallers[fn][0]

    def ext_caller_callsites(self, fn: FnKey) -> int:
        """Return the number of direct call sites of the function in the
        application (all of them have supporting proof obligations that are
        checked)."""
        return self._extcallers[fn][1]

    def category(self, po: "CFunctionPO") -> str:
        """Return the consolidated category of the proof obligation (one of
        consolidated_categories)."""
        if po.is_open:
            return "open"
        if po.is_finding:
            return "finding"
        return reasons_category(self.reasons(po))

    def is_proven(self, po: "CFunctionPO") -> bool:
        return self.category(po) == "proven"

    def supporting_pos(self, po: "CFunctionPO") -> List["CFunctionPO"]:
        """Return the call-site supporting proof obligations that discharge
        the api assumptions of the proof obligation (direct only)."""
        return list(self._deps.get(po_key(po), (set([]), []))[1])

    def blocking_pos(self, po: "CFunctionPO") -> List["CFunctionPO"]:
        """Return the supporting proof obligations, direct or transitive,
        that are open or fail and on which the proof obligation depends."""
        result: List["CFunctionPO"] = []
        seen: Set[POKey] = set([po_key(po)])
        worklist = self.supporting_pos(po)
        while len(worklist) > 0:
            spo = worklist.pop()
            k = po_key(spo)
            if k in seen:
                continue
            seen.add(k)
            if spo.is_open or spo.is_finding:
                result.append(spo)
            else:
                worklist.extend(self.supporting_pos(spo))
        return result

    def count(self, pos: List["CFunctionPO"]) -> Dict[str, int]:
        result: Dict[str, int] = {c: 0 for c in consolidated_categories}
        for po in pos:
            result[self.category(po)] += 1
        return result
