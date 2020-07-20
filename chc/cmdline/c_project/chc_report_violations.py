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
"""Reports violations for a project that has been analyzed."""

import argparse
import os

import chc.util.fileutil as UF

import chc.reporting.ProofObligations as RP

from chc.app.CApplication import CApplication

def parse():
    usage = ('\nCall with the directory name that contains the semantics directory of a project')
    parser = argparse.ArgumentParser(usage=usage,description=__doc__)
    parser.add_argument('path',help=('directory that holds the semantics directory'
                                         + ' or short-cut name of a test application'))
    parser.add_argument('--showcode',help='show the function code associated with the violations',
                            action='store_true')
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

    stats = {}
    stats['openppos'] = 0
    stats['openspos'] = 0
    stats['ppoviolations'] = 0
    stats['spoviolations'] = 0
   
    capp = CApplication(sempath)
    fns = []
    def v(f):
        ppoviolations = f.get_violations()
        spoviolations = f.get_spo_violations()
        openppos = f.get_open_ppos()
        openspos = f.get_open_spos()
        if len(ppoviolations) > 0 or len(spoviolations) > 0:
            fns.append(f)
            stats['ppoviolations'] += len(ppoviolations)
            stats['spoviolations'] += len(spoviolations)
        stats['openppos'] += len(openppos)
        stats['openspos'] += len(openspos)
    capp.iter_functions(v)

    print('~' * 80)
    print('Violation report for application ' + args.path)
    print('  - ppo violations suspected: ' + str(stats['ppoviolations']))
    print('  - spo violations suspected: ' + str(stats['spoviolations']))
    print('  - open ppos: ' + str(stats['openppos']))
    print('  - open spos: ' + str(stats['openspos']))
    print('~' * 80)
    print('\n')

    if stats['ppoviolations'] + stats['spoviolations'] > 0:
        pofilter = lambda po:po.is_violated()
        print('Violations suspected: ')
        for f in fns:
            if  args.showcode:
                print(RP.function_code_violation_tostring(f))
            else:
                print(RP.function_pos_to_string(f,pofilter=pofilter))

    opencount = stats['openppos'] + stats['openspos']

    if opencount > 0:
        print(('*' * 35) + ' Important ' + ('*' * 34))
        print('* Any of the ' + str(opencount)
                  + ' open proof obligations could indicate a violation.')
        print('* A program is proven safe only if ALL proof obligations are proven safe.')
        print('*' * 80)
    
