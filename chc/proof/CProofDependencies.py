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
"""Dependencies of proof on assumptions and invariants."""

import xml.etree.ElementTree as ET

from typing import cast, Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.proof.CFunctionProofs import CFunctionProofs

class CProofDependencies:
    """Extent of dependency of a closed proof obligation.

    levels:
       
    - 's': dependent on statement itself only
    - 'f': dependent on function context
    - 'r': reduced to local spo in function context
    - 'a': dependent on other functions in the application
    - 'x': dead code

    ids: list of api assumption id's on which the proof is dependent

    invs: list of invariants indices used to establish dependencies or validity

    """

    def __init__(
            self, cproofs: "CFunctionProofs", xnode: ET.Element) -> None:
        self.xnode = xnode
        self._cproofs = cproofs
        self._level: Optional[str] = None
        self._ids: Optional[List[int]] = None
        self._invs: Optional[List[int]] = None

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def level(self) -> str:
        if self._level is None:
            self._level = self.xnode.get("deps", "s")
            if self._level is None:
                raise UF.CHCError("Mypy omission")
        return self._level

    @property
    def ids(self) -> List[int]:
        if self._ids is None:
            self._ids = []
            xids = self.xnode.get("ids", "")
            if len(xids) > 0:
                self._ids = [int(x) for x in xids.split(",")]
        return self._ids

    @property
    def invs(self) -> List[int]:
        if self._invs is None:
            self._invs = []
            xinvs = self.xnode.get("invs", "")
            if len(xinvs) > 0:
                self._invs = [int(x) for x in xinvs.split(",")]
        return self._invs

    @property
    def is_stmt(self) -> bool:
        return self.level == "s"

    @property
    def is_local(self) -> bool:
        return self.level == "s" or self.level == "f" or self.level == "r"

    def has_external_dependencies(self) -> bool:
        return self.level == "a"

    @property
    def is_deadcode(self) -> bool:
        return self.level == "x"

    def write_xml(self, cnode: ET.Element) -> None:
        cnode.set("deps", self.level)
        if len(self.ids) > 0:
            cnode.set("ids", ",".join([str(i) for i in self.ids]))
        if len(self.invs) > 0:
            cnode.set("invs", ",".join([str(i) for i in self.invs]))

    def __str__(self) -> str:
        return self.level
