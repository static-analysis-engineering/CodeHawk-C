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

import json
import os
import shutil

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

class FileParseError(UF.CHCError):
    
    def __init__(self,msg):
        UF.CHCError.__init__(self,msg)

class XmlFileNotFoundError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class FunctionPPOError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class FunctionSPOError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class FunctionPEVError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class FunctionSEVError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class AnalyzerMissingError(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.util.Config import Config
from chc.cmdline.ParseManager import ParseManager
from chc.cmdline.kendra.TestResults import TestResults
from chc.cmdline.kendra.TestSetRef import TestSetRef

class TestManager(object):
    """Provide utility functions to support regression and platform tests.

    Args:
        cpath: directory that holds the source code
        tgtpath: directory that holds the chc artifacts directory
        testname: name of the test directory
        saveref: adds missing ppos to functions in the json spec file and 
                 overwrites the json file with the result
    """

    def __init__(self,cpath,tgtpath,testname,saveref=False,verbose=True):
        self.cpath = cpath
        self.tgtpath = tgtpath
        self.saveref = saveref
        self.config = Config()
        self.ismac = self.config.platform == 'macOS'
        self.verbose = verbose
        self.sempath = os.path.join(self.cpath,'semantics')
        self.contractpath = os.path.join(self.cpath,'chccontracts')
        testfilename = os.path.join(self.cpath,testname + '.json')
        self.testsetref = TestSetRef(testfilename)
        self.testresults = TestResults(self.testsetref)

    def get_test_results(self): return self.testresults

    def print_test_results(self): print(str(self.testresults))

    def print_test_results_summary(self): print(str(self.testresults.get_summary()))

    def print_test_results_line_summary(self): print(str(self.testresults.get_line_summary()))
 
    def test_parser(self,savesemantics=False):
        """Parse the source code and optionally save the semantics files in a tar file.

        Check if the required semantic artifacts are produced for all files and functions.

        Note: if the test set is labeled as linux-only and this is run on a mac, no 
            parsing is performed.
        """

        if self.ismac and self.testsetref.is_linux_only():
            if UF.unpack_tar_file(self.cpath,deletesemantics=True):
                self.sempath = os.path.join(self.tgtpath,'semantics')
                self.tgtxpath = UF.get_chc_artifacts_path(self.sempath)
                self.tgtspath = os.path.join(self.sempath,'sourcefiles')   # for .c and .i files
                return True
            else:
                return False
        
        self.parsemanager = ParseManager(self.cpath,self.tgtpath,verbose=self.verbose)
        self.sempath = self.parsemanager.sempath
        self.tgtxpath = self.parsemanager.tgtxpath
        self.tgtspath = self.parsemanager.tgtspath
        self.testresults.set_parsing()
        self.clean()
        self.parsemanager.initialize_paths()
        if self.verbose: print('\nParsing files\n' + ('-' * 80))
        for cfile in self.get_cref_files():
            cfilename = cfile.name
            ifilename = self.parsemanager.preprocess_file_with_gcc(cfilename,copyfiles=True)
            parseresult = self.parsemanager.parse_ifile(ifilename)
            if parseresult != 0:
                self.testresults.add_parse_error(cfilename,str(parseresult))
                raise FileParseError(cfilename)
            self.testresults.add_parse_success(cfilename)
            if self.xcfile_exists(cfilename):
                self.testresults.add_xcfile_success(cfilename)
            else:
                self.testresults.add_xcfile_error(cfilename)
                raise FileParseError(cfilename)
            for fname in cfile.get_functionnames():
                if self.xffile_exists(cfilename,fname):
                    self.testresults.add_xffile_success(cfilename,fname)
                else:
                    self.testresults.add_xffile_error(cfilename,fname)
                    raise FileParseError(cfilename)
        if savesemantics:
            self.parsemanager.save_semantics()
        return True

    def check_ppos(self,cfilename,cfun,ppos,refppos):
        """Check if all required primary proof obligations are created."""

        d = {}
        # collect ppos produced
        for ppo in ppos:
            context = ppo.get_context_strings()
            if not context in d: d[context] = []
            d[context].append(ppo.get_predicate_tag())

        # compare with reference ppos
        for ppo in refppos:
            p = ppo.get_predicate()
            context = ppo.get_context_string()
            if not context in d:
                self.testresults.add_missing_ppo(cfilename,cfun,context,p)
                for c in d:
                    if self.verbose:
                        print(str(c))
                        print('Did not find ' + str(context))
                raise FunctionPPOError(cfilename + ':' + cfun + ':'
                                           + ' Missing ppo: ' + str(context))
            else:
                if not p in d[context]:
                    self.testresults.add_missing_ppo(cfilename,cfun,context,p)
                    raise FunctionPPOError(
                        cfilename + ':' + cfun + ':' + str(context) + ':' + p)

    def create_reference_ppos(self,cfilename,fname,ppos):
        """Create reference ppos from actual analysis results."""

        result = []
        for ppo in ppos:
            ctxt = ppo.context
            d = {}
            d['line'] = ppo.get_line()
            d['cfgctxt'] = str(ctxt.get_cfg_context())
            d['expctxt'] = str(ctxt.get_exp_context())
            d['predicate'] = ppo.get_predicate_tag()
            d['tgtstatus'] = 'open'
            d['status'] = 'open'
            result.append(d)
        self.testsetref.set_ppos(cfilename,fname,result)

    def create_reference_spos(self,cfilename,fname,spos):
        """Create reference spos from actual analysis results."""

        result = []
        if len(spos) > 0:
            for spo in spos:
                d = {}
                d['line'] = spo.get_line()
                d['cfgctxt'] = spo.get_cfg_contextstring()
                d['tgtstatus'] = 'unknown'
                d['status'] = 'unknown'
                result.append(d)
            self.testsetref.set_spos(cfilename,fname,result)

    def test_ppos(self):
        """Create primary proof obligations and check if created as expected."""

        if not os.path.isfile(self.config.canalyzer):
            raise AnalyzerMissingError(self.config.canalyzer)
        self.testresults.set_ppos()
        saved = False
        try:
            for creffile in self.get_cref_files():
                creffilename = creffile.name
                creffilefilename = UF.get_cfile_filename(self.tgtxpath,creffilename)
                if not os.path.isfile(creffilefilename):
                    raise XmlFileNotFoundError(creffilefilename)
                capp = CApplication(self.sempath,cfilename=creffilename,
                                        contractpath=self.contractpath)
                am = AnalysisManager(capp,verbose=self.verbose)
                am.create_file_primary_proofobligations(creffilename)
                cfile = capp.get_single_file()
                capp.collect_post_assumes()
                ppos = cfile.get_ppos()
                for creffun in creffile.get_functions():
                    fname = creffun.name
                    cfun = cfile.get_function_by_name(fname)
                    if self.saveref:
                        if creffun.has_ppos():
                            print('Ppos not created for ' + fname + ' (delete first)')
                        else:
                            self.create_reference_ppos(creffilename,fname,cfun.get_ppos())
                            saved = True
                    else:
                        refppos = creffun.get_ppos()
                        funppos = [ ppo for ppo in ppos if ppo.cfun.name == fname ]
                        if len(refppos) == len(funppos):
                            self.testresults.add_ppo_count_success(creffilename,fname)
                            self.check_ppos(creffilename,fname,funppos,refppos)
                        else:
                            self.testresults.add_ppo_count_error(
                                creffilename,fname,len(funppos),len(refppos))
                            raise FunctionPPOError(creffilename + ':' + fname)
        except FunctionPPOError as detail:
            self.print_test_results()
            print('Function PPO error: ' + str(detail))
            exit()
        if self.saveref and saved:
            self.testsetref.save()
            exit()

    def check_spos(self,cfilename,cfun,spos,refspos):
        """Check if spos created match reference spos."""

        d = {}
        # collect spos produced
        for spo in spos:
            context = spo.cfg_context_string
            if not context in d: d[context] = []
            d[context].append(spo.predicatetag)

        # compare with reference spos
        for spo in refspos:
            context = spo.get_context()
            if not context in d:
                p = spo.get_predicate()
                self.testresults.add_missing_spo(cfilename,cfun,context,p)
                for c in d:
                    if self.verbose: print(str(c))
                raise FunctionSPOError(cfilename + ':' + cfun + ':' + ' Missing spo: '
                                           + str(context) + ' (' + str(d) + ')')
            else:
                p = spo.get_predicate()
                if not p in d[context]:
                    self.testresults.add_missing_spo(cfilename,cfun,context,p)
                    raise FunctionSPOError(
                        cfilename + ':' + cfun + ':' + str(context) + ':'
                        + p + str(d[context]))

    def test_spos(self,delaytest=False):
        """Run analysis and check if all expected spos are created."""

        try:
            for creffile in self.get_cref_files():
                self.testresults.set_spos()
                cfilename = creffile.name
                cfilefilename = UF.get_cfile_filename(self.tgtxpath,cfilename)
                if not os.path.isfile(cfilefilename):
                    raise XmlFileNotFoundError(xfilefilename)
                capp = CApplication(self.sempath,cfilename=cfilename,
                                        contractpath=self.contractpath)
                cappfile = capp.get_single_file()
                capp.update_spos()
                capp.collect_post_assumes()
                spos = cappfile.get_spos()
                if delaytest: continue
                for cfun in creffile.get_functions():
                    fname = cfun.name
                    if self.saveref:
                        if cfun.has_spos():
                            print('Spos not created for ' + fname + ' in ' + cfilename +
                                      ' (delete first)')
                        else:
                            self.create_reference_spos(cfilename,fname,spos[fname])
                    else:
                        refspos = cfun.get_spos()
                        funspos = [ spo for spo in spos if spo.cfun.name == fname ]
                        if funspos is None and len(refspos) == 0:
                            self.testresults.add_spo_count_success(cfilename,fname)
                            
                        elif len(refspos) == len(funspos):
                            self.testresults.add_spo_count_success(cfilename,fname)
                            self.check_spos(cfilename,fname,funspos,refspos)
                        else:
                            self.testresults.add_spo_count_error(
                                cfilename,fname,len(funspos),len(refspos))
                            raise FunctionSPOError(cfilename + ':' + fname
                                                       + ' (' + str(len(funspos)) + ')')
        except FunctionSPOError as detail:
            self.print_test_results()
            print('')
            print('*' * 80)
            print('Function SPO error: ' + str(detail))
            print('*' * 80)
            exit()
        if self.saveref:
            self.testsetref.save()
            exit()

    def check_ppo_proofs(self,cfilename,cfun,funppos,refppos):
        """Check if ppo analysis results match the expected results."""

        d = {}
        fname = cfun.name
        # collect actual analysis results
        for ppo in funppos:
            context = ppo.get_context_strings()
            if not context in d: d[context] = {}
            p = ppo.get_predicate_tag()
            if p in d[context]:
                raise FunctionPEVError(
                    cfilename + ':' + fname + ':' + str(context) + ': ' +
                    'multiple instances of ' + p)
            else:
                status = ppo.status
                if ppo.is_delegated(): status += ':delegated'
                d[context][p] = status

        # compare with reference results
        for ppo in refppos:
            context = ppo.get_context_string()
            p = ppo.get_predicate()
            if not context in d:
                raise FunctionPEVError(
                    cfilename + ':' + fname + ':' + str(context) + ': missing')
            else:
                if ppo.get_status() != d[context][p]:
                    self.testresults.add_pev_discrepancy(
                        cfilename,cfun,ppo,d[context][p])

    def test_ppo_proofs(self,delaytest=False):
        """Run analysis and check if analysis results match expected results.

        Skip checking results if delaytest is true.
        """

        if not os.path.isfile(self.config.canalyzer):
            raise AnalyzerMissingError(self.config.canalyzer)
        
        self.testresults.set_pevs()
        for creffile in self.get_cref_files():
            cfilename = creffile.name
            cfilefilename = UF.get_cfile_filename(self.tgtxpath,cfilename)
            if not os.path.isfile(cfilefilename):
                raise XmlFileNotFoundError(cfilefilename)
            capp = CApplication(self.sempath,cfilename=cfilename,contractpath=self.contractpath)
            cfile = capp.get_single_file()
            # only generate invariants if required
            if creffile.has_domains():
                for d in creffile.get_domains():
                    am = AnalysisManager(capp,verbose=self.verbose)
                    am.generate_and_check_file(cfilename,d)
            cfile.reinitialize_tables()
            ppos = cfile.get_ppos()
            if delaytest: continue
            for cfun in creffile.get_functions():
                fname = cfun.name
                funppos = [ ppo for ppo in ppos if ppo.cfun.name == fname ]
                refppos = cfun.get_ppos()
                self.check_ppo_proofs(cfilename,cfun,funppos,refppos)

    def check_spo_proofs(self,cfilename,cfun,funspos,refspos):
        """Check if spo analysis results match the expected results."""

        d = {}
        fname = cfun.name
        for spo in funspos:
            context = spo.cfg_context_string
            if not context in d: d[context] = {}
            p = spo.predicatetag
            if p in d[context]:
                raise FunctionSEVError(
                    cfilename + ':' + fname + ':' + str(context) + ': ' +
                    'multiple instances of ' + p)
            else:
                status = spo.status
                if spo.is_delegated() : status = status + ':delegated'
                d[context][p] = status
        for spo in refspos:
            context = spo.get_context()
            p = spo.get_predicate()
            if not context in d:
                raise FunctionSEVError(
                    cfilename + ':' + fname + ':' + str(context) + ': missing')
            else:
                if spo.get_status() != d[context][p]:
                    self.testresults.add_sev_discrepancy(
                        cfilename,cfun,spo,d[context][p])
                    
    def test_spo_proofs(self,delaytest=False):
        """Run analysis and check if the analysis results match the expected results.

        Skip the checking if delaytest is True.
        """

        self.testresults.set_sevs()
        for creffile in self.get_cref_files():
            creffilename = creffile.name
            cfilefilename = UF.get_cfile_filename(self.tgtxpath,creffilename)
            if not os.path.isfile(cfilefilename):
                raise XmlFileNotFoundError(cfilefilename)
            capp = CApplication(self.sempath,cfilename=creffilename,
                                    contractpath=self.contractpath)
            cappfile = capp.get_single_file()
            if creffile.has_domains():
                for d in creffile.get_domains():
                    am = AnalysisManager(capp,verbose=self.verbose)
                    am.generate_and_check_file(creffilename,d)
            cappfile.reinitialize_tables()
            spos = cappfile.get_spos()
            if delaytest: continue
            for cfun in creffile.get_functions():
                fname = cfun.name
                funspos = [ spo for spo in spos if spo.cfun.name == fname ]
                refspos = cfun.get_spos()
                self.check_spo_proofs(creffilename,cfun,funspos,refspos)
                    

    def get_cref_filenames(self): return self.testsetref.get_cfilenames()

    def get_cref_files(self): return self.testsetref.get_cfiles()

    def get_cref_file(self,cfilename): self.testsetref.get_cfile(cfilename)

    def clean(self):
        """Remove semantics directory and .i files."""

        for cfilename in self.get_cref_filenames():
            cfilename = os.path.join(self.cpath,cfilename)[:-2] + '.i'
            if os.path.isfile(cfilename):
                if self.verbose: print('Removing ' + cfilename)
                os.remove(cfilename)
        if os.path.isdir(self.sempath):
            if self.verbose: print('Removing ' + self.sempath)
            shutil.rmtree(self.sempath)

    def xcfile_exists(self,cfilename):
        """Checks existence of xml file for cfilename."""
        xfilename = UF.get_cfile_filename(self.tgtxpath,cfilename)
        return os.path.isfile(xfilename)

    def xffile_exists(self,cfilename,funname):
        """Checks existence of xml file for function funname in cfilename."""
        xfilename = UF.get_cfun_filename(self.tgtxpath,cfilename,funname)
        return os.path.isfile(xfilename)

        
