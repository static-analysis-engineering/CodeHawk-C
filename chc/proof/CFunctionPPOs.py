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
"""The collection of all primary proof obligations in a function."""

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from chc.proof.CFunctionPPO import CFunctionPPO
from chc.proof.CProofDependencies import CProofDependencies
from chc.proof.CProofDiagnostic import CProofDiagnostic

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionProofs import CFunctionProofs
    from chc.proof.CFunPODictionary import CFunPODictionary


po_status = {"g": "safe", "o": "open", "r": "violation", "x": "dead-code"}


class CFunctionPPOs:
    """Represents the set of primary proof obligations for a function.

    xnode received is the content of the <"ppos"> element
    """

    def __init__(self, cproofs: "CFunctionProofs", xnode: ET.Element) -> None:
        self.xnode = xnode
        self._cproofs = cproofs
        self._ppos: Optional[Dict[int, CFunctionPPO]] = None  # ppoid -> CFunctionPPO
        # self._initialize()

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def cfun(self) -> "CFunction":
        return self.cproofs.cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def ppos(self) -> Dict[int, CFunctionPPO]:
        if self._ppos is None:
            self._ppos = {}
            for xp in self.xnode.findall("ppo"):
                ppotype = self.podictionary.read_xml_ppo_type(xp)
                id = ppotype.index
                status = po_status[xp.get("s", "o")]
                deps = CProofDependencies(self.cproofs, xp)
                diagnostic = CProofDiagnostic(xp.find("d"))

                # get explanation
                enode = xp.find("e")
                if enode is not None:
                    expl: Optional[str] = enode.get("txt", "")
                else:
                    expl = None

                self._ppos[id] = CFunctionPPO(
                    self.cproofs, ppotype, status, deps, expl, diagnostic)
        return self._ppos

    def get_ppo(self, id: int) -> CFunctionPPO:
        if id in self.ppos:
            return self.ppos[id]
        else:
            raise UF.CHCError("Ppo with id " + str(id) + " not found")

    def iter(self, f: Callable[[CFunctionPPO], None]) -> None:
        for ppo in sorted(
            self.ppos,
            key=lambda p: (self.ppos[p].location.line, int(self.ppos[p].po_index)),
        ):
            f(self.ppos[ppo])

    def __str__(self) -> str:
        lines: List[str] = []
        for ppo in self.ppos.values():
            lines.append(str(ppo))
        return "\n".join(lines)
'''
    def _initialize(self):
        for p in self.xnode.find("ppos").findall("ppo"):
            ppotype = self.cfun.podictionary.read_xml_ppo_type(p)
            id = ppotype.index
            deps = None
            status = po_status[p.get("s", "o")]
            if "deps" in p.attrib:
                level = p.get("deps")
                if level == "a":
                    ids = p.get("ids")
                    if len(ids) > 0:
                        ids = [int(x) for x in p.get("ids").split(",")]
                    else:
                        ids = []
                    invs = p.get("invs")
                    if len(invs) > 0:
                        invs = [int(x) for x in invs.split(",")]
                    else:
                        invs = []
                    deps = CProofDependencies(self, level, ids, invs)
                else:
                    deps = CProofDependencies(self, level)
            expl = None
            enode = p.find("e")
            if enode is not None:
                expl = enode.get("txt")
            diag = None
            dnode = p.find("d")
            if dnode is not None:
                pinvs = {}
                amsgs = {}
                kmsgs = {}
                for n in dnode.find("invs").findall("arg"):
                    pinvs[int(n.get("a"))] = [int(x) for x in n.get("i").split(",")]
                pmsgs = [x.get("t") for x in dnode.find("msgs").findall("msg")]
                for n in dnode.find("amsgs").findall("arg"):
                    arg = int(n.get("a"))
                    msgs = [x.get("t") for x in n.findall("msg")]
                    amsgs[arg] = msgs
                knode = dnode.find("kmsgs")
                if knode is not None:
                    for n in knode.findall("key"):
                        key = n.get("k")
                        msgs = [x.get("t") for x in n.findall("msg")]
                        kmsgs[key] = msgs
                diag = CProofDiagnostic(pinvs, pmsgs, amsgs, kmsgs)
            self.ppos[id] = CFunctionPPO(self, ppotype, status, deps, expl, diag)
'''
