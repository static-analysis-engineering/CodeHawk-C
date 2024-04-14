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

import chc.util.xmlutil as UX

import chc.proof.CFunctionPO as PO

from chc.app.CLocation import CLocation
from chc.app.CFileDictionary import CKeyLookupError

from chc.proof.CFunctionCallsiteSPO import CFunctionCallsiteSPO
from chc.proof.CFunctionPO import (
    CProofDependencies,
    CProofDiagnostic,
    po_status,
    get_diagnostic,
    get_dependencies)
from chc.proof.CFunctionPO import po_status
from chc.proof.CFunctionPO import CProofDiagnostic

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CContext import ProgramContext, CfgContext
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFunctionSPOs import CFunctionSPOs
    from chc.proof.CFunPODictionary import CFunPODictionary


class CallsiteTarget:

    def __init__(self, cspos: "CFunctionSPOs", xnode: ET.Element) -> None:
        self.xnode = xnode
        self._cspos = cspos

    @property
    def cspos(self) -> "CFunctionSPOs":
        return self._cspos

    @property
    def cfile(self) -> "CFile":
        return self.cspos.cfile

    def has_callee(self) -> bool:
        return "ivinfo" in self.xnode.attrib

    @property
    def callee(self) -> "CVarInfo":
        if self.has_callee():
            return self.cfile.declarations.read_xml_varinfo(self.xnode)
        else:
            raise UF.CHCError("Call target does not have a callee")

    def has_callee_exp(self) -> bool:
        return "iexp" in self.xnode.attrib

    @property
    def callee_exp(self) -> "CExp":
        if self.has_callee_exp():
            return self.cfile.dictionary.read_xml_exp(self.xnode)
        else:
            raise UF.CHCError("Call target does not have a callee expression")

    def has_callees(self) -> bool:
        return "icallee" in self.xnode.attrib

    @property
    def callees(self) -> List["CVarInfo"]:
        if "icallees" in self.xnode.attrib:
            xicallees = self.xnode.get("icallees")
            if xicallees is not None:
                return [
                    self.cfile.declarations.get_varinfo(int(i))
                    for i in xicallees.split(",")]
            else:
                raise UF.CHCError("Inconsistent icallees element")
        else:
            raise UF.CHCError("Call target does not have resolved callees")
        


class CFunctionCallsiteSPOs:
    """Represents the supporting proof obligations associated with a call site."""

    def __init__(self, cspos: "CFunctionSPOs", xnode: ET.Element) -> None:
        self._cspos = cspos
        self.xnode = xnode
        self._calltarget = CallsiteTarget(self._cspos, self.xnode)
        self._iargs: Optional[List[int]] = None
        self._callargs: Optional[List["CExp"]] = None
        self._spos: Optional[Dict[int, List[CFunctionCallsiteSPO]]] = None
        self._postassumes: Optional[List[int]] = None
        self._icallees: Optional[List[int]] = None
        self._callees: Optional[List["CVarInfo"]] = None
        # self.cfile = self.cspos.cfile
        # self.context = self.cfile.contexttable.read_xml_context(xnode)
        # self.header = xnode.get("header", "")
        # self.cfun = self.cspos.cfun
        # self.location = self.cfile.declarations.read_xml_location(xnode)
        # direct call
        '''
        if "ivinfo" in xnode.attrib:
            self.callee = self.cfile.declarations.read_xml_varinfo(xnode)
        else:
            self.callee = None
        # indirect call
        if "iexp" in xnode.attrib:
            self.callee_exp = self.cfile.declarations.dictionary.read_xml_exp(xnode)
        else:
            self.callee_exp = None
        # resolved targets from indirect call
        if "icallees" in xnode.attrib:
            self.icallees = xnode.get("icallees")
            self.callees = [
                self.cfile.declarations.get_varinfo(int(i))
                for i in self.icallees.split(",")
            ]
        else:
            self.icallees = None
            self.callees = None

        # supporting proof obligations and post condition assumptions
        self.spos = {}  # api-id -> CFunctionCallsiteSPO
        self.postassumes = []  # xpredicate id's

        # arguments to the call
        self.iargs = xnode.get("iargs")
        if self.iargs == "":
            self.args = []
        else:
            self.args = [
                self.cfile.declarations.dictionary.get_exp(int(i))
                for i in self.iargs.split(",")
            ]
        self._initialize(xnode)
        '''

    @property
    def calltarget(self) -> CallsiteTarget:
        return self._calltarget

    @property
    def iargs(self) -> List[int]:
        if self._iargs is None:
            xargs = self.xnode.get("iargs")
            if xargs is None:
                self._iargs = []
            elif xargs == "":
                self._iargs = []
            else:
                self._iargs = [int(i) for i in xargs.split(",")]
        return self._iargs

    @property
    def call_arguments(self) -> List["CExp"]:
        if self._callargs is None:
            self._callargs = [
                self.cfile.dictionary.get_exp(i) for i in self.iargs]
        return self._callargs

    @property
    def cspos(self) -> "CFunctionSPOs":
        return self._cspos

    @property
    def cfile(self) -> "CFile":
        return self.cspos.cfile

    @property
    def cfun(self) -> "CFunction":
        return self.cspos.cfun

    @property
    def podictionary(self) -> "CFunPODictionary":
        return self.cspos.podictionary

    @property
    def header(self) -> str:
        return self.xnode.get("header", "")

    @property
    def context(self) -> "ProgramContext":
        return self.contextdictionary.read_xml_context(self.xnode)

    @property
    def location(self) -> "CLocation":
        return self.cfile.declarations.read_xml_location(self.xnode)

    @property
    def contextdictionary(self) -> "CContextDictionary":
        return self.cspos.contextdictionary

    @property
    def spos(self) -> Dict[int, List[CFunctionCallsiteSPO]]:
        if self._spos is None:
            self._spos = {}
            xanode = self.xnode.find("api-conditions")
            if xanode is not None:
                for p in xanode.findall("api-c"):
                    xapid = p.get("iapi")
                    if xapid is not None:
                        self._spos[int(xapid)] = []
                        for xpo in p.findall("po"):
                            spotype = self.podictionary.read_xml_spo_type(xpo)
                            deps = get_dependencies(self.cspos, xpo)
                            status = po_status[xpo.get("s", "o")]
                            xexpl = xpo.find("e")
                            expl = None if xexpl is None else xexpl.get("txt")
                            dnode = xpo.find("d")
                            if dnode is not None:
                                diag: Optional[CProofDiagnostic] = get_diagnostic(dnode)
                            else:
                                diag = None
                            self._spos[int(xapid)].append(
                                CFunctionCallsiteSPO(
                                    self.cspos, spotype, status, deps, expl, diag))
        return self._spos

    @property
    def postassumes(self) -> List[int]:
        if self._postassumes is None:
            self._postassumes = []
            xpost = self.xnode.find("post-assumes")
            if xpost is not None:
                xipcs = xpost.get("iipcs")
                if xipcs is not None:
                    self._postassumes = [int(x) for x in xipcs.split(",")]
        return self._postassumes

    @property
    def is_indirect_call(self) -> bool:
        return self.calltarget.has_callee_exp()

    @property
    def is_direct_call(self) -> bool:
        return self.calltarget.has_callee()

    def has_callee(self) -> bool:
        return self.calltarget.has_callee()

    @property
    def callee(self) -> "CVarInfo":
        return self.calltarget.callee

    def has_callee_exp(self) -> bool:
        return self.calltarget.has_callee_exp()

    @property
    def icallees(self) -> List[int]:
        """Indices of indirect calls."""

        if self._icallees is None:
            icallees = self.xnode.get("icallees")
            if icallees is None:
                self._icallees = []
            else:
                self._icallees = [int(i) for i in icallees.split(",")]
        return self._icallees

    @property
    def callees(self) -> List["CVarInfo"]:
        """Resolved indirect call targets."""

        if self._callees is None:
            self._callees = [
                self.cfile.declarations.get_varinfo(i) for i in self.icallees]
        return self._callees

    @property
    def callee_exp(self) -> "CExp":
        return self.calltarget.callee_exp

    @property
    def line(self) -> int:
        return self.location.line

    @property
    def cfgcontext(self) -> "CfgContext":
        return self.context.cfg_context

    def update(self) -> None:
        """Update the spo's associated with the call site."""

        if not self.has_callee():
            chklogger.logger.warning(
                "missing callee in %s - %s", self.cfile.name, self.cfun.name)
            return

        # retrieve callee information
        if self.header.startswith("lib:"):
            return

        calleefun = self.cfile.capp.resolve_vid_function(
            self.cfile.index, self.callee.vid)
        if calleefun is None:
            chklogger.logger.warning(
                "missing external function in %s - %s: %s",
                self.cfile.name, self.cfun.name, self.callee)
            return

        # retrieve callee's api assumptions and substitute parameters by
        # arguments
        api = calleefun.api
        calleefile = calleefun.cfile
        if len(api.api_assumptions) > 0:
            pars = api.parameters
            vids = api.formal_vids
            subst = {}
            if len(pars) == len(self.call_arguments):
                substitutions = zip(vids, self.call_arguments)
                for (vid, arg) in substitutions:
                    subst[vid] = arg
            else:
                chklogger.logger.warning(
                    "number of arguments (%s) is not the same as the number "
                    + "of parameters (%s) in call to %s in function %s "
                    + "in file %s",
                    str(len(self.call_arguments)),
                    str(len(pars)),
                    calleefun.name,
                    self.cfun.name,
                    self.cfile.name)
                return
            if len(api.api_assumptions) > 0:
                '''
                if (
                    calleefile.has_file_contracts()
                    and calleefile.index != self.cfile.index
                ):
                    gvarinfos = calleefile.contracts.globalvariables.values()
                    for othergvar in gvarinfos:
                        othervid = othergvar.gvinfo.vid
                        thisvid = self.cfile.capp.convert_vid(
                            calleefile.index, othervid, self.cfile.index
                        )
                        if thisvid is None:
                            gvid = self.cfile.capp.indexmanager.get_gvid(
                                calleefile.index, othervid
                            )
                            gvarinfo = self.cfile.capp.declarations.get_varinfo(gvid)
                            gvarname = gvarinfo.vname + "__" + str(gvid) + "__"
                            gvartyp = othergvar.gvinfo.vtype.get_opaque_type()
                            thisvtypeix = self.cfile.declarations.dictionary.index_typ(
                                gvartyp
                            )
                            thisvinfoix = (
                                self.cfile.declarations.make_opaque_global_varinfo(
                                    gvid, gvarname, thisvtypeix
                                )
                            )
                            thisvinfo = self.cfile.declarations.get_varinfo(thisvinfoix)
                            logging.warning(
                                self.cfile.name
                                + ": "
                                + self.cfun.name
                                + " call to "
                                + calleefun.name
                                + " ("
                                + str(calleefun.cfile.name)
                                + "): global api variable "
                                + othergvar.gvinfo.vname
                                + " (gvid:"
                                + str(gvid)
                                + ")"
                                + " converted to opaque variable"
                                + " (vinfo-ix:"
                                + str(thisvinfoix)
                                + ")"
                            )
                        else:
                            thisvinfo = self.cfile.declarations.get_global_varinfo(
                                thisvid
                            )
                            if thisvinfo is None:
                                logging.warning(
                                    self.cfile.name
                                    + ": "
                                    + self.cfun.name
                                    + " call to "
                                    + calleefun.name
                                    + " ("
                                    + str(calleefun.cfile.name)
                                    + "): global api variable "
                                    + othergvar.gvinfo.vname
                                    + " not found"
                                )
                                return
                        expindex = (
                            self.cfile.declarations.dictionary.varinfo_to_exp_index(
                                thisvinfo
                            )
                        )
                        subst[othervid] = self.cfile.declarations.dictionary.get_exp(
                            expindex
                        )
                '''
            for a in api.api_assumptions.values():
                if a.id in self.spos:
                    continue
                if a.isfile:
                    continue  # file_level assumption
                try:
                    pid = self.cfile.predicatedictionary.index_predicate(
                        a.predicate, subst=subst
                    )
                    apiid = a.id
                    self.spos[apiid] = []
                    ictxt = self.contextdictionary.index_context(self.context)
                    iloc = self.cfile.declarations.index_location(self.location)
                    ispotype = self.cfun.podictionary.index_spo_type(
                        ["cs"], [iloc, ictxt, pid, apiid]
                    )
                    spotype = self.cfun.podictionary.get_spo_type(ispotype)
                    self.spos[apiid].append(CFunctionCallsiteSPO(self.cspos, spotype))
                except CKeyLookupError as e:
                    chklogger.logger.warning(
                        "%s: %s call to %s (%s) request datastructure condition "
                        + "for %s for key %s to handle assumption",
                        self.cfile.name,
                        self.cfun.name,
                        calleefun.name,
                        str(calleefun.cfile.name),
                        str(a.predicate),
                        str(e.ckey))
                except LookupError as e:
                    chklogger.logger.warning(
                        "%s: %s call to %s (%s) request datastruction condition "
                        + "for %s: %s to handle api assumption",
                        self.cfile.name,
                        self.cfun.name,
                        calleefun.name,
                        str(calleefun.cfile.name),
                        str(a.predicate),
                        str(e))
                except Exception as e:
                    chklogger.logger.warning(
                        "%s: %s call to %s (%s): unable to create spo for "
                        + "assumption %s: %s",
                        self.cfile.name,
                        self.cfun.name,
                        calleefun.name,
                        str(calleefun.cfile.name),
                        str(a),
                        str(e))

    def collect_post_assumes(self) -> None:
        """Collect postconditions from callee's contract and add as assume."""
        if self.header.startswith("lib:"):
            return
        if not self.has_callee():
            return
        # retrieve callee information
        calleefun = self.cfile.capp.resolve_vid_function(
            self.cfile.index, self.callee.vid)
        if calleefun is None:
            return

        # retrieve postconditions from the contract of the callee
        if calleefun.cfile.has_function_contract(calleefun.name):
            fcontract = calleefun.cfile.get_function_contract(calleefun.name)
            for p in fcontract.postconditions.values():
                iipc = self.cfile.interfacedictionary.index_xpredicate(p)
                if iipc not in self.postassumes:
                    self.postassumes.append(iipc)

    def get_context_string(self):
        return self.context.context_strings()

    '''
    def iter(self, f):
        for id in self.spos:
            for spo in self.spos[id]:
                f(spo)
    '''

    def get_spo(self, id: int) -> CFunctionCallsiteSPO:
        for apiid in self.spos:
            for spo in self.spos[apiid]:
                if spo.po_index == id:
                    return spo
        raise UF.CHCError("Call site spos does not include id " + str(id))

    def has_spo(self, id: int) -> bool:
        for apiid in self.spos:
            for spo in self.spos[apiid]:
                if spo.po_index == id:
                    return True
        return False

    def write_xml(self, cnode: ET.Element) -> None:
        # write location
        self.cfile.declarations.write_xml_location(cnode, self.location)
        self.cfile.contextdictionary.write_xml_context(cnode, self.context)
        if self.header != "":
            cnode.set("header", self.header)

        # write information about the callee
        if self.has_callee():
            self.cfile.declarations.write_xml_varinfo(cnode, self.callee)
        if self.has_callee_exp():
            self.cfile.declarations.dictionary.write_xml_exp(cnode, self.callee_exp)
        if len(self.icallees) > 0:
            cnode.set("icallees", ",".join(str(i) for i in self.icallees))
        cnode.set("iargs", ",".join(str(i) for i in self.iargs))

        # write api assumptions associated with the callee at the call site
        oonode = ET.Element("api-conditions")
        for apiid in self.spos:
            apinode = ET.Element("api-c")
            apinode.set("iapi", str(apiid))
            for spo in self.spos[apiid]:
                onode = ET.Element("po")
                spo.write_xml(onode)
                apinode.append(onode)
            oonode.append(apinode)
        cnode.append(oonode)

        # write assumptions about the post conditions of the callee
        if len(self.postassumes) > 0:
            panode = ET.Element("post-assumes")
            panode.set("iipcs", ",".join([str(i) for i in sorted(self.postassumes)]))
            cnode.append(panode)

    '''
    def _initialize(self, xnode):
        # read in api assumptions associated with the call site
        oonode = xnode.find("api-conditions")
        if oonode is not None:
            for p in oonode.findall("api-c"):
                apiid = int(p.get("iapi"))
                self.spos[apiid] = []
                for po in p.findall("po"):
                    spotype = self.cfun.podictionary.read_xml_spo_type(po)
                    deps = None
                    status = po_status[po.get("s", "o")]
                    deps = PO.get_dependencies(self, po)
                    expl = None
                    enode = po.find("e")
                    if enode is not None:
                        expl = enode.get("txt")
                    diag = None
                    dnode = po.find("d")
                    if dnode is not None:
                        diag = PO.get_diagnostic(dnode)
                    self.spos[apiid].append(
                        CFunctionCallsiteSPO(self, spotype, status, deps, expl, diag)
                    )

        # read in assumptions about the post conditions of the callee
        ppnode = xnode.find("post-assumes")
        if ppnode is not None:
            self.postassumes = [int(x) for x in ppnode.get("iipcs").split(",")]
    '''
