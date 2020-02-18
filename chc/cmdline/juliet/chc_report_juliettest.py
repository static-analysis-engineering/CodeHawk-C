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

    excludefiles = [ 'io.c', 'main_linux.c', 'std_thread.c' ]

    summary = UF.read_project_summary_results(cpath)
    if not summary  is None:
        print(RP.project_proofobligation_stats_dict_to_string(summary))
        exit(0)

    capp = CApplication(sempath,excludefiles=excludefiles)

    filterout = [ 'io', 'main_linux', 'std_thread' ]
    dc = [ 'deadcode' ]
    def filefilter(f): return (not f in filterout)

    print(RP.project_proofobligation_stats_tostring(capp,extradsmethods=dc,filefilter=filefilter))

    contract_condition_violations = capp.get_contract_condition_violations()
    
    if len(contract_condition_violations) > 0:
        print('=' * 80)
        print(str(len(contract_condition_violations)) + ' CONTRACT CONDITION FAILURES')
        print('=' * 80)
        for (fn,cc) in contract_condition_violations:
            print(fn + ':')
            for (name,desc) in cc:
                print('   ' + name + ':' + desc)
        print('=' * 80)

