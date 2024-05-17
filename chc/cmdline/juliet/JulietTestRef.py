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

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from chc.cmdline.juliet.JulietTestFileRef import JulietSafeControl
from chc.cmdline.juliet.JulietTestFileRef import JulietTestFileRef
from chc.cmdline.juliet.JulietTestFileRef import JulietViolation


if TYPE_CHECKING:
    from chc.cmdline.juliet.JulietTestSetRef import JulietTestSetRef


class JulietTestRef:
    def __init__(
            self,
            testsetref: "JulietTestSetRef",
            test: str,
            d: Dict[str, Any]) -> None:
        self._testsetref = testsetref
        self._test = test
        self._d = d
        self._cfiles: Optional[Dict[str, JulietTestFileRef]] = None  # filename

    @property
    def testsetref(self) -> "JulietTestSetRef":
        return self._testsetref

    @property
    def test(self) -> str:
        return self._test

    @property
    def cfiles(self) -> Dict[str, JulietTestFileRef]:
        if self._cfiles is None:
            self._cfiles = {}
            for f in self._d["cfiles"]:
                self._cfiles[f] = JulietTestFileRef(
                    self, self.test, self._d["cfiles"][f])
        return self._cfiles

    def iter(self, f: Callable[[str, JulietTestFileRef], None]) -> None:
        for (filename, fileref) in self.cfiles.items():
            f(filename, fileref)

    def expand_macro(self, m: str) -> List[Dict[str, Any]]:
        return self.testsetref.expand_macro(m)

    def get_violations(self) -> List[JulietViolation]:
        result: List[JulietViolation] = []
        for f in self.cfiles.values():
            result.extend(f.get_violations())
        return result

    def get_safe_controls(self) -> List[JulietSafeControl]:
        result: List[JulietSafeControl] = []
        for f in self.cfiles.values():
            result.extend(f.get_safe_controls())
        return result

    def __str__(self) -> str:
        lines: List[str] = []
        for f in self.cfiles:
            lines.append(f)
            lines.append(str(self.cfiles[f]))
        return "\n".join(lines)
