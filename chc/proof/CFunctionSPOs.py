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
"""Container for all supporting proof obligations in a function."""

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from chc.proof.CFunctionCallsiteSPO import CFunctionCallsiteSPO
from chc.proof.CFunctionCallsiteSPOs import CFunctionCallsiteSPOs
from chc.proof.CFunctionReturnsiteSPOs import CFunctionReturnsiteSPOs
from chc.proof.CFunctionLocalSPO import CFunctionLocalSPO

from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPO import po_status
from chc.proof.CProofDependencies import CProofDependencies
from chc.proof.CProofDiagnostic import CProofDiagnostic, SituatedMsg

from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionProofs import CFunctionProofs
    from chc.proof.CFunPODictionary import CFunPODictionary


class CFunctionSPOs:
    """Represents the set of supporting proof obligations for a function.

    xnode received is the content of the <"spos"> element.
    """

    def __init__(self, cproofs: "CFunctionProofs", xnode: ET.Element) -> None:
        self.xnode = xnode
        self._cproofs = cproofs
        self.spocounter = 0
        self._localspos: Optional[Dict[int, CFunctionLocalSPO]] = None

        # cfg-contextstring -> CFunctionCallsiteSPOs
        self._callsitespos: Optional[Dict[str, CFunctionCallsiteSPOs]] = None

        # cfg-contextstring -> CFunctionReturnsiteSPOs
        self._returnsitespos: Optional[Dict[str, CFunctionReturnsiteSPOs]] = None

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def cfun(self) -> "CFunction":
        return self.cproofs.cfun

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cfun.podictionary

    @property
    def spos(self) -> List[CFunctionPO]:
        result: List[CFunctionPO] = []
        result.extend(list(self.local_spos.values()))
        for cspos in self.callsite_spos.values():
            for spos in cspos.spos.values():
                result.extend(spos)

        for rspos in self.returnsite_spos.values():
            for sposr in rspos.spos.values():
                result.extend(sposr)

        return result

    @property
    def local_spos(self) -> Dict[int, CFunctionLocalSPO]:
        if self._localspos is None:
            self._localspos = {}
            xlspos = self.xnode.find("localspos")
            if xlspos is not None:
                for xpo in xlspos.findall("po"):
                    spotype = self.podictionary.read_xml_spo_type(xpo)
                    xexpl = xpo.find("e")
                    expl = (
                        None if xexpl is None
                        else SituatedMsg(self.cfun.cdictionary, xexpl))
                    deps = CProofDependencies(self.cproofs, xpo)
                    diagnostic = CProofDiagnostic(self.cproofs, xpo.find("d"))
                    status = po_status[xpo.get("s", "o")]
                    self._localspos[spotype.po_index] = CFunctionLocalSPO(
                        self.cproofs, spotype, status, deps, expl, diagnostic)
        return self._localspos

    @property
    def callsite_spos(self) -> Dict[str, CFunctionCallsiteSPOs]:
        if self._callsitespos is None:
            self._callsitespos = {}
            xcss = self.xnode.find("callsites")
            if xcss is not None:
                xdcss = xcss.find("direct-calls")
                if xdcss is not None:
                    for cs in xdcss.findall("dc"):
                        cspo = CFunctionCallsiteSPOs(self.cproofs, cs)
                        cfgctxt = str(cspo.cfgcontext)
                        self._callsitespos[cfgctxt] = cspo
                xicss = xcss.find("indirect-calls")
                if xicss is not None:
                    for cs in xicss.findall("ic"):
                        cspo = CFunctionCallsiteSPOs(self.cproofs, cs)
                        cfgcontext = str(cspo.cfgcontext)
                        self._callsitespos[cfgcontext] = cspo
        return self._callsitespos

    @property
    def returnsite_spos(self) -> Dict[str, CFunctionReturnsiteSPOs]:
        if self._returnsitespos is None:
            self._returnsitespos = {}
            xrss = self.xnode.find("returnsites")
            if xrss is not None:
                for rs in xrss.findall("rs"):
                    rsspos = CFunctionReturnsiteSPOs(self.cproofs, rs)
                    cfgctxt = str(rsspos.cfgcontext)
                    self._returnsitespos[cfgctxt] = rsspos
        return self._returnsitespos

    def update(self) -> None:
        for cs in self.callsite_spos.values():
            cs.update()

    def collect_post_assumes(self) -> None:
        """for all call sites collect postconditions from callee's contracts
        and add as assume."""

        for cs in self.callsite_spos.values():
            cs.collect_post_assumes()

    def distribute_post_guarantees(self) -> None:
        for cs in self.callsite_spos.values():
            cs.distribute_post_guarantees()

    def get_spo(self, id: int) -> CFunctionPO:
        for localspo in self.local_spos.values():
            if localspo.po_index == id:
                return localspo
        for cs in self.callsite_spos.values():
            if cs.has_spo(id):
                return cs.get_spo(id)
        for rs in self.returnsite_spos.values():
            if rs.has_spo(id):
                return rs.get_spo(id)
        else:
            print(
                "No spo found with id "
                + str(id)
                + " in function "
                + self.cproofs.cfun.name
            )
            exit(1)

    def iter_callsites(self, f: Callable[[CFunctionCallsiteSPOs], None]) -> None:
        for cs in sorted(self.callsite_spos.values(), key=lambda p: (p.line)):
            f(cs)

    def iter(self, f: Callable[[CFunctionPO], None]) -> None:
        for localspo in self.local_spos.values():
            f(localspo)
        for cs in sorted(self.callsite_spos.values(), key=lambda p: (p.line)):
            cs.iter(f)
        for rs in self.returnsite_spos.values():
            rs.iter(f)

    def write_xml(self, cnode: ET.Element) -> None:
        snode = ET.Element("spos")
        llnode = ET.Element("localspos")
        cssnode = ET.Element("callsites")
        rrnode = ET.Element("returnsites")
        dcnode = ET.Element("direct-calls")
        idcnode = ET.Element("indirect-calls")
        for ls in self.local_spos.values():
            lnode = ET.Element("po")
            ls.write_xml(lnode)
            llnode.append(lnode)
        for cs in self.callsite_spos.values():
            if cs.is_direct_call:
                csnode = ET.Element("dc")
                cs.write_xml(csnode)
                dcnode.append(csnode)
            if cs.is_indirect_call:
                csnode = ET.Element("ic")
                cs.write_xml(csnode)
                idcnode.append(csnode)
        for rs in self.returnsite_spos.values():
            rsnode = ET.Element("rs")
            rs.write_xml(rsnode)
            rrnode.append(rsnode)
        snode.append(llnode)
        snode.append(cssnode)
        snode.append(rrnode)
        cssnode.extend([dcnode, idcnode])
        cnode.extend([snode])
