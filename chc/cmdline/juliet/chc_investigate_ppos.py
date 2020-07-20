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

from chc.app.CApplication import CApplication
import chc.reporting.ProofObligations as RP

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('cwe',help='name of cwe, e.g., CWE121')
    parser.add_argument('test',help='name of test case, e.g., CWE129_large')
    parser.add_argument('--xdelegated',help="exclude delegated ppo's",
                            action='store_true')
    parser.add_argument('--xviolated',help="exclude violated ppo's",
                            action='store_true')
    parser.add_argument('--predicates',nargs='*',
                            help='predicates of interest (default: all)')
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

    capp = CApplication(sempath,excludefiles=excludefiles)

    pofilter = lambda p:True
    if args.predicates:
        pofilter = lambda p:p.get_predicate_tag() in args.predicates

    openppos = capp.get_open_ppos()
    violations = capp.get_violations()
    delegated = capp.get_delegated()

    if len(openppos) > 0:
        print('Open proof obligations:\n' + ('=' * 80))
        print(RP.tag_file_function_pos_tostring(openppos,pofilter=pofilter))
    else:
        print('No open proof obligations found')

    if len(delegated) > 0:
        if args.xdelegated:
            print("Number of delegated ppo's: " + (str(len(delegated))))
        else:
            print('\n\nDelegated proof obligations:\n' +  ('=' * 80))
            print(RP.tag_file_function_pos_tostring(delegated,pofilter=pofilter))
    else:
        print('No delegated proof obligations found')

    if len(violations) > 0:
        if args.xviolated:
            print("Number of violations: " + str(len(violations)))
        else:
            print('\n\nViolations:\n' + ('=' * 80))
            print(RP.tag_file_function_pos_tostring(violations,pofilter=pofilter))
    else:
        print('\n' + ('=' * 80) + '\nNo violations found')
        print('Note: any open proof obligation can be a violation!')
        print('=' * 80)
