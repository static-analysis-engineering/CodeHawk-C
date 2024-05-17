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
"""Juliet scoring reference for a juliet test set file."""

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from chc.cmdline.juliet.JulietTestRef import JulietTestRef
    from chc.proof.CFunctionPO import CFunctionPO


class JulietTestFileRef:

    def __init__(
            self,
            testref: "JulietTestRef",
            test: str,
            d: Dict[str, Dict[str, List[str]]]) -> None:
        self._testref = testref
        self._test = test
        self._d = d
        self._violations: Optional[Dict[int, List[JulietViolation]]] = None
        self._safecontrols: Optional[Dict[int, List[JulietSafeControl]]] = None

    @property
    def testref(self) -> "JulietTestRef":
        return self._testref

    @property
    def test(self) -> str:
        return self._test

    @property
    def violations(self) -> Dict[int, List["JulietViolation"]]:
        if self._violations is None:
            self._violations = {}
            for line in self._d["violations"]:
                self._violations[int(line)] = []
                for v in self._d["violations"][line]:
                    ppovs = self.expand(v)
                    for ppov in ppovs:
                        self._violations[int(line)].append(
                            JulietViolation(self, self.test, int(line), ppov))
        return self._violations

    @property
    def safe_controls(self) -> Dict[int, List["JulietSafeControl"]]:
        if self._safecontrols is None:
            self._safecontrols = {}
            for line in self._d["safe-controls"]:
                self._safecontrols[int(line)] = []
                for s in self._d["safe-controls"][line]:
                    ppovs = self.expand(s)
                    for ppov in ppovs:
                        self._safecontrols[int(line)].append(
                            JulietSafeControl(self, self.test, int(line), ppov))
        return self._safecontrols

    def expand(self, m: str) -> List[Dict[str, Any]]:
        return self.testref.expand_macro(m)

    def get_violations(self) -> List["JulietViolation"]:
        result: List[JulietViolation] = []
        for (line, v) in sorted(self.violations.items()):
            result.extend(v)
        return result

    def iter_violations(
            self, f: Callable[[int, "JulietPpo"], None]) -> None:
        for (line, ppos) in self.violations.items():
            for ppo in ppos:
                f(line, ppo)

    def get_safe_controls(self) -> List["JulietSafeControl"]:
        result: List[JulietSafeControl] = []
        for (line, s) in sorted(self.safe_controls.items()):
            result.extend(s)
        return result

    def iter_safe_controls(
            self, f: Callable[[int, "JulietPpo"], None]) -> None:
        for (line, ppos) in self.safe_controls.items():
            for ppo in ppos:
                f(line, ppo)

    def iter(self, f: Callable[[int, "JulietPpo"], None]) -> None:
        self.iter_violations(f)
        self.iter_safe_controls(f)

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("  violations:")
        for line in self.violations:
            lines.append("    line " + str(line))
            for v in self.violations[line]:
                lines.append("      " + str(v))
        lines.append("")
        lines.append("  safe-controls:")
        for line in self.safe_controls:
            lines.append("    line " + str(line))
            for s in self.safe_controls[line]:
                lines.append("      " + str(s))
        return "\n".join(lines)


class JulietPpo:
    """Primary proof obligation."""

    def __init__(
            self,
            testfileref: JulietTestFileRef,
            test: str,
            line: int,
            d: Dict[str, Any]) -> None:
        self._testfileref = testfileref
        self._test = test
        self._line = line
        self._d = d

    @property
    def testfileref(self) -> JulietTestFileRef:
        return self._testfileref

    @property
    def test(self) -> str:
        return self._test

    @property
    def line(self) -> int:
        return self._line

    @property
    def is_violation(self) -> bool:
        return False

    @property
    def is_safe_control(self) -> bool:
        return False

    @property
    def predicate(self) -> str:
        return self._d["P"]

    def has_pred_arg(self) -> bool:
        return "A" in self._d

    @property
    def predarg(self) -> List[str]:
        return self._d.get("A", [])

    def has_exp_ctxt(self) -> bool:
        return "E" in self._d

    @property
    def expctxt(self) -> str:
        return self._d["E"]

    def has_cfg_ctxt(self) -> bool:
        return "C" in self._d

    def has_variable_names(self) -> bool:
        return "V" in self._d

    @property
    def variable_names(self) -> List[str]:
        return self._d.get("V", [])

    def has_variable_names_plus(self) -> bool:
        return "VP" in self._d

    @property
    def variable_names_plus(self) -> List[str]:
        return self._d.get("VP", [])

    def has_variable_deref(self) -> bool:
        return "D" in self._d

    @property
    def variable_derefs(self) -> List[str]:
        return self._d.get("D", [])

    def has_target_type(self) -> bool:
        return "T" in self._d

    @property
    def targettype(self) -> str:
        return self._d["T"]

    def has_reference_type(self) -> bool:
        return "R" in self._d

    @property
    def reference_type(self) -> str:
        return self._d["R"]

    def matches_pred_arg(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_pred_arg()) or any(
            [ppo.has_argument_name(vname) for vname in self.predarg]
        )

    def matches_exp_ctxt(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_exp_ctxt()) or str(
            ppo.context.exp_context
        ) == self.expctxt

    def matches_variable_names(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_variable_names()) or any(
            [ppo.has_variable_name(vname) for vname in self.variable_names]
        )

    def matches_variable_names_plus(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_variable_names_plus()) or any(
            [ppo.has_variable_name_op(vname, "+")
             for vname in self.variable_names_plus]
        )

    def matches_variable_deref(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_variable_deref()) or any(
            [ppo.has_variable_name_deref(vname)
             for vname in self.variable_derefs]
        )

    def matches_target_type(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_target_type()) or str(ppo.predicate.tgtkind
        ) == self.targettype

    def matches_reference_type(self, ppo: "CFunctionPO") -> bool:
        return (not self.has_reference_type()) or (
            self.reference_type == "mem" and ppo.predicate.has_ref_type()
        )

    def __str__(self) -> str:
        ctxt = ""
        if self.has_exp_ctxt():
            ctxt = " (" + self.expctxt + ")"
        return str(self.line) + "  " + self.predicate + ctxt


class JulietViolation(JulietPpo):

    def __init__(
            self,
            testfileref: JulietTestFileRef,
            test: str,
            line: int,
            d: Dict[str, Any]) -> None:
        JulietPpo.__init__(self, testfileref, test, line, d)

    @property
    def is_violation(self) -> bool:
        return True


class JulietSafeControl(JulietPpo):

    def __init__(
            self,
            testfileref: JulietTestFileRef,
            test: str,
            line: int,
            d: Dict[str, Any]) -> None:
        JulietPpo.__init__(self, testfileref, test, line, d)

    @property
    def is_violation(self) -> bool:
        return False
