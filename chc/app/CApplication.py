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
import os
import logging
import multiprocessing
import sys

import chc.util.fileutil as UF

from chc.api.CGlobalContract import CGlobalContract

from chc.app.CCompInfo import CCompInfo
from chc.app.CFile import CFile
from chc.app.CVarInfo import CVarInfo
from chc.app.IndexManager import IndexManager
from chc.app.CGlobalDeclarations import CGlobalDeclarations

from chc.source.CSrcFile import CSrcFile

class CApplication(object):
    """Primary access point for source code and analysis results."""

    def __init__(self,path,cfilename=None,srcpath=None,contractpath=None,
                     candidate_contractpath=None,excludefiles=[],includefiles=None):
        self.singlefile = not (cfilename is None)
        self.path = UF.get_chc_artifacts_path(path)
        self.srcpath = os.path.join(path,'sourcefiles') if srcpath is None else srcpath
        self.contractpath = contractpath
        self.globalcontract = None
        self.excludefiles = excludefiles   # files analyzed: all excluding these
        self.includefiles = includefiles   # files analyzed (if not None): these
        if not self.contractpath is None:
            self.globalcontract = CGlobalContract(self)
        self.candidate_contractpath = candidate_contractpath
        self.filenames = {}          # file index -> filename
        self.files = {}              # filename -> CFile
        if self.singlefile:
            self.declarations = None         # TBD: set to CFileDeclarations
        else:
            self.declarations = CGlobalDeclarations(self)
        self.indexmanager = IndexManager(self.singlefile)
        self.callgraph = {}     # (fid,vid) -> (callsitespos, (tgtfid,tgtvid))
        self.revcallgraph = {}  # (tgtfid,tgtvid) -> ((fid,vid),callsitespos)
        self._initialize(cfilename)

    def get_filenames(self): return self.filenames.values()

    """Returns true if name is a base filename."""
    def is_application_header(self,name):
        for n in self.get_filenames():
            if name == os.path.basename(n[:-2]):
                return True
        else:
            return False

    def get_max_filename_length(self):
        return max([ len(x) for x in self.get_filenames()])

    def get_filename_dictionary(self):
        result = {}
        for f in self.get_files():
            result[f.name] = []
            for fn in f.get_functions():
                result[f.name].append(fn.name)
        return result

    def get_files(self):
        self._initialize_files()
        return sorted(self.files.values(),key=lambda x:x.name)

    def has_single_file(self): return 0 in self.filenames

    # return file from single-file application
    def get_single_file(self):
        if 0 in self.filenames:
            return self.files[self.filenames[0]]
        else:
            tgtxnode = UF.get_targetfiles_xnode(self.path)
            filenames = [ c.get('name') for c in tgtxnode.findall('c-file') ]
            raise UF.CHCSingleCFileNotFoundError(filenames)

    def get_cfile(self):
        if self.singlefile: return self.get_single_file()

    def get_file(self,fname):
        self._initialize_files()
        index = self.get_file_index(fname)
        self._initialize_file(index,fname)
        if fname in self.files:
            return self.files[fname]

    def get_file_by_index(self,index):
        if index in self.filenames:
            return self.get_file(self.filenames[index])

    def get_file_index(self,fname):
        for i in self.filenames:
            if self.filenames[i] == fname: return i
            
    def get_srcfile(self,fname):
        srcfile = os.path.join(self.srcpath,fname)
        return CSrcFile(self,srcfile)

    # return a list of ((fid,vid),callsitespos).
    def get_callsites(self,fid,vid):
        self._initialize_callgraphs()
        if (fid,vid) in self.revcallgraph:
            return self.revcallgraph[(fid,vid)]
        return []

    def iter_files(self,f):
        for file in self.get_files(): f(file)

    def iter_files_parallel(self, f, processes):
        for fname in self.get_files():
            while(len(multiprocessing.active_children()) >= processes):
                pass

            multiprocessing.Process(target=f, args=(fname,)).start()

        while(len(multiprocessing.active_children()) > 0):
            pass

    def iter_filenames(self,f):
        for fname in self.filenames.values(): f(fname)
        
    def iter_filenames_parallel(self, f, processes):
        for fname in self.filenames.values(): 
            while(len(multiprocessing.active_children()) >= processes):
                pass

            multiprocessing.Process(target=f, args=(fname,)).start()
            
        while(len(multiprocessing.active_children()) > 0):
            pass

    def iter_functions(self,f):
        def g(fi): fi.iter_functions(f)
        self.iter_files(g)

    def iter_functions_parallel(self,f,maxprocesses):
        def g(fi): fi.iter_functions(f)
        self.iter_files_parallel(g,maxprocesses)

    def resolve_vid_function(self,fid,vid):
        msg = 'resolve-vid-function(' + str(fid) + ',' + str(vid) + '):'
        result = self.indexmanager.resolve_vid(fid,vid)
        if not result is None:
            tgtfid = result[0]
            tgtvid = result[1]
            if tgtfid in self.filenames:
                filename = self.filenames[tgtfid]
                self._initialize_file(tgtfid,filename)
                if not self.files[filename] is None:
                    return self.files[filename].get_function_by_index(tgtvid)
                logging.warning(msg + 'Filename not found: ' + filename)
                return None
            logging.warning(msg + 'Target fid ' + str(tgtfid) + ' not found')
            return None
        logging.warning(msg + 'Unable to resolve')

    def convert_vid(self,fidsrc,vid,fidtgt):
        return self.indexmanager.convert_vid(fidsrc,vid,fidtgt)

    def get_gckey(self,fid,ckey):
        return self.indexmanager.get_gckey(fid,ckey)
         
    def get_function_by_index(self,index):
        for f in self.files:
            if self.files[f].has_function_by_index(index):
                return self.files[f].get_function_by_index(index)
        else:
            print('No function found with index ' + str(index))
            # exit(1)

    def get_callinstrs(self):
        result = []
        def f(fi): result.extend(fi.getcallinstrs())
        self.iter_files(f)
        return result
        
    def get_externals(self):
        result = {}
        for e in self.xnode.find('global-definitions').find('external-varinfos'):
            vfile = e.get('vfile')
            vname = e.get('vname')
            summarized = e.get('summarized')
            if vfile not in result: result[vfile] = []
            result[vfile].append((vname,summarized))
        return result

    def get_compinfo(self,fileindex,ckey):
        return self.get_file_by_index(fileindex).get_compinfo(ckey)

    def get_global_compinfos(self):
        return self.declarations.compinfo_table.values()

    def get_file_compinfos(self):
        result = []
        def f(f):result.extend(f.declarations.getcompinfos())
        self.fileiter(f)
        return result

    def get_file_global_varinfos(self):
        result = []
        def f(f):result.extend(f.declarations.get_global_varinfos())
        self.fileiter(f)
        return result

    # ------------------- Application statistics -------------------------------
    def get_line_counts(self):
        counts = {}
        def f(cfile):
            decls = cfile.declarations
            counts[cfile.name] = (decls.get_max_line(),
                                      decls.get_code_line_count(),
                                      decls.get_function_count())
        self.iter_files(f)
        flen = self.get_max_filename_length()
        lines = []
        lines.append('file'.ljust(flen) + 'LOC'.rjust(12) + 'CLOC'.rjust(12)
                         + 'functions'.rjust(12))
        lines.append('-' * (flen + 36))
        for (c,(ml,mc,fc)) in sorted(counts.items()):
            lines.append(c.ljust(flen) + str(ml).rjust(12) + str(mc).rjust(12)
                             + str(fc).rjust(12))
        lines.append('-' * (flen + 36))
        mltotal = sum(x[0] for x in counts.values())
        mctotal = sum(x[1] for x in counts.values())
        fctotal = sum(x[2] for x in counts.values())
        lines.append('total'.ljust(flen) + str(mltotal).rjust(12)
                         + str(mctotal).rjust(12)
                         + str(fctotal).rjust(12))
        return '\n'.join(lines)

    def get_project_counts(self,filefilter=lambda f:True):
        linecounts = []
        clinecounts = []
        cfuncounts = []
        def f(cfile):
            if filefilter(cfile.name):
                decls = cfile.declarations
                linecounts.append(decls.get_max_line())
                clinecounts.append(decls.get_code_line_count())
                cfuncounts.append(decls.get_function_count())
        self.iter_files(f)
        return (sum(linecounts),sum(clinecounts),sum(cfuncounts))

    def update_spos(self):
        """Create supporting proof obligations for all call sites."""

        def f(fn):
            fn.update_spos()
            fn.save_spos()
            fn.save_pod()
        def h(cfile):
            cfile.iter_functions(f)
            cfile.save_predicate_dictionary()
            cfile.save_interface_dictionary()
            cfile.save_declarations()
        self.iter_files(h)

    def collect_post_assumes(self):
        """For all call sites collect postconditions from callee's contracts and add as assume."""

        self.iter_files(lambda f:f.collect_post_assumes())

    def distribute_post_guarantees(self):
        '''add callee postcondition guarantees to call sites as assumptions'''
        if self.contractpath is None: return              # no contracts provided
        def f(fn):
            fn.distribute_post_guarantees()
            fn.save_spos()
            fn.save_pod()
        def h(cfile):
            cfile.iter_functions(f)
            cfile.save_predicate_dictionary()
            cfile.save_interface_dictionary()
            cfile.save_declarations()
        self.iter_files(h)

    def reinitialize_tables(self):
        def f(fi):fi.reinitialize_tables()
        self.iter_files(f)
        
    # reload ppos after analyzer checks
    def reload_ppos(self):
        def f(fn):fn.reload_ppos()
        self.iter_functions(f)

    # reload spos after analyzer invariant generation and analyzer checks
    def reload_spos(self):
        def f(fn):fn.reload_spos()
        self.iter_functions(f)

    def get_contract_condition_violations(self):
        result = []
        def f(fn):
            if fn.violates_contract_conditions():
                result.append((fn.name,fn.get_contract_condition_violations()))
        self.iter_functions(f)
        return result

    def get_ppos(self):
        result = []
        def f(fn): result.extend(fn.get_ppos())
        self.iter_functions(f)
        return result

    def get_spos(self):
        result = []
        def f(fn): result.extend(fn.get_spos())
        self.iter_functions(f)
        return result

    def get_open_ppos(self):
        result = []
        def f(fn): result.extend(fn.get_open_ppos())
        self.iter_functions(f)
        return result

    def get_violations(self):
        result = []
        def f(fn): result.extend(fn.get_violations())
        self.iter_functions(f)
        return result

    def get_delegated(self):
        result = []
        def f(fn): result.extend(fn.get_delegated())
        self.iter_functions(f)
        return result

    def _initialize(self,fname):
        if fname is None:
            # read target_files.xml file to retrieve application files
            tgtxnode = UF.get_targetfiles_xnode(self.path)
            if self.includefiles is None:
                for c in tgtxnode.findall('c-file'):
                    if c.get('name') in self.excludefiles: continue
                    id = int(c.get('id'))
                    if id is None:
                        print('No id found for ' + c.get('name'))
                    else:
                        self.filenames[int(id)] = c.get('name')
            else:
                for c in tgtxnode.findall('c-file'):
                    if c.get('name') in self.includefiles:
                        id = int(c.get('id'))
                        if id is None:
                            print('No id found for ' + c.get('name'))
                        else:
                            self.filenames[int(id)] = c.get('name')
        else:
            self._initialize_file(0,fname)            

    def _initialize_files(self):
        for i,f in self.filenames.items(): self._initialize_file(i,f)

    def _initialize_file(self,index,fname):
        if fname in self.files:
            return

        cfile = UF.get_cfile_xnode(self.path,fname)
        if not cfile is None:
            self.filenames[index] = fname
            self.files[fname] = CFile(self,index,cfile)
            self.indexmanager.add_file(self.files[fname])
        else:
            tgtxnode = UF.get_targetfiles_xnode(self.path)
            filenames = [ c.get('name') for c in tgtxnode.findall('c-file') ]
            raise CFileNotFoundException(filenames)

    def _initialize_callgraphs(self):
        if len(self.callgraph) > 0: return
        def collectcallers(fn):
            fid = fn.cfile.index
            vid = fn.svar.get_vid()
            def g(cs):
                if cs.callee is None: return
                fundef = self.indexmanager.resolve_vid(fid,cs.callee.get_vid())
                if not fundef is None:
                    if not (fid,vid) in self.callgraph:
                        self.callgraph[(fid,vid)] = []
                    self.callgraph[(fid,vid)].append((cs,fundef))
            fn.iter_callsites(g)
        self.iter_functions(collectcallers)

        for s in self.callgraph:
            for (cs,t) in self.callgraph[s]:
                if not t in self.revcallgraph: self.revcallgraph[t] = []
                self.revcallgraph[t].append((s,cs))
		

        
