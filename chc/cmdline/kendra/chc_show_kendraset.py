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
"""Displays the proof obligations and their expected (desired) status."""

import argparse
import json
import os

import chc.util.fileutil as UF
from chc.cmdline.kendra.TestSetRef import TestSetRef

def parse():
    usage = ('\nCall with the directory name of one of the subdirectories in\n' +
                 'tests/kendra\n\n' +
                 '   Example: python chc_show_kendraset.py id115Q\n')
    parser = argparse.ArgumentParser(usage=usage,description=__doc__)
    parser.add_argument('testset',help='name of test directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()

    testname = args.testset
    try:
        cpath = UF.get_kendra_testpath(testname)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    testfilename = os.path.join(cpath,testname + '.json')
    if not os.path.isfile(testfilename):
        print('*' * 80)
        print('Test directory does not contain a test specification.')
        print('Expected to find the file')
        print('   ' + testfilename)
        print('*' * 80)
        exit(1)
        
    testsetref = TestSetRef(testfilename)
    print(str(testsetref))
        
