# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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
"""Analyzes all variants of a Juliet  test case."""

import argparse
import logging
import os
import time

from contextlib import contextmanager

import chc.reporting.ProofObligations as RP
import chc.util.fileutil as UF

from chc.app.CApplication import CApplication
from chc.cmdline.AnalysisManager import AnalysisManager
from chc.util.Config import Config
from chc.util.IndexedTable import IndexedTableError
from chc.linker.CLinker import CLinker

def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cwe',help='name of cwe, e.g., CWE121')
    parser.add_argument('test',help='name of test case, e.g., CWE129_large')
    parser.add_argument('--maxprocesses','-m',
                            help='number of files to process in parallel',
                            type=int, default=1)
    parser.add_argument('--analysisrounds',
                            help='Number of times to generate supporting proof obligations',
                            type=int,default=5)
    parser.add_argument('--wordsize',
                            help='architecture word size in bits',
                            type=int,
                            default=64)
    parser.add_argument('--contractpath',help='path to save the contracts file',default=None)
    args = parser.parse_args()
    return args

@contextmanager
def timing(activity):
    t0 = time.time()
    yield
    print('\n' + ('=' * 80) + 
          '\nCompleted ' + activity + ' in ' + str(time.time() - t0) + ' secs' +
          '\n' + ('=' * 80))

def save_xrefs(f):
    capp.indexmanager.save_xrefs(capp.path,f.name,f.index)

if __name__ == '__main__':

    args = parse()
    try:
        cpath = UF.get_juliet_testpath(args.cwe,args.test)
        UF.check_semantics(cpath,deletesemantics=True)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    logfilename = os.path.join(cpath,'chc_logfile.txt')    
    logging.basicConfig(filename=logfilename,level=logging.WARNING)

    sempath = os.path.join(cpath,'semantics')

    excludefiles = [ 'io.c', 'main_linux.c', 'std_thread.c' ]        

    capp = CApplication(sempath,excludefiles=excludefiles)
    linker = CLinker(capp)
    linker.link_compinfos()
    linker.link_varinfos()
    capp.iter_files(save_xrefs)
    linker.save_global_compinfos()

    if args.contractpath is None:
        contractpath = os.path.join(cpath,'chc_contracts')
    else:
        contractpath = args.contractpath

    # have to reinitialize capp to get linking info properly initialized

    capp = CApplication(sempath,contractpath=contractpath,excludefiles=excludefiles)

    # assume wordsize of 64
    # use unreachability as a means of proof obligation discharge
    am = AnalysisManager(capp,wordsize=args.wordsize,unreachability=True,
                             thirdpartysummaries=[UF.get_juliet_summaries()])

    with timing('analysis of ' + args.cwe + ' - ' + args.test):

        try:
            am.create_app_primary_proofobligations(processes=args.maxprocesses)
            capp.collect_post_assumes()
        except UF.CHCError as e:
            print(str(e.wrap()))
            exit(1)

        for i in range(1):
            am.generate_and_check_app('llrvisp',processes=args.maxprocesses)
            capp.reinitialize_tables()
            capp.update_spos()

        for i in range(5):
            capp.update_spos()
            am.generate_and_check_app('llrvisp',processes=args.maxprocesses)
            capp.reinitialize_tables()

    def filefilter(filename):
        return (not (filename in  [ "io", "main_linux", "std_thread" ]))

    with timing('summarize'):

        contractviolations = capp.get_contract_condition_violations()
        if len(contractviolations) > 0:
            print(' --> ' + str(len(contractviolations)) + ' contract violations in ' + args.path)
        
        timestamp = os.stat(capp.path).st_ctime
        try:
            result = RP.project_proofobligation_stats_to_dict(capp,filefilter=filefilter)
            result['timestamp'] = timestamp
            result['project'] = cpath
            UF.save_project_summary_results(cpath,result)
        except IndexedTableError as e:
            print(
                '\n' + ('*' * 80) + '\nThe analysis results format has changed'
                + '\nYou may have to re-run the analysis first: '
                + '\n' + e.msg
                + '\n' + ('*' * 80))

