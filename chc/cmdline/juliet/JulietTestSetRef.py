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

from typing import Any, cast, Dict, List, Optional, TYPE_CHECKING

from chc.cmdline.juliet.JulietTestFileRef import JulietSafeControl
from chc.cmdline.juliet.JulietTestFileRef import JulietViolation
from chc.cmdline.juliet.JulietTestRef import JulietTestRef


class JulietTestSetMacros:
    """Macro definitions of proof obligations."""

    def __init__(self, d: Dict[str, Any]) -> None:
        self._d = d
        self._po_macros: Optional[Dict[str, Any]] = None
        self._ps_macros: Optional[Dict[str, List[str]]] = None

    @property
    def po_macros(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dictionary of proof obligation definitions."""

        if self._po_macros is None:
            self._po_macros = {}
            for key in self._d:
                if key.startswith("PPO"):
                    self._po_macros[key] = self._d[key]
        return self._po_macros

    @property
    def ps_macros(self) -> Dict[str, List[str]]:
        """Returns a dictionary of lists of macro definitions."""

        if self._ps_macros is None:
            self._ps_macros = {}
            for key in self._d:
                if key.startswith("PS"):
                    self._ps_macros[key] = self._d[key]
        return self._ps_macros

    @property
    def predicates(self) -> List[str]:
        result: List[str] = []
        for po in self.po_macros.values():
            if "P" in po:
                result.append(po["P"])
        return result

    def expand_macro(self, m: str) -> List[Dict[str, Any]]:
        """Returns a list of proof obligation definitions."""

        if m in self.po_macros:
            return [self.po_macros[m]]

        if m in self.ps_macros:
            result: List[Dict[str, Any]] = []
            for p in self.ps_macros[m]:
                result.extend(self.expand_macro(p))
            return result

        return []


class JulietTestSetRef(object):
    """Reference proof obligation results for a juliet test set."""

    def __init__(self, d: Dict[str, Any]) -> None:
        self._d = d
        self._tests: Optional[Dict[str, JulietTestRef]] = None  # testindex
        self._macros: Optional[JulietTestSetMacros] = None

    @property
    def macros(self) -> JulietTestSetMacros:
        if self._macros is None:
            self._macros = JulietTestSetMacros(self._d.get("macros", {}))
        return self._macros

    def expand_macro(self, m: str) -> List[Dict[str, Any]]:
        return self.macros.expand_macro(m)

    '''
        if m.startswith("PPO"):
            if m in self.macros:
                return self.macros[m]
            else:
                return m
        if m.startswith("PS"):
            if m in self.macros:
                lst = self.macros[m]
                return [self.expand(x) for x in lst]
            else:
                return m
        return m
    '''

    @property
    def predicates(self) -> List[str]:
        return self.macros.predicates

    '''
    def get_predicates(self):
        result = []
        for p in self.macros:
            if p.startswith("PPO"):
                result.append(self.macros[p]["P"])
        return result
    '''

    @property
    def tests(self) -> Dict[str, JulietTestRef]:
        if self._tests is None:
            self._tests = {}
            for test in self._d["tests"]:
                self._tests[test] = JulietTestRef(self, test, self._d[test])
        return self._tests

    '''
    def get_tests(self):
        return self.tests.items()
    '''

    def get_predicate_violations(self) -> Dict[str, int]:
        result: Dict[str, int] = {}
        # violations = self.get_violations()
        for v in self.get_violations():
            p = v.predicate
            result.setdefault(p, 0)
            result[p] += 1
        return result

    def get_predicate_safe_controls(self) -> Dict[str, int]:
        result: Dict[str, int] = {}
        # safecontrols = self.get_safe_controls()
        for s in self.get_safe_controls():
            p = s.predicate
            result.setdefault(p, 0)
            result[p] += 1
        return result

    def get_violations(self) -> List[JulietViolation]:
        result: List[JulietViolation] = []
        for testref in self.tests.values():
            result.extend(testref.get_violations())
        return result
    '''
        def f(i, test):
            result.extend(test.get_violations())

        self.iter(f)
        return result
    '''

    def get_safe_controls(self) -> List[JulietSafeControl]:
        result: List[JulietSafeControl] = []
        for testref in self.tests.values():
            result.extend(testref.get_safe_controls())
        return result

    '''
        def f(i, test):
            result.extend(test.get_safe_controls())

        self.iter(f)
        return result
    '''

    '''
    def iter(self, f):
        for (t, test) in self.get_tests():
            f(t, test)
    '''

    def __str__(self) -> str:
        lines: List[str] = []
        for test in sorted(self.tests):
            lines.append("\nTest " + test)
            lines.append(str(self.tests[test]))
        return "\n".join(lines)

    '''
    def _initialize(self):
        for m in self.d["macros"]:
            self.macros[m] = self.d["macros"][m]
        for test in self.d["tests"]:
            self.tests[test] = JulietTestRef(self, test, self.d["tests"][test])
    '''
