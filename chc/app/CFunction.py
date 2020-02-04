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

import chc.util.fileutil as UF

from chc.app.CFunctionBody import CFunctionBody
from chc.app.CLocation import CLocation
from chc.app.CFunDeclarations import CFunDeclarations
from chc.app.CVarInfo import CVarInfo
from chc.invariants.CFunVarDictionary import CFunVarDictionary
from chc.invariants.CFunInvDictionary import CFunInvDictionary
from chc.invariants.CFunInvariantTable import CFunInvariantTable

from chc.api.CFunctionApi import CFunctionApi
from chc.proof.CFunPODictionary import CFunPODictionary
from chc.proof.CFunctionProofs import CFunctionProofs

class CFunction(object):
    '''Function implementation.'''

    def __init__(self,cfile,xnode):
        self.cfile = cfile
        self.capp = self.cfile.capp
        self.xnode = xnode
        self.fdecls = CFunDeclarations(self,xnode.find('declarations'))
        self.svar = self.cfile.declarations.get_varinfo(int(xnode.find('svar').get('ivinfo')))
        self.ftype = self.svar.vtype
        self.name = self.svar.vname
        self.formals = {}                            # vid -> CVarInfo
        self.locals = {}                             # vid -> CVarInfo
        self.body = CFunctionBody(self,self.xnode.find('sbody'))
        self.podictionary = CFunPODictionary(self)
        self.proofs = CFunctionProofs(self)        
        self.api = CFunctionApi(self)              
        self.vard = CFunVarDictionary(self.fdecls)
        self.invd = CFunInvDictionary(self.vard)
        self.invtable = CFunInvariantTable(self.invd)
        self.invariants = None                       # CFunctionInvariants object
        self._initialize()

    def reinitialize_tables(self):
        self.api = CFunctionApi(self)
        self.podictionary.initialize()
        self.vard.initialize(force=True)

    def export_function_data(self,result):
        result[self.name] = {}
        fnresult =  result[self.name]
        fnresult['type'] = self.ftype.to_idict()
        fnresult['typestr'] = str(self.ftype)
        fnresult['stmt-count'] = self.get_stmt_count()
        fnresult['instr-count'] = self.get_instr_count()
        fnresult['call-instrs'] = [ i.to_dict()  for i in self.get_call_instrs() ]
        fnresult['call-instrs-strs'] = [ str(i) for i in self.get_call_instrs() ]

    def get_formal_vid(self,name):
        for v in self.formals:
            if self.formals[v].vname == name: return v
        else:
            print('Formals: ' + ','.join([ str(v) for v in self.formals.values() ]))

    def get_variable_vid(self,vname):
        for v in self.formals:
            if self.formals[v].vname == vname: return self.formals[v].get_vid()
        for v in self.locals:
            if self.locals[v].vname == vname: return self.locals[v].get_vid()

    # returns a list of strings
    def get_strings(self):
        return self.body.get_strings()

    # returns the number of occurrences of vid in expressions and lhs
    def get_variable_uses(self,vid):
        return self.body.get_variable_uses(vid)

    def has_function_contract(self):
        return self.cfile.has_function_contract(self.name)

    def get_function_contract(self):
        if self.has_function_contract():
            return self.cfile.get_function_contract(self.name)

    def selfignore(self):
        return self.has_function_contract() and self.get_function_contract().ignore

    def iter_ppos(self,f): self.proofs.iter_ppos(f)

    def get_ppo(self,index): return self.proofs.get_ppo(index)

    def get_spo(self,index): return self.proofs.get_spo(index)

    def iter_callsites(self,f): self.proofs.iter_callsites(f)

    def get_vid(self): return self.svar.get_vid()

    def get_api(self): return self.api

    def get_location(self): return self.svar.vdecl

    def get_source_code_file(self): return self.get_location().get_file()

    def get_line_number(self):
        if self.cfile.name + '.c' == self.get_source_code_file():
            return self.get_location().get_line()

    def get_formals(self): return self.formals.values()

    def get_locals(self): return self.locals.values()

    def get_body(self): return self.body

    def get_block_count(self): return self.body.get_block_count()

    def get_stmt_count(self): return self.body.get_stmt_count()

    def get_instr_count(self): return self.body.get_instr_count()

    def get_call_instrs(self): return self.body.get_call_instrs()

    def get_invariants(self):
        self._readinvariants()
        return self.invariants

    def violates_contract_conditions(self):
        return len(self.api.contractconditionfailures) > 0

    def get_contract_condition_violations(self):
        return self.api.contractconditionfailures

    def get_proofs(self): return self.proofs

    def get_callsite_spos(self): return self.proofs.getspos

    def update_spos(self):
        if self.selfignore(): return
        self.proofs.update_spos()

    def collect_post_assumes(self):
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self.proofs.collect_post_assumes()
        self.save_spos()

    def distribute_post_guarantees(self): self.proofs.distribute_post_guarantees()

    def collect_post(self):
        '''Add postcondition requests to the contract of the callee'''
        for r in self.get_api().get_postcondition_requests():
            tgtfid = r.callee.get_vid()
            tgtfun = self.capp.resolve_vid_function(self.cfile.index,tgtfid)
            if tgtfun is None:
                print('No function found to register post request in function ' +
                          self.cfile.name + ':' + self.name)
            else:
                tgtcfile = tgtfun.cfile
                if tgtfun.cfile.has_function_contract(tgtfun.name):
                    tgtifx = tgtfun.cfile.interfacedictionary
                    tgtpostconditionix = tgtifx.index_xpredicate(r.postcondition)
                    tgtpostcondition = tgtifx.get_xpredicate(tgtpostconditionix)
                    cfuncontract = tgtcfile.get_function_contract(tgtfun.name)
                    cfuncontract.add_postrequest(tgtpostcondition)

    def save_spos(self): self.proofs.save_spos()

    def save_pod(self):
        cnode = ET.Element('function')
        cnode.set('name',self.name)
        self.podictionary.write_xml(cnode)
        UF.save_pod_file(self.cfile.capp.path,self.cfile.name,self.name,cnode)

    def reload_ppos(self): self.proofs.reload_ppos()

    def reload_spos(self): self.proofs.reload_spos()

    def get_ppos(self): return self.proofs.get_ppos()

    def get_spos(self): return self.proofs.get_spos()

    def get_open_ppos(self): return self.proofs.get_open_ppos()

    def get_open_spos(self): return self.proofs.get_open_spos()

    def get_violations(self): return self.proofs.get_violations()

    def get_spo_violations(self): return self.proofs.get_spo_violations()

    def get_delegated(self): return self.proofs.get_delegated()

    def _initialize(self):
        for v in self.fdecls.get_formals():
            self.formals[v.get_vid()] = v
        for v in self.fdecls.get_locals(): self.locals[v.get_vid()] = v
        self.vard.initialize()
        self.invtable.initialize()

    def _read_invariants(self):
        if not self.invariants is None: return
        xinvs = UF.get_invs_xnode(self.cfile.capp.path,self.cfile.name,self.name)
        self.invariants = CFunctionInvariants(self,xinvs)

