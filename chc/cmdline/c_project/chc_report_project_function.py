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
import os

import chc.util.fileutil as UF

from chc.util.IndexedTable import IndexedTableError

import chc.reporting.ProofObligations as RP

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help=('directory that holds the semantics files'
                                         + ' or the name of a test application'))
    parser.add_argument('cfile',help='name of c file that is part of the project')
    parser.add_argument('cfunction',help='name of function in c file')
    parser.add_argument('--list_test_applications',
                            help='list names of test applications provided',
                            action='store_true')
    parser.add_argument('--open',help='only show open proof obligations',action='store_true')
    parser.add_argument('--predicate',help='only show proof obligations of this type')
    parser.add_argument('--showinvs',help='show context invariants',action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_analysis_results(cpath)        
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')
    try:
        cfapp = CApplication(sempath,args.cfile)
        cfile = cfapp.get_cfile()
    except UF.CFileNotFoundException as e:
        print(e)
        exit(0)

    if not cfile.has_function_by_name(args.cfunction):
        lines = []
        lines.append('*' * 80)
        lines.append(('Function ' + args.cfunction + ' not found in file '
                          + cfile.name + '; function names available:'))
        lines.append('-' * 80)
        for n in cfile.functionnames:
            lines.append('  ' + n)
        lines.append('*' * 80)
        print('\n'.join(lines))
        exit(0)

    cfunction = cfile.get_function_by_name(args.cfunction)

    try:

        if args.open:
            print(RP.function_code_open_tostring(cfunction))
        elif args.predicate:
            print(RP.function_code_predicate_tostring(cfunction,args.predicate,showinvs=args.showinvs))
        else:
            print(RP.function_code_tostring(cfunction,showinvs=args.showinvs))

        print(RP.function_proofobligation_stats_tostring(cfunction))

    except IndexedTableError as e:
        print(
            '\n' + ('*' * 80) + '\nThe analysis results format has changed'
            + '\nYou may have to re-run the analysis first: '
            + '\n' + e.msg
            + '\n' + ('*' * 80))
    

