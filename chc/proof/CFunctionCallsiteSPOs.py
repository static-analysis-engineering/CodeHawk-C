# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
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

import logging

import xml.etree.ElementTree as ET

import chc.util.xmlutil as UX

import chc.proof.CFunctionPO as PO

from chc.app.CLocation import CLocation
from chc.app.CFileDictionary import CKeyLookupError

from chc.proof.CFunctionCallsiteSPO import CFunctionCallsiteSPO
from chc.proof.CFunctionPO import CProofDependencies
from chc.proof.CFunctionPO import po_status
from chc.proof.CFunctionPO import CProofDiagnostic


class CFunctionCallsiteSPOs(object):
    """Represents the supporting proof obligations associated with a call site."""

    def __init__(self,cspos,xnode):
        self.cspos = cspos
        self.cfile = self.cspos.cfile
        self.context = self.cfile.contexttable.read_xml_context(xnode)
        self.header = xnode.get('header','') 
        self.cfun = self.cspos.cfun
        self.location = self.cfile.declarations.read_xml_location(xnode)
        # direct call
        if 'ivinfo' in xnode.attrib:
            self.callee = self.cfile.declarations.read_xml_varinfo(xnode)
        else:
            self.callee = None
        # indirect call
        if 'iexp' in xnode.attrib:
            self.callee_exp = self.cfile.declarations.dictionary.read_xml_exp(xnode)
        else:
            self.callee_exp = None
        # resolved targets from indirect call
        if 'icallees' in xnode.attrib:
            self.icallees = xnode.get('icallees')
            self.callees = [ self.cfile.declarations.get_varinfo(int(i))
                                  for i in self.icallees.split(',') ]
        else:
            self.icallees = None
            self.callees = None

        # supporting proof obligations and post condition assumptions
        self.spos = {}                  # api-id -> CFunctionCallsiteSPO
        self.postassumes = []           # xpredicate id's

        # arguments to the call
        self.iargs = xnode.get('iargs')
        if self.iargs == "":
            self.args = []
        else:
            self.args = [ self.cfile.declarations.dictionary.get_exp(int(i))
                              for i in self.iargs.split(',') ]
        self._initialize(xnode)

    def is_indirect_call(self): return not (self.callee_exp is None)

    def is_direct_call(self): return (self.callee_exp is None)

    def has_callee(self): return not (self.callee is None)

    def get_line(self): return self.location.get_line()

    def get_cfg_context_string(self): return str(self.context)

    def update(self):
        """Update the spo's associated with the call site."""

        if not self.has_callee():
            logging.warning('Missing callee in ' + self.cfile.name + ' - ' +
                                self.cfun.name)
            return

        # retrieve callee information
        if  self.header.startswith('lib:'): return
        cfile = self.cfile
        calleefun = cfile.capp.resolve_vid_function(cfile.index,self.callee.get_vid())
        if calleefun is None:
            logging.warning('Missing external function in ' + self.cfile.name + ' - ' +
                                self.cfun.name + ': ' + str(self.callee))
            return

        # retrieve callee's api assumptions and substitute parameters by arguments
        api = calleefun.get_api()
        calleefile = calleefun.cfile
        if len(api.get_api_assumptions()) > 0:
            pars = api.get_parameters()
            vids = api.get_formal_vids()
            subst = {}
            if len(pars) == len(self.args):
                substitutions = zip(vids,self.args)
                for (vid,arg) in substitutions:
                    subst[vid] = arg
            else:
                logging.warning('Number of arguments (' + str(len(self.args))
                        + ') is not the same as the number of parameters (' + str(len(pars))
                        + ') in call to ' + calleefun.name + ' in function ' + self.cfun.name
                        + ' in file ' + cfile.name)
                return
            if len(api.get_api_assumptions()) > 0:
                if calleefile.has_file_contracts() and calleefile.index != self.cfile.index:
                    gvarinfos = calleefile.contracts.globalvariables.values()
                    for othergvar in gvarinfos:
                        othervid = othergvar.gvinfo.get_vid()
                        thisvid = self.cfile.capp.convert_vid(calleefile.index,othervid,self.cfile.index)
                        if thisvid is None:
                            gvid = self.cfile.capp.indexmanager.get_gvid(calleefile.index,othervid)
                            gvarinfo = self.cfile.capp.declarations.get_varinfo(gvid)
                            gvarname = gvarinfo.vname + '__' + str(gvid) + '__'
                            gvartyp = othergvar.gvinfo.vtype.get_opaque_type()
                            thisvtypeix = self.cfile.declarations.dictionary.index_typ(gvartyp)
                            thisvinfoix = self.cfile.declarations.make_opaque_global_varinfo(gvid,gvarname,thisvtypeix)
                            thisvinfo = self.cfile.declarations.get_varinfo(thisvinfoix)
                            logging.warning(cfile.name + ': ' + self.cfun.name + ' call to '
                                                + calleefun.name + ' (' + str(calleefun.cfile.name)
                                                + '): global api variable ' + othergvar.gvinfo.vname
                                                + ' (gvid:' + str(gvid) + ')'
                                                + ' converted to opaque variable'
                                                + ' (vinfo-ix:' + str(thisvinfoix) + ')')
                        else:
                            thisvinfo = self.cfile.declarations.get_global_varinfo(thisvid)
                            if thisvinfo is None:
                                logging.warning(cfile.name + ': ' + self.cfun.name + ' call to '
                                                + calleefun.name + ' (' + str(calleefun.cfile.name)
                                                + '): global api variable ' + othergvar.gvinfo.vname
                                                + ' not found')
                                return
                        expindex = self.cfile.declarations.dictionary.varinfo_to_exp_index(thisvinfo)
                        subst[othervid] = self.cfile.declarations.dictionary.get_exp(expindex)
            for a in api.get_api_assumptions():
                if a.id in self.spos: continue
                if a.isfile: continue       # file_level assumption
                try:
                    pid = self.cfile.predicatedictionary.index_predicate(a.predicate,subst=subst)
                    apiid = a.id
                    self.spos[apiid] = []
                    ictxt = self.cfile.contexttable.index_context(self.context)
                    iloc = self.cfile.declarations.index_location(self.location)
                    ispotype = self.cfun.podictionary.index_spo_type(['cs'],[iloc,ictxt,pid,apiid])
                    spotype = self.cfun.podictionary.get_spo_type(ispotype)
                    self.spos[apiid].append(CFunctionCallsiteSPO(self,spotype))
                except CKeyLookupError as e:
                    logging.warning(cfile.name + ': ' + self.cfun.name + ' call to '
                                        + calleefun.name + ' (' + str(calleefun.cfile.name)
                                        + ') request datastructure condition for '
                                        + str(a.predicate) + ' for key ' + str(e.ckey)
                                        + ' to handle api assumption')
                except LookupError as e:
                    logging.warning(cfile.name + ': ' + self.cfun.name + ' call to '
                                        + calleefun.name + ' (' + str(calleefun.cfile.name)
                                        + ') request datastructure condition for '
                                        + str(a.predicate) + ': ' + str(e)
                                        + ' to handle api assumption')
                except Exception as e:
                    logging.warning(cfile.name + ': ' + self.cfun.name + ' call to '
                                        + calleefun.name + ' (' + str(calleefun.cfile.name)
                                        + '): unable to create spo for assumption '
                                        + str(a) + ': ' + str(e))


    def collect_post_assumes(self):
        """Collect postconditions from callee's contract and add as assume."""
        if self.header.startswith('lib:'): return
        if not self.has_callee(): return
        # retrieve callee information
        cfile = self.cfile
        calleefun = cfile.capp.resolve_vid_function(cfile.index,self.callee.get_vid())
        if calleefun is None: return

        # retrieve postconditions from the contract of the callee
        if calleefun.cfile.has_function_contract(calleefun.name):
            fcontract = calleefun.cfile.get_function_contract(calleefun.name)
            for p in fcontract.postconditions.values():
                iipc = self.cfile.interfacedictionary.index_xpredicate(p)
                if not iipc in self.postassumes:
                    self.postassumes.append(iipc)

    def get_context_string(self): return self.context.context_strings()

    def iter(self,f):
        for id in self.spos:
            for spo in self.spos[id]:
                f(spo)

    def get_spo(self,id):
        for apiid in self.spos:
            for spo in self.spos[apiid]:
                if  spo.id == id: return spo

    def has_spo(self,id):
        for apiid in self.spos:
            for spo in self.spos[apiid]:
                if spo.id == id: return True
        return False

    def write_xml(self,cnode):
        # write location
        self.cfile.declarations.write_xml_location(cnode,self.location)
        self.cfile.contexttable.write_xml_context(cnode,self.context)
        if self.header != '': cnode.set('header',self.header)

        # write information about the callee
        if not self.callee is None:
            self.cfile.declarations.write_xml_varinfo(cnode,self.callee)
        if not self.callee_exp is None:
            self.cfile.declarations.dictionary.write_xml_exp(cnode,self.callee_exp)
        if not self.icallees is None:
            cnode.set('icallees',self.icallees)
        cnode.set('iargs',self.iargs)

        # write api assumptions associated with the callee at the call site
        oonode = ET.Element('api-conditions')
        for apiid in self.spos:
            apinode = ET.Element('api-c')
            apinode.set('iapi',str(apiid))
            for spo in self.spos[apiid]:
                onode = ET.Element('po')
                spo.write_xml(onode)
                apinode.append(onode)
            oonode.append(apinode)
        cnode.append(oonode)

        # write assumptions about the post conditions of the callee
        if len(self.postassumes) > 0:
            panode = ET.Element('post-assumes')
            panode.set('iipcs',','.join([ str(i) for i in sorted(self.postassumes) ]))
            cnode.append(panode)


    def _initialize(self,xnode):
        # read in api assumptions associated with the call site
        oonode = xnode.find('api-conditions')
        if not oonode is None:
            for p in oonode.findall('api-c'):
                apiid = int(p.get('iapi'))
                self.spos[apiid] = []
                for po in p.findall('po'):
                    spotype = self.cfun.podictionary.read_xml_spo_type(po)
                    deps = None
                    status = po_status[po.get('s','o')]
                    deps = PO.get_dependencies(self,po)
                    expl = None
                    enode = po.find('e')
                    if not enode is None:
                        expl = enode.get('txt')
                    diag = None
                    dnode = po.find('d')
                    if not dnode is None:
                        diag = PO.get_diagnostic(dnode)
                    self.spos[apiid].append(CFunctionCallsiteSPO(self,spotype,status,deps,expl,diag))

        # read in assumptions about the post conditions of the callee
        ppnode = xnode.find('post-assumes')
        if not ppnode is None:
            self.postassumes = [ int(x) for x in ppnode.get('iipcs').split(',') ]

