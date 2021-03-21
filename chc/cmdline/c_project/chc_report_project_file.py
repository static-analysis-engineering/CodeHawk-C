# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2018 Kestrel Technology LLC
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
import os

import chc.util.fileutil as UF
import chc.reporting.ProofObligations as RP

from chc.util.Config import Config
from chc.app.CApplication import CApplication

from chc.util.IndexedTable import IndexedTableError


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help=('directory that holds the semantics directory'
                                         + ' or the name of a test application'))
    parser.add_argument('cfile',help='name of c file that is part of the project')
    parser.add_argument('--showcode',help='show proof obligations on code for entire file',
                            action='store_true')
    parser.add_argument('--open',help=('show only proof obligions on code that are still open'
                                           + ' or that indicate a violation'),
                            action='store_true')
    parser.add_argument('--showinvs',help='show context invariants',action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    config = Config()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_analysis_results(cpath)        
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')
    if not os.path.isdir(sempath):
        print('semantics_not_found_err_msg: ' + cpath)
        exit(1)

    try:
        cfapp = CApplication(sempath,args.cfile)
        cfile = cfapp.get_cfile()
    except UF.CFileNotFoundException as e:
        print(str(e.wrap()))
        exit(0)

    try:
        if args.showcode:
            if args.open:
                print(RP.file_code_open_tostring(cfile,showinvs=args.showinvs))
            else:
                print(RP.file_code_tostring(cfile))

        print(RP.file_proofobligation_stats_tostring(cfile))
    except IndexedTableError as e:
        print(
            '\n' + ('*' * 80) + '\nThe analysis results format has changed'
            + '\nYou may have to re-run the analysis first: '
            + '\n' + e.msg
            + '\n' + ('*' * 80))

        
