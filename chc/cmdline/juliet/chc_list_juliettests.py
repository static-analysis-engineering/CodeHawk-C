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
import time

import chc.util.fileutil as UF
import chc.reporting.reportutil as UR

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cwe',help='only list tests for this CWE')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    cwerequested = 'all'
    if args.cwe is not None: cwerequested = args.cwe

    try:
        testcases = UF.get_flattened_juliet_testcases()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    result = {}
    
    for cwe in sorted(testcases):
        if not (cwerequested == 'all' or cwerequested == cwe):
            continue
        for t in sorted(testcases[cwe]):
            name = cwe + ':' + t
            result[name] = UF.get_juliet_result_times(cwe,t)
            
    print(UR.reportheader('Juliet test sets currently provided (' + str(len(result)) + ')'))
    print('\n  ' + 'directory'.ljust(44) + 'analysis time    score time')
    print('-' * 80)
    for name in sorted(result):
        (ktmodtime,scmodtime) = result[name]
        if ktmodtime == '0': ktmodtime = 'no results'
        if scmodtime == '0': scmodtime = 'no results'
        print('  ' + name.ljust(44)
                  + ktmodtime.rjust(16) + '  '
                  + scmodtime.rjust(16))
    print(('-' * 80) + '\n')
