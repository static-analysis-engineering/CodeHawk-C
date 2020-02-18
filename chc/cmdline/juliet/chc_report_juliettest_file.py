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
import chc.reporting.ProofObligations as RP

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('cwe',help='name of cwe, e.g., CWE121')
    parser.add_argument('test',help='name of test case, e.g., CWE129_large')
    parser.add_argument('cfile',help='name of juliet c file (.e.g., x01.c)')
    parser.add_argument('--showcode',help='show proof obligations on code for entire file',
                            action='store_true')
    parser.add_argument('--open',help='show only proof obligions on code that are still open',
                            action='store_true')
    parser.add_argument('--showinvariants',help='show invariants for open proof obligations',
                            action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    try:
        cpath = UF.get_juliet_testpath(args.cwe,args.test)
        UF.check_analysis_results(cpath)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')

    try:        
        cfapp = CApplication(sempath,args.cfile)
        cfile = cfapp.get_cfile()
    except UF.CFileNotFoundException as e:
        print(str(e))
        exit(1)

    dc = [ 'deadcode' ]

    if args.showcode:
        if args.open:
            print(RP.file_code_open_tostring(cfile,showinvs=args.showinvariants))
        else:
            print(RP.file_code_tostring(cfile,showinvs=args.showinvariants))

    print(RP.file_proofobligation_stats_tostring(cfile,extradsmethods=dc))
                      
