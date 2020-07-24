#!/usr/bin/env python
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

import argparse
import logging
import time
import os

from contextlib import contextmanager

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication
from chc.cmdline.AnalysisManager import AnalysisManager

def parse():
    usage = ('\nCall with the name of the directory that holds the semantics directory and\n' +
                 'the name of the c file.\n\n' +
                 '  Example: python chc_analyze_file.py ../../tests/sard/kendra/id115Q id115.c\n\n')
    description = ('Analyzes the semantics files for the given c source code file. It expects\n' +
                       'that the file has already been parsed and that the semantics files are\n' +
                       'available either in a subdirectory of the passed in path, called\n' +
                       'semantics, or in a (gzipped) tar file semantics_linux.tar.gz or \n' +
                       'semantics_linux.tar (or semantics_mac.tar.gz/semantics_mac.tar resp.)')
    parser = argparse.ArgumentParser(usage=usage,description=description)
    parser.add_argument('path',help='directory that holds the semantics directory for the c file')
    parser.add_argument('cfile',help='c filename')
    parser.add_argument('--continueanalysis',help='continue with existing results',action='store_true')
    parser.add_argument('--deletesemantics',
                            help='Unpack a fresh version of the semantics files',
                            action='store_true')
    parser.add_argument('--wordsize',help='wordsize of target platform (e.g. 32 or 64)',
                            type=int,default=32)
    parser.add_argument('--analysisrounds',type=int,default=3,
                            help='number of times to generate secondary proof obligations')
    parser.add_argument('--verbose',help='print out intermediate results',
                            action='store_true')
    parser.add_argument('--contractpath',help='path to contract files',default=None)
    parser.add_argument('--unreachability',help='use unreachability to discharge proof obligations',
                            action='store_true')
    parser.add_argument('--thirdpartysummaries',help='use 3rd party summaries',nargs='*')
    args = parser.parse_args()
    return args

@contextmanager
def timing(activity):
    t0 = time.time()
    yield
    print('\n' + ('=' * 80) + 
          '\nCompleted ' + activity + ' in ' + str(time.time() - t0) + ' secs' +
          '\n' + ('=' * 80))

if __name__ == '__main__':

    logging.basicConfig(filename='chc_log.log',level=logging.WARNING)
    
    args = parse()
    cpath = os.path.abspath(args.path)
    try:
        cpath = UF.get_project_path(args.path)
        UF.check_cfile(args.path,args.cfile)
        UF.check_semantics(cpath,deletesemantics=args.deletesemantics)       
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')

    if args.contractpath is None:
        contractpath = os.path.join(cpath,'chc_contracts')
    else:
        contractpath = args.contractpath    

    capp = CApplication(sempath,args.cfile,contractpath=contractpath)
    chcpath = capp.path

    try:
        xfilename = UF.get_cfile_filename(chcpath,args.cfile)
        UF.check_cfile(chcpath,xfilename)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)
    
    am = AnalysisManager(capp,wordsize=int(args.wordsize),verbose=args.verbose,
                             unreachability=args.unreachability,
                             thirdpartysummaries=args.thirdpartysummaries)

    cfilename = args.cfile

    if args.continueanalysis is None or (not args.continueanalysis):
        am.create_file_primary_proofobligations(cfilename)
        am.reset_tables(cfilename)
        capp.collect_post_assumes()

    am.generate_and_check_file(cfilename,'llrvisp')
    am.reset_tables(cfilename)
    capp.collect_post_assumes()

    for k in range(args.analysisrounds):
        capp.update_spos()
        am.generate_and_check_file(cfilename,'llrvisp')
        am.reset_tables(cfilename)


