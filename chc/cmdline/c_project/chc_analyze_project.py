# ------------------------------------------------------------------------------
# Script to run analysis on a full application
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
"""Analyzes a c application."""

import argparse
import logging
import time
import os
import subprocess

from contextlib import contextmanager

import chc.reporting.ProofObligations as RP
import chc.util.fileutil as UF

from chc.util.Config import Config
from chc.app.CApplication import CApplication
from chc.linker.CLinker import CLinker

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.util.IndexedTable import IndexedTableError

def parse():
    usage = ('\nCall with the directory that holds the semantics files\n\n')
    parser = argparse.ArgumentParser(usage=usage,description=__doc__)
    parser.add_argument('path',
                            help=('directory that holds the semantics directory (or tar.gz file)'
                                      + ' or the name of a test application'))
    parser.add_argument('--maxprocesses',
                            help='number of files to process in parallel',
                            type=int,
                            default=1)
    parser.add_argument('--wordsize',
                            help='architecture word size (default 32)',
                            type=int,
                            default=32)
    parser.add_argument('--verbose',
                            help='Print all output from analyzer to console',
                            action='store_true')
    parser.add_argument('--deletesemantics',
                            help='Unpack a fresh version of the semantics files',
                            action='store_true')
    parser.add_argument('--analysisrounds',
                            help='Number of times to create supporting proof obligations',
                            type=int, default=2)
    parser.add_argument('--contractpath',help='path to contract files to be used in analysis')
    parser.add_argument('--candidate_contractpath',
                            help='path to contract files to collect suggestions for conditions')
    parser.add_argument('--logging',help='log level msgs to be recorded (default=WARNING)',
                            default='WARNING',
                            choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    parser.add_argument('--logfilename',help='name of file to collect log messages',
                            default=None)
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
        UF.check_analyzer()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if args.logging is None:
        loglevel = logging.WARNING
    else:
        if args.logging == 'DEBUG': loglevel = logging.DEBUG
        elif args.logging == 'INFO': loglevel = logging.INFO
        elif args.logging == 'WARNING': loglevel = logging.WARNING
        elif args.logging == 'ERROR': loglevel = logging.ERROR
        elif args.logging == 'CRITICAL': loglevel = logging.CRITICAL

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_semantics(cpath,deletesemantics=args.deletesemantics)
        sempath = os.path.join(cpath,'semantics')
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    logfilename = os.path.join(cpath,'chclogfile.txt')
    
    logging.basicConfig(filename=logfilename,level=loglevel)
        
    if args.contractpath is None:
        contractpath = os.path.join(cpath,'chc_contracts')
    else:
        contractpath = args.contractpath

    # check linkinfo
    globaldefs = os.path.join(sempath,os.path.join('ktadvance','globaldefinitions.xml'))
    if not os.path.isfile(globaldefs):
        capp = CApplication(sempath,contractpath=contractpath)
        linker = CLinker(capp)
        linker.link_compinfos()
        linker.link_varinfos()
        capp.iter_files(save_xrefs)

        linker.save_global_compinfos()
        
    # have to reinitialize capp to get linking info properly initialized
    capp = CApplication(sempath,contractpath=contractpath,
                            candidate_contractpath=args.candidate_contractpath)
    am = AnalysisManager(capp,verbose=args.verbose,wordsize=args.wordsize)

    with timing('analysis'):

        am.create_app_primary_proofobligations(processes=args.maxprocesses)
        try:
            capp.collect_post_assumes()
            capp.reinitialize_tables()
            capp.update_spos()
        except UF.CHCError as e:
            print(str(e.wrap()))
            exit(1)

        for i in range(1):
            am.generate_and_check_app('vllrisp', processes=args.maxprocesses)
            capp.reinitialize_tables()
            capp.update_spos()

        for i in range(args.analysisrounds):
            capp.update_spos()
            am.generate_and_check_app('vllrisp', processes=args.maxprocesses)
            capp.reinitialize_tables()

    timestamp = os.stat(capp.path).st_ctime
    try:
        result = RP.project_proofobligation_stats_to_dict(capp)
        result['timestamp'] = timestamp
        result['project'] = cpath
        UF.save_project_summary_results(cpath,result)
        UF.save_project_summary_results_as_xml(cpath, result)
    except IndexedTableError as e:
        print(
            '\n' + ('*' * 80) + '\nThe analysis results format has changed'
            + '\nYou may have to re-run the analysis first: '
            + '\n' + e.msg
            + '\n' + ('*' * 80))
