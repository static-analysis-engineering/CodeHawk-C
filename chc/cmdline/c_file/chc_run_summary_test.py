#!/usr/bin/env python
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
"""Script to parse, analyze, and report the results of a library summary test file."""

import argparse
import json
import os
import shutil

import chc.util.fileutil as UF
import chc.reporting.ProofObligations as RP

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.app.CApplication import CApplication
from chc.util.Config import Config
from chc.cmdline.ParseManager import ParseManager


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('header',help='name of header file, e.g., time')
    parser.add_argument('function',help='name of function, e.g., localtime')
    parser.add_argument('--verbose',help='show intermediate results during analysis',
                            action='store_true')
    parser.add_argument('--showcode',help='show proof obligations and results on code',
                            action='store_true')
    parser.add_argument('--open',help='only show open proof obligations on code',
                            action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()

    try:
        UF.check_parser()
        (cpath,cfilename) = UF.get_libc_summary_test(args.header,args.function)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    # --------------------------------------------------------------- parsing ---

    parsemanager = ParseManager(cpath,cpath)
    parsemanager.initialize_paths()

    os.chdir(cpath)
    if os.path.isdir('semantics'):
        print('Removing semantics directory')
        shutil.rmtree('semantics')

    try:
        basename = os.path.basename(cfilename)
        ifilename = parsemanager.preprocess_file_with_gcc(basename)
        result = parsemanager.parse_ifile(ifilename)
        if result != 0:
            print('*' * 80)
            print('Error in parsing ' + cfilename)
            print('*' * 80)
            exit(1)
    except OSError as e:
        print('OSError while parsing file: ' + str(e))
        exit(1)

    # ------------------------------------------------------------- analysis ---  

    sempath = os.path.join(cpath,'semantics')

    capp = CApplication(sempath,cfilename)

    am = AnalysisManager(capp,verbose=args.verbose)

    am.create_file_primary_proofobligations(cfilename)
    am.reset_tables(cfilename)
    capp.collect_post_assumes()

    am.generate_and_check_file(cfilename,'llrvisp')
    am.reset_tables(cfilename)
    capp.collect_post_assumes()

    for k in range(0,5):
        capp.update_spos()
        am.generate_and_check_file(cfilename,'llrvisp')
        am.reset_tables(cfilename)

    # ------------------------------------------------------------ reporting ---

    cfile = capp.get_cfile()

    if args.showcode:
        if args.open:
            def pofilter(po):return not po.is_closed()
        else:
            def pofilter(po):return True
        print(RP.file_code_tostring(cfile,pofilter=pofilter,showinvs=True))

    print(RP.file_proofobligation_stats_tostring(cfile))
