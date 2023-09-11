# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
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

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, TYPE_CHECKING

from chc.proof.CFunctionPO import get_dependencies, get_diagnostic

from chc.proof.CFunctionCallsiteSPOs import CFunctionCallsiteSPOs
from chc.proof.CFunctionReturnsiteSPOs import CFunctionReturnsiteSPOs
from chc.proof.CFunctionLocalSPO import CFunctionLocalSPO

from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPOs import CFunctionPOs

from chc.proof.CFunctionPO import CProofDependencies
from chc.proof.CFunctionPO import po_status
from chc.proof.CFunctionPO import CProofDiagnostic

if TYPE_CHECKING:
    from chc.proof.CFunctionProofs import CFunctionProofs


class CFunctionSPOs(CFunctionPOs):
    """Represents the set of supporting proof obligations for a function.

    xnode received is the content of the <"spos"> element.
    """

    def __init__(self, cproofs: "CFunctionProofs", xnode: ET.Element) -> None:
        CFunctionPOs.__init__(self, cproofs)
        self.xnode = xnode
        # self.cproofs = cproofs
        self.spocounter = 0
        self._localspos: Optional[Dict[int, CFunctionLocalSPO]] = None
        self._callsitespos: Optional[Dict[str, CFunctionCallsiteSPOs]] = None  # cfg-contextstring -> CFunctionCallsiteSPOs
        self._returnsitespos: Optional[Dict[str, CFunctionReturnsiteSPOs]] = None  # cfg-contextstring -> CFunctionReturnsiteSPOs
        # self._initialize()

    @property
    def spos(self) -> List[CFunctionPO]:
        result: List[CFunctionPO] = []
        result.extend(list(self.local_spos.values()))
        for cspos in self.callsite_spos.values():
            for spos in cspos.spos.values():
                result.extend(spos)
        # result.extend(list(self.callsite_spos.values()))
        for rspos in self.returnsite_spos.values():
            for sposr in rspos.spos.values():
                result.extend(sposr)
        # result.extend(list(self.returnsite_spos.values()))
        return result

    @property
    def local_spos(self) -> Dict[int, CFunctionLocalSPO]:
        if self._localspos is None:
            self._localspos = {}
            xlspos = self.xnode.find("localspos")
            if xlspos is not None:
                for po in xlspos.findall("po"):
                    spotype = self.podictionary.read_xml_spo_type(po)
                    xexpl = po.find("e")
                    expl = None if xexpl is None else xexpl.get("txt")
                    deps = get_dependencies(self, po)
                    xd = po.find("d")
                    diag = None if xd is None else get_diagnostic(xd)
                    status = po_status[po.get("s", "o")]
                    self._localspos[spotype.po_index] = CFunctionLocalSPO(
                        self, spotype, status, deps, expl, diag)
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
                        cspo = CFunctionCallsiteSPOs(self, cs)
                        cfgctxt = str(cspo.cfgcontext)
                        self._callsitespos[cfgctxt] = cspo
                xicss = xcss.find("indirect-calls")
                if xicss is not None:
                    for cs in xicss.findall("ic"):
                        cspo = CFunctionCallsiteSPOs(self, cs)
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
                    rsspos = CFunctionReturnsiteSPOs(self, rs)
                    cfgctxt = str(rsspos.cfgcontext)
                    self._returnsitespos[cfgctxt] = rsspos
        return self._returnsitespos

    def add_returnsite_postcondition(self, postcondition):
        for r in self.returnsite_spos.values():
            r.add_postcondition(postcondition)

    def update(self) -> None:
        for cs in self.callsite_spos.values():
            cs.update()

    def collect_post_assumes(self):
        """for all call sites collect postconditions from callee's contracts 
        and add as assume."""

        for cs in self.callsite_spos.values():
            cs.collect_post_assumes()

    def distribute_post_guarantees(self):
        for cs in self.callsitespos.values():
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

    '''
    def iter_callsites(self, f):
        for cs in sorted(self.callsitespos.values(), key=lambda p: (p.get_line())):
            f(cs)

    def iter(self, f):
        for localspo in self.localspos.values():
            f(localspo)
        for cs in sorted(self.callsitespos.values(), key=lambda p: (p.get_line())):
            cs.iter(f)
        for cs in self.returnsitespos.values():
            cs.iter(f)
    '''

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

    '''
    def _initialize(self):
        spos = self.xnode.find("spos")

        localspos = spos.find("localspos")
        if localspos is not None:
            for po in localspos.findall("po"):
                spotype = self.cfun.podictionary.read_xml_spo_type(po)
                expl = None if po.find("e") is None else po.find("e")
                deps = PO.get_dependencies(self, po)
                diag = PO.get_diagnostic(po.find("d"))
                status = po_status[po.get("s", "o")]
                self.localspos[spotype.id] = CFunctionLocalSPO(
                    self, spotype, status, deps, expl, diag
                )

        css = spos.find("callsites").find("direct-calls")
        if css is not None:
            for cs in css.findall("dc"):
                cspo = CFunctionCallsiteSPOs(self, cs)
                cfgctxt = cspo.get_cfg_context_string()
                self.callsitespos[cfgctxt] = cspo
        icss = spos.find("callsites").find("indirect-calls")
        if icss is not None:
            for cs in icss.findall("ic"):
                cspo = CFunctionCallsiteSPOs(self, cs)
                cfgctxt = cspo.get_cfg_context_string()
                self.callsitespos[cfgctxt] = cspo
        rss = spos.find("returnsites")
        if rss is not None:
            for rs in rss.findall("rs"):
                rsspos = CFunctionReturnsiteSPOs(self, rs)
                cfgctxt = rsspos.get_cfg_context_string()
                self.returnsitespos[cfgctxt] = rsspos
        '''
