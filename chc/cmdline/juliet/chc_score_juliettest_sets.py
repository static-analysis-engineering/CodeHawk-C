# ------------------------------------------------------------------------------
# Script to score multiple juliet tests
# Author: Andrew McGraw
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
import subprocess

from multiprocessing import Pool

import chc.util.fileutil as UF

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--maxprocesses',type=int,help='maximum number of processors to use',
                            default='1')
    parser.add_argument('--cwe',help='only score the given cwe')
    args = parser.parse_args()
    return args

def score_juliettest(testcase):
    (cwe,t) = testcase
    cmd = ['python', 'chc_score_juliettest.py', cwe, t ]
    print('Scoring ' + ':'.join(testcase) + ' ...')
    result = subprocess.call(cmd, stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT)
    return result

if __name__ == '__main__':

    args = parse()

    pool = Pool(args.maxprocesses)
    testcases = []
    results = []

    def excluded(cwe):
        if args.cwe is None: return False
        return not (args.cwe == cwe)

    juliettests = UF.get_juliet_testcases()
    for cwe in sorted(juliettests):
            if excluded(cwe): continue        
            for subdir in juliettests[cwe]:
                for t in juliettests[cwe][subdir]:
                    testcases.append((cwe,t))
            
    results = pool.map(score_juliettest, testcases)

    print('\n\n' + ('=' * 80))
    if results.count(0) < len(results):
        for x in range(len(results)):
            if results[x] != 0:
                print('Error in testcase ' + ':'.join(testcases[x]))
    else:
        cmd = [ 'python', 'chc_juliet_dashboard.py' ]
        result = subprocess.call(cmd,stderr=subprocess.STDOUT)
        print('All Juliet test cases were scored successfully.')
    print(('=' * 80) + '\n')
