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

import argparse
import json
import os

from chc.util.Config import Config
from chc.cmdline.kendra.TestSetRef import TestSetRef

def parse():
    usage = ('\nCall with the directory name of one of the subdirectories in\n' +
                 'tests/sard/kendra\n\n' +
                 '   Example: python chc_show_kendraset.py id115Q\n')
    description = ('Displays the proof obligations and their expected (desired) status')
    parser = argparse.ArgumentParser(usage=usage,description=description)
    parser.add_argument('testset',help='name of test directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    config = Config()
    testpath = os.path.join(config.testdir,'kendra')
    testname = args.testset
    cpath = os.path.join(os.path.abspath(testpath),testname)
    if not os.path.isdir(cpath):
        print('*' * 80)
        print('Test directory')
        print('   ' + cpath)
        print('not found')
        print('*' * 80)
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
        
