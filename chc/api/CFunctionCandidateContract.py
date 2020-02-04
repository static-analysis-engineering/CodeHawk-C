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

import xml.etree.ElementTree as ET

class CFunctionCandidateContract(object):
    '''Representsa a function contract to collect analysis-produced requests.'''

    def __init__(self,cfilecontracts,xnode):
        self.cfilecontracts = cfilecontracts
        self.ixd = self.cfilecontracts.cfile.interfacedictionary
        self.prd = self.cfilecontracts.cfile.predicatedictionary
        self.xnode = xnode
        self.name  = self.xnode.get('name')
        self.cfun = self.cfilecontracts.cfile.get_function_by_name(self.name)
        self.api = self.cfun.api
        self.signature = {}                   # name -> index nr
        self.rsignature = {}                  # index nr -> name
        self.postrequests = {}                # index -> XPredicate
        self.postguarantees = {}              # index -> XPredicate
        self._initialize(self.xnode)

    def collect_post(self):
        '''collect advertised post condition from this function's api'''
        guarantees = self.api.get_postcondition_guarantees()
        for g in guarantees:
            if g.index in self.postconditions: continue
            self.postguarantees[g.index] = g

    def add_postrequest(self,pc):
        '''add post request from caller's function api'''
        if pc.index in self.postconditions: return
        self.postrequests[pc.index] = pc

    def add_datastructure_request(self,ckey,predicate):
        '''add data structure request from caller's function spo'''
        pc = self.convert_to_post(ckey,predicate)
        if not ((ckey,pc.index) in self.datastructurerequests):
            self.datastructurerequests[(ckey,pc.index)] = pc

    def convert_to_post(self,ckey,p):
        if p.is_initialized():
            lval = p.get_lval()
            offset = lval.get_offset()
            if offset.is_field() and not offset.get_offset().has_offset():
                fieldname = offset.get_fieldname()
                fieldterm = self.ixd.mk_field_s_term(fieldname)
                return self.ixd.mk_initialized_xpredicate(fieldterm)

    def write_mathml_parameters(self,cnode):
        for par in self.signature:
            pnode = ET.Element('par')
            pnode.set('name',par)
            pnode.set('nr',str(self.signature[par]))
            cnode.append(pnode)

    def write_mathml_postrequests(self,cnode):
        for pr in self.postrequests.values():
            prnode = ET.Element('post')
            prnode.set('status','request')
            prmnode = ET.Element('math')
            pr.write_mathml(prmnode,self.rsignature)
            cnode.append(prnode)
            prnode.append(prmnode)

    def write_mathml_postguarantees(self,cnode):
        for p in self.postguarantees.values():
            pnode = ET.Element('post')
            pnode.set('status','guarantee')
            pmnode = ET.Element('math')
            p.write_mathml(pmnode,self.rsignature)
            cnode.append(pnode)
            pnode.append(pmnode)            

    def write_mathml_postconditions(self,cnode):
        for p in self.postconditions.values():
            pnode = ET.Element('post')
            pnode.set('status','use')
            pmnode = ET.Element('math')
            p.write_mathml(pmnode,self.rsignature)
            cnode.append(pnode)
            pnode.append(pmnode)

    def write_mathml_datastructurerequests(self,cnode):
        for (ckey,predid) in self.datastructurerequests:
            pred = self.ixd.get_xpredicate(predid)
            structname = self.cfilecontracts.cfile.declarations.get_structname(ckey)
            dnode = ET.Element('ds-request')
            dnode.set('ckey',str(ckey))
            dnode.set('predid',str(predid))
            dnode.set('predicate',str(pred))
            dnode.set('structname',structname)
            mnode = ET.Element('math')
            pred.write_mathml(mnode,self.rsignature)
            dnode.append(mnode)
            cnode.append(dnode)

    def write_mathml(self,fnode):
        parsnode = ET.Element('parameters')
        ppnode = ET.Element('postconditions')
        ssnode = ET.Element('sideeffects')
        ddnode = ET.Element('data-structure-requests')
        self.write_mathml_parameters(parsnode)
        self.write_mathml_postrequests(ppnode)
        self.write_mathml_postconditions(ppnode)
        self.write_mathml_postguarantees(ppnode)
        self.write_mathml_datastructurerequests(ddnode)
        fnode.extend([ parsnode, ppnode, ssnode, ddnode ])
        
    def _initialize_signature(self,ppnode):
        if ppnode is None:
            print('Problem with kta function contract signature: ' + self.name)
            return
        for pnode in ppnode.findall('par'):
            self.signature[pnode.get('name')] = int(pnode.get('nr'))
            self.rsignature[int(pnode.get('nr'))] = pnode.get('name')

    def _initialize_postconditions(self,pcsnode):
        for pcnode in pcsnode.findall('post'):
            ipc = self.ixd.parse_mathml_xpredicate(pcnode,self.signature)
            pc = self.ixd.get_xpredicate(ipc)
            status = pcnode.get('status','use')
            if status == 'request':
                self.postrequests[ipc] = pc
            elif status == 'guarantee':
                self.postguarantees[ipc] = pc
            else:
                self.postconditions[ipc] = pc

    def _initialize_datastructure_requests(self,ddnode):
        for rnode in ddnode.findall('ds-request'):
            ckey = int(rnode.get('ckey'))
            predid = int(rnode.get('predid'))
            self.datastructurerequests[(ckey,predid)] = self.ixd.get_xpredicate(predid)

    def _initialize_frame_conditions(self,fnode): pass

    def _initialize(self,xnode):
        self._initialize_signature(xnode.find('parameters'))
        self._initialize_postconditions(xnode.find('postconditions'))
        self._initialize_datastructure_requests(xnode.find('data-structure-requests'))
        self._initialize_frame_conditions(xnode.find('frame-conditions'))

    def __str__(self):
        lines = []
        lines.append('Contract for ' + self.name)
        lines.append('-' * 80)
        def add(t, pl):
            if len(pl) > 0:
                lines.append(t)
                for p in pl: lines.append('   ' + str(p))
        add('Postconditions used', self.postconditions.values())
        add('Postconditions guaranteed', self.postguarantees.values())
        add('Postconditions requested', self.postrequests.values())
        return '\n'.join(lines)
                                            

