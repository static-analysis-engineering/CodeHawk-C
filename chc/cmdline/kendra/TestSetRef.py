# ------------------------------------------------------------------------------
# C Source Code Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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

import json

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from chc.cmdline.kendra.TestCFileRef import TestCFileRef


class TestSetRef:
    """Provides access to the reference results of a set of C files."""

    def __init__(self, specfilename: str) -> None:
        self._specfilename = specfilename
        self._cfiles: Dict[str, TestCFileRef] = {}
        self._refd: Dict[str, Any] = {}

    @property
    def specfilename(self) -> str:
        return self._specfilename

    @property
    def refd(self) -> Dict[str, Any]:
        if len(self._refd) == 0:
            with open(self.specfilename) as fp:
                self._refd = json.load(fp)
        return self._refd

    @property
    def cfiles(self) -> Dict[str, TestCFileRef]:
        if len(self._cfiles) == 0:
            for (f, fdata) in self.refd["cfiles"].items():
                self._cfiles[f] = TestCFileRef(self, f, fdata)
        return self._cfiles

    '''
    def iter(self, f):
        for cfile in self.cfiles.values():
            f(cfile)
    '''

    @property
    def cfilenames(self) -> List[str]:
        return sorted(self.cfiles.keys())

    '''
    def get_cfiles(self):
        return sorted(self.cfiles.values(), key=lambda f: f.name)
    '''

    def cfile(self, cfilename: str) -> Optional[TestCFileRef]:
        if cfilename in self.cfiles:
            return self.cfiles[cfilename]
        else:
            return None

    def set_ppos(
            self, cfilename: str, cfun: str, ppos: List[Dict[str, str]]
    ) -> None:
        self._refd["cfiles"][cfilename]["functions"][cfun]["ppos"] = ppos

    def set_spos(self, cfilename: str, cfun: str, spos: List[Dict[str, str]]
    ) -> None:
        self._refd["cfiles"][cfilename]["functions"][cfun]["spos"] = spos

    def has_characteristics(self) -> bool:
        return "characteristics" in self.refd

    @property
    def characteristics(self) -> List[str]:
        if "characteristics" in self.refd:
            return self.refd["characteristics"]
        else:
            return []

    def has_restrictions(self) -> bool:
        return "restrictions" in self.refd

    @property
    def restrictions(self) -> List[str]:
        if "restrictions" in self.refd:
            return self.refd["restrictions"]
        else:
            return []

    @property
    def is_linux_only(self) -> bool:
        return "linux-only" in self.restrictions

    def save(self) -> None:
        with open(self.specfilename, "w") as fp:
            fp.write(json.dumps(self._refd, indent=4, sort_keys=True))

    def __str__(self) -> str:
        lines: List[str] = []
        for cfile in self.cfiles.values():
            lines.append(cfile.name)
            for cfun in sorted(cfile.functions.values(), key=lambda f:f.name):
                lines.append("  " + cfun.name)
                if cfun.has_ppos():
                    for ppo in sorted(cfun.ppos, key=lambda p: p.line):
                        hasmultiple = cfun.has_multiple(
                            ppo.line, ppo.predicate
                        )
                        ctxt = ppo.context_string if hasmultiple else ""
                        status = ppo.status.ljust(12)
                        if ppo.status == ppo.tgt_status:
                            tgtstatus = ""
                        else:
                            tgtstatus = "(" + ppo.tgt_status + ")"
                        lines.append(
                            "    "
                            + str(ppo.line).rjust(4)
                            + "  "
                            + ppo.predicate.ljust(24)
                            + " "
                            + status
                            + " "
                            + ctxt.ljust(40)
                            + tgtstatus
                        )
        return "\n".join(lines)

    '''
    def _initialize(self):
        for f in self.r["cfiles"]:
            self.cfiles[f] = TestCFileRef(self, f, self.r["cfiles"][f])
    '''
