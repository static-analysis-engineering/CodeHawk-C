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
"""Boundary of a system of separately analyzed modules (two-pass verification).

Collection step of the system-level bootstrapping (design doc "CodeHawk-C
Contracts", section "System-level bootstrapping: two passes"). Every module
(a CodeHawk-C project) has been analyzed cold, without external companions.
For the set of modules this collects:

- boundary functions: functions called by a module that are neither defined
  in it nor specified by a library summary, and that another module of the
  set defines (the provider); their headers get external companions;
- external functions: such functions that no module of the set defines (not
  analyzed: trusted companions or library summaries);
- conflicts: functions defined with external linkage by more than one module
  (C11 6.9p5 allows at most one external definition in a program);
- indirect calls: the callee is unknown; the pointer type is
  recorded as the carrier of a future function-pointer typedef contract;
- address-taken functions: functions whose address is taken may be
  called from other modules through a pointer, so their preconditions are
  assumptions on those callers;
- gaps: functions declared in a header of the calling module itself and
  defined nowhere (a source missing from the module's compile database).

For every boundary function it records the clients' requests (external
conditions), and the provider's api assumptions (draft preconditions) and
proven postcondition guarantees. Draft companions are written per header with
the provenance of every condition, for review by the user.
"""

import json
import os
import re

from typing import Any, cast, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from chc.reporting.VerificationReport import (
    VerificationReport, external_condition_text)

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CExp import CExp, CExpCastE, CExpLval
    from chc.app.CFunction import CFunction
    from chc.app.CInstr import CCallInstr
    from chc.app.CLHost import CLHostMem, CLHostVar
    from chc.app.CLval import CLval
    from chc.app.COffset import COffset, CFieldOffset
    from chc.app.CTyp import CTyp, CTypArray, CTypNamed, CTypPtr
    from chc.app.CVarInfo import CVarInfo


# condition (analyzer term) -> attribute that states it in a companion
CONDITION_ATTRIBUTE = {
    "preserves-all-memory": "__chkc_preserves_all_memory__",
    "not-null(return-value)": "returns_nonnull",
}

# conditions that are side effects (frame), as opposed to postconditions
EFFECT_CONDITIONS = set(["preserves-all-memory"])


def _project_root(capp: "CApplication") -> str:
    names = [cf.name for cf in capp.cfiles]
    return os.path.commonpath(names) if names else ""


def _parameter_names(vinfo: "CVarInfo") -> List[str]:
    try:
        fargs = vinfo.vtype.funargs     # type: ignore
        return [a.name for a in fargs.arguments] if fargs is not None else []
    except Exception:
        return []


def _type_name(t: "CTyp") -> str:
    """The type as written. Note: CIL (goblint-cil 2.0.6) unrolls typedefs
    of pointer-to-function types, so the typedef name of a function pointer
    is normally lost; attributes declared on the typedef survive
    on the pointer or function type, and are included in the string."""
    if t.is_named_type:
        tn = cast("CTypNamed", t)
        return tn.name + " (" + str(tn.expand()) + ")"
    return str(t)


def _offset_type(
        cfun: "CFunction", t: Optional["CTyp"], off: "COffset"
) -> Optional["CTyp"]:
    """Type of the lvalue with base type t and offset off."""
    while off.has_offset():
        if off.is_field:
            foff = cast("CFieldOffset", off)
            cinfo = cfun.cfile.get_compinfo_by_ckey(foff.ckey)
            fields = [f for f in cinfo.fields if f.fname == foff.fieldname]
            if len(fields) != 1:
                return None
            t = fields[0].ftype
            off = foff.offset
        elif off.is_index:
            if t is None:
                return None
            te = t.expand()
            if not te.is_array:
                return None
            t = cast("CTypArray", te).array_basetype
            off = off.offset    # type: ignore
        else:
            return None
    return t


def _exp_type(cfun: "CFunction", e: "CExp") -> Optional["CTyp"]:
    """Type of a pointer-valued expression; None if not determined."""
    if e.is_caste:
        return cast("CExpCastE", e).typ
    if e.is_lval:
        lval = cast("CExpLval", e).lval
        return _lval_type(cfun, lval)
    return None


def _lval_type(cfun: "CFunction", lval: "CLval") -> Optional["CTyp"]:
    t: Optional["CTyp"] = None
    if lval.lhost.is_var:
        vid = cast("CLHostVar", lval.lhost).vid
        try:
            t = cfun.cfundecls.get_varinfo(vid).vtype
        except Exception:
            return None
    elif lval.lhost.is_mem:
        pt = _exp_type(cfun, cast("CLHostMem", lval.lhost).exp)
        if pt is None:
            return None
        pte = pt.expand()
        if not pte.is_pointer:
            return None
        t = cast("CTypPtr", pte).pointedto_type
    return _offset_type(cfun, t, lval.offset)


def callee_pointer_type(cfun: "CFunction", instr: "CCallInstr") -> str:
    """The function-pointer type through which an indirect call is made, as
    declared (a typedef name is kept: it is the carrier of a function-pointer
    contract."""
    e = instr.callee
    if e.is_lval:
        lval = cast("CExpLval", e).lval
        if lval.lhost.is_mem and lval.offset.is_no_offset:
            t = _exp_type(cfun, cast("CLHostMem", lval.lhost).exp)
            if t is not None:
                return _type_name(t)
        else:
            # call through a function-typed lvalue (not produced by CIL for
            # pointers, kept for completeness)
            t = _lval_type(cfun, lval)
            if t is not None:
                return _type_name(t)
    return "?"


def _is_direct(instr: "CCallInstr") -> Optional[str]:
    """Name of the callee of a direct call, None for an indirect call."""
    e = instr.callee
    if e.is_lval:
        lval = cast("CExpLval", e).lval
        if lval.lhost.is_var and lval.offset.is_no_offset:
            return cast("CLHostVar", lval.lhost).name
    return None


class SystemBoundary:

    def __init__(
            self,
            targetpath: str,
            capps: Dict[str, "CApplication"],
            level: str = "implementation-defined") -> None:
        self._targetpath = targetpath
        self._capps = capps
        self._level = level
        self._projects = list(capps.keys())
        self._reports: Dict[str, Dict[str, Any]] = {}
        self._defined: Dict[str, Dict[str, "CFunction"]] = {}
        self._declarations: Dict[str, Dict[str, "CVarInfo"]] = {}
        self._roots: Dict[str, str] = {}
        self.entries: Dict[str, Dict[str, Any]] = {}
        self.conflicts: Dict[str, List[str]] = {}
        self.indirect: List[Dict[str, Any]] = []
        self.addresstaken: List[Dict[str, Any]] = []
        self.gaps: List[Dict[str, Any]] = []
        self._collect()

    @property
    def projects(self) -> List[str]:
        return self._projects

    @property
    def targetpath(self) -> str:
        return self._targetpath

    def _relpath(self, path: str) -> str:
        if os.path.isabs(path):
            return os.path.relpath(path, self.targetpath)
        return path

    # ---------------------------------------------------------- collection --

    def _index(self) -> None:
        for p, capp in self._capps.items():
            self._roots[p] = _project_root(capp)
            self._reports[p] = VerificationReport(capp, self._level).to_dict()
            defined: Dict[str, "CFunction"] = {}
            decls: Dict[str, "CVarInfo"] = {}
            for cf in capp.cfiles:
                for fn in cf.get_functions():
                    if fn.svar.vstorage != "s":
                        defined[fn.name] = fn
                for g in cf.declarations.get_global_varinfos():
                    if g.vname not in decls and g.vdecl is not None:
                        decls[g.vname] = g
            self._defined[p] = defined
            self._declarations[p] = decls

    def _collect(self) -> None:
        self._index()
        for p in self.projects:
            self._collect_callees(p)
            self._collect_indirect(p)
            self._collect_address_taken(p)
        for e in self.entries.values():
            self._collect_provider_data(e)

    def _collect_callees(self, p: str) -> None:
        b = self._reports[p]["boundary"]
        ext = self._reports[p]["remedies"]["external-condition"]
        counts = dict((fn, n) for (fn, n) in ext["items"])
        conds: Dict[str, List[str]] = ext.get("conditions", {})
        callees: List[Tuple[str, int, str]] = [
            (u["function"], u["callsites"], "unmodeled")
            for u in b["unmodeled"]]
        # partially specified: effects or preconditions not
        # declared; complete specifications are not drafted
        partial = dict((r["function"], r) for r in b.get("partial", []))
        callees += [
            (r["function"], r["callsites"], "partially-specified")
            for r in partial.values()]
        for (fn, nsites, kind) in callees:
            vinfo = self._declarations[p].get(fn)
            header = ""
            line = 0
            if vinfo is not None and vinfo.vdecl is not None:
                header = self._relpath(vinfo.vdecl.file)
                line = vinfo.vdecl.line
            providers = [
                q for q in self.projects if q != p and fn in self._defined[q]]
            if len(providers) > 1:
                self.conflicts[fn] = providers
            root = self._relpath(self._roots[p])
            if (
                    not providers
                    and header != ""
                    and header.startswith(root + "/")):
                self.gaps.append(
                    {"client": p, "function": fn, "header": header})
                continue
            e = self.entries.setdefault(fn, {
                "function": fn,
                "header": header,
                "line": line,
                "params": _parameter_names(vinfo) if vinfo else [],
                "provider": providers[0] if len(providers) == 1 else None,
                "kind": kind,
                "specification": (
                    {"effects": partial[fn].get("effects"),
                     "preconditions": partial[fn].get("preconditions"),
                     "compiler-preconditions": partial[fn].get(
                         "compiler-preconditions")}
                    if fn in partial else None),
                "clients": {},
                "requests": {}})
            e["clients"][p] = e["clients"].get(p, 0) + nsites
            for c in conds.get(fn, []):
                r = e["requests"].setdefault(c, {})
                r[p] = r.get(p, 0) + counts.get(fn, 0)

    def _collect_indirect(self, p: str) -> None:
        for cf in self._capps[p].cfiles:
            for cfun in cf.get_functions():
                for ci in cfun.call_instrs:
                    if _is_direct(ci) is not None:
                        continue
                    self.indirect.append({
                        "client": p,
                        "file": self._relpath(cf.name + ".c"),
                        "function": cfun.name,
                        "line": ci.location.line,
                        "callee": str(ci.callee),
                        "pointer-type": callee_pointer_type(cfun, ci)})

    def _collect_address_taken(self, p: str) -> None:
        """Functions defined in p whose address is taken anywhere in p: they
        may be called through a pointer from another module."""
        names: Set[str] = set([])
        for cf in self._capps[p].cfiles:
            for g in cf.declarations.get_global_varinfos():
                if g.vaddrof and g.vtype.is_function:
                    names.add(g.vname)
        for cf in self._capps[p].cfiles:
            for fn in cf.get_functions():
                if fn.name in names:
                    self.addresstaken.append({
                        "project": p,
                        "function": fn.name,
                        "file": self._relpath(cf.name + ".c"),
                        "static": fn.svar.vstorage == "s"})

    def _collect_provider_data(self, e: Dict[str, Any]) -> None:
        e["assumptions"], e["guarantees"], e["defined-in"] = [], [], ""
        q = e["provider"]
        if q is None:
            return
        fn = self._defined[q][e["function"]]
        e["defined-in"] = self._relpath(fn.cfile.name + ".c")
        for a in fn.api.api_assumptions.values():
            e["assumptions"].append({
                "predicate": str(a.predicate),
                "global": a.isglobal,
                "ppos": len(a.ppos),
                "spos": len(a.spos)})
        for g in fn.api.postcondition_guarantees.values():
            e["guarantees"].append(str(g))

    # -------------------------------------------------------------- output --

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projects": dict(
                (p, {"root": self._relpath(self._roots[p])})
                for p in self.projects),
            "entries": self.entries,
            "conflicts": self.conflicts,
            "indirect": self.indirect,
            "address-taken": self.addresstaken,
            "gaps": self.gaps}

    def summary(self) -> str:
        lines = ["Boundary of " + ", ".join(
            "%s (%s)" % (p, self._relpath(self._roots[p]))
            for p in self.projects), ""]
        byprov: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for e in self.entries.values():
            prov = e["provider"]
            if prov is None:
                prov = (
                    "(conflict)" if e["function"] in self.conflicts
                    else "(not analyzed)")
            byprov.setdefault(prov, {}).setdefault(
                e["header"], []).append(e)

        # order = lambda p: (p.startswith("("), p)
        for prov in sorted(byprov, key=lambda p: (p.startswith("("), p)):
            hs = byprov[prov]
            nf = sum(len(v) for v in hs.values())
            lines.append(
                "Provider %s: %d functions in %d headers"
                % (prov, nf, len(hs)))
            lines.append("  %-48s %4s %5s %5s %5s %5s  %s" % (
                "header", "fns", "sites", "reqs", "assum", "guar", "clients"))
            for h in sorted(hs, key=lambda h: (-len(hs[h]), h)):
                es = hs[h]
                clients = sorted(set(c for e in es for c in e["clients"]))
                lines.append("  %-48s %4d %5d %5d %5d %5d  %s" % (
                    h, len(es),
                    sum(sum(e["clients"].values()) for e in es),
                    sum(1 for e in es if e["requests"]),
                    sum(len(e["assumptions"]) for e in es),
                    sum(len(e["guarantees"]) for e in es),
                    ", ".join(clients)))
            lines.append("")

        lines.append(
            "Defined by more than one module (C11 6.9p5; not drafted):")
        for fn in sorted(self.conflicts):
            lines.append("  %-36s %s" % (fn, ", ".join(self.conflicts[fn])))
        if not self.conflicts:
            lines.append("  none")
        lines.append("")

        lines.append(
            "Indirect calls (callee unknown; contract on the pointer type"
            + " needed:")
        bytype: Dict[Tuple[str, str], int] = {}
        for r in self.indirect:
            k = (r["client"], r["pointer-type"])
            bytype[k] = bytype.get(k, 0) + 1
        for (client, ptype) in sorted(bytype, key=lambda k: (k[0], -bytype[k])):
            lines.append(
                "  %-14s %4d  %s" % (client, bytype[(client, ptype)], ptype))
        if not self.indirect:
            lines.append("  none")
        lines.append("")

        lines.append(
            "Address-taken functions (may be called through a pointer by"
            + " another module:")
        byproj: Dict[str, int] = {}
        for r in self.addresstaken:
            byproj[r["project"]] = byproj.get(r["project"], 0) + 1
        for proj in sorted(byproj):
            lines.append("  %-14s %4d" % (proj, byproj[proj]))
        if not self.addresstaken:
            lines.append("  none")
        lines.append("")

        lines.append(
            "Not a boundary (declared in the calling module, defined"
            + " nowhere):")
        for g in self.gaps:
            lines.append(
                "  %-14s %-36s %s" % (g["client"], g["function"], g["header"]))
        if not self.gaps:
            lines.append("  none")
        return "\n".join(lines)

    # ---------------------------------------------------- draft companions --

    def _prototype_text(self, header: str, line: int, name: str) -> str:
        """The declaration as written in the header, without trailing
        attribute macros (e.g. OS_PRINTF), which are not visible to a
        companion."""
        path = os.path.join(self.targetpath, header)
        if not os.path.isfile(path) or line <= 0:
            return "/* declaration of " + name + " not found */"
        with open(path, errors="replace") as fp:
            lines = fp.readlines()
        text = ""
        for ln in lines[line - 1:]:
            text += ln
            if ";" in ln:
                break
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        i = text.find(name)
        j = text.find("(", i)
        depth = 0
        for k in range(j, len(text)):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    return " ".join(text[:k + 1].split())
        return " ".join(text.split(";")[0].split())

    @staticmethod
    def _assumption_attribute(pred: str, params: List[str]) -> Optional[str]:
        m = re.match(r"^not-null\((\w+)\)$", pred)
        if m is not None and m.group(1) in params:
            return "__chkc_nonnull__(%d)" % (params.index(m.group(1)) + 1)
        return None

    def draft_entry(self, e: Dict[str, Any]) -> List[str]:
        fn = e["function"]
        attrs: List[str] = []
        notes: List[str] = []
        clients = ", ".join(
            "%s (%d call site%s)" % (c, n, "" if n == 1 else "s")
            for c, n in sorted(e["clients"].items()))
        notes.append(
            "%s  [defined in %s: %s]" % (fn, e["provider"], e["defined-in"]))
        notes.append("  called by: " + clients)
        spec = e.get("specification")
        if e["kind"] == "partially-specified" and spec is not None:
            pre = spec["preconditions"] or "not declared"
            if spec["preconditions"] is None and spec.get(
                    "compiler-preconditions"):
                pre += (
                    " (header attributes " + spec["compiler-preconditions"]
                    + " do not count)")
            notes.append(
                "  partially specified by the declaration: effects: "
                + (spec["effects"] or "not declared")
                + "; preconditions: " + pre)
        effects = spec is not None and spec["effects"] is not None
        for c, perclient in sorted(e["requests"].items()):
            text = external_condition_text.get(c, (c, ""))[0]
            attr = CONDITION_ATTRIBUTE.get(c)
            who = ", ".join(
                "%s: %d POs" % (k, v) for k, v in sorted(perclient.items()))
            if c in e["guarantees"]:
                status = "proven by the provider"
            elif c in EFFECT_CONDITIONS:
                status = "side effect: not checked yet"
            else:
                status = (
                    "NOT proven by the provider's run 0: check before"
                    + " accepting")
            notes.append("  requested: %s (%s)%s" % (
                text, who,
                ("  -> " + attr) if attr else "  (no attribute syntax yet)"))
            notes.append("    [%s]" % status)
            if attr:
                attrs.append(attr)
            effects = effects or c in EFFECT_CONDITIONS
        preconditions = spec is not None and spec["preconditions"] is not None
        if e["assumptions"]:
            notes.append("  provider api assumptions (preconditions it needs):")
            for a in e["assumptions"]:
                attr = (
                    None if a["global"]
                    else self._assumption_attribute(
                        a["predicate"], e["params"]))
                notes.append("    %s%s%s" % (
                    a["predicate"], " [global]" if a["global"] else "",
                    ("  -> " + attr) if attr
                    else "  (no attribute syntax yet)"))
                if attr:
                    attrs.append(attr)
        elif not preconditions:
            notes.append(
                "  provider api assumptions: none; if none are needed,"
                + " declare __chkc_requires_none__")
        if e["guarantees"]:
            notes.append(
                "  provider postcondition guarantees (proven in its run 0):")
            for g in e["guarantees"]:
                attr = CONDITION_ATTRIBUTE.get(g)
                notes.append("    %s%s" % (g, ("  -> " + attr) if attr else ""))
                if attr and attr not in attrs:
                    attrs.append(attr)
        if not effects:
            notes.append(
                "  effects: not declared -- add an effects clause"
                + " (or __chkc_effects_unknown__")
        # the function belongs to the external unit of its provider: in the
        # provider its postconditions are checked by primary proof
        # obligations at the return sites
        attrs.insert(0, "__chkc_exported__")
        notes.append(
            "  __chkc_exported__: in %s the postconditions are guarantees,"
            " checked by primary proof obligations" % e["provider"])
        proto = self._prototype_text(e["header"], e["line"], fn)
        lines = (
            ["/* " + notes[0]] + [" * " + n for n in notes[1:]] + [" */"])
        if attrs:
            # (always non-empty: __chkc_exported__)
            lines.append(proto)
            for i, a in enumerate(attrs):
                lines.append(
                    "  __attribute__((%s))%s"
                    % (a, ";" if i == len(attrs) - 1 else ""))
        else:
            lines.append(proto + ";")
        return lines

    def draft_companions(self) -> Dict[Tuple[str, str], List[str]]:
        """Draft companion text per (provider, header)."""
        byheader: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for e in self.entries.values():
            if e["provider"] is None:
                continue
            byheader.setdefault((e["provider"], e["header"]), []).append(e)
        result: Dict[Tuple[str, str], List[str]] = {}
        for (provider, header), es in sorted(byheader.items()):
            out = [
                "/* Draft companion of %s (external unit of %s)."
                % (header, provider),
                "   Generated by chkc c-system collect-boundary from cold"
                + " runs;",
                "   review every entry: requests are sufficient, not"
                + " necessary.",
                "   Only functions called by other analyzed modules are"
                + " listed. */",
                ""]
            body: List[str] = []
            for e in sorted(es, key=lambda e: e["line"]):
                body.extend(self.draft_entry(e))
                body.append("")
            # a companion is preprocessed on its own: it does not see the
            # macros of the headers it annotates; system headers may be
            # included
            if re.search(r"\bbool\b", "\n".join(body)):
                out.extend(["#include <stdbool.h>", ""])
            out.extend(body)
            result[(provider, header)] = out
        return result

    def write(self, outdir: str) -> List[str]:
        """Write draft companions (<outdir>/<provider>/<header path>, with
        .h replaced by .chk.h, mirroring the source tree as the contract
        path does), summary.txt and boundary.json. Returns the files
        written."""
        written: List[str] = []
        for (provider, header), text in self.draft_companions().items():
            base, _ = os.path.splitext(header)
            path = os.path.join(outdir, provider, base + ".chk.h")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fp:
                fp.write("\n".join(text))
            written.append(path)
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, "summary.txt")
        with open(path, "w") as fp:
            fp.write(self.summary() + "\n")
        written.append(path)
        path = os.path.join(outdir, "boundary.json")
        with open(path, "w") as fp:
            json.dump(self.to_dict(), fp, indent=2, default=str)
        written.append(path)
        return written
