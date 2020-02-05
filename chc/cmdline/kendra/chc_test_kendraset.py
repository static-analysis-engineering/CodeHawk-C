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
import logging
import os

import chc.util.fileutil as UF

from chc.util.Config import Config
from chc.cmdline.ParseManager import ParseManager
from chc.cmdline.kendra.TestManager import TestManager
from chc.cmdline.kendra.TestManager import FileParseError
from chc.cmdline.kendra.TestManager import AnalyzerMissingError

def parse():
    usage = (
        '\nCall with the directory name of one of the subdirectories in\n' +
        'tests/sard/kendra\n\n  Example: python chc_test_kendraset.py id115Q\n')
    description = (
        'Parses and analyzes a set of 4 test cases from the NIST Software Assurance\n ' +
        'Reference Dataset (SARD) and compares the results with a set of reference\n ' +
        'results\n')
    parser = argparse.ArgumentParser(usage=usage,description=description)
    parser.add_argument('testset',help='name of the test case (e.g., id115Q)')
    parser.add_argument('--saveref',help='save ppo specs',action='store_true')
    parser.add_argument('--savesemantics',help='save tar file with semantics files',
                            action='store_true')
    parser.add_argument('--verbose',help='print verbose output',action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    testname = args.testset
    loglevel = logging.WARNING
    logfilename =  args.testset + '_log.txt'
    logging.basicConfig(filename=logfilename,level=loglevel)

    try:
        UF.check_parser()
        UF.check_analyzer()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

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
        print('    ' + testfilename + '.')
        print('*' * 80)
        exit(1)

    testmanager = TestManager(cpath,cpath,testname,saveref=args.saveref,verbose=args.verbose)
    testmanager.clean()
    try:
        if testmanager.test_parser(savesemantics=args.savesemantics):
            testmanager.test_ppos()
            testmanager.test_ppo_proofs(delaytest=True)
            testmanager.test_spos(delaytest=True)
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_spos(delaytest=True)
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_ppo_proofs()
            testmanager.test_spos()
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_spo_proofs()
            if testmanager.verbose:
                testmanager.print_test_results()
            else:
                testmanager.print_test_results_summary()
    except FileParseError as e:
        print(': Unable to parse ' + str(e))
        exit(1)

    except OSError as e:
        print('*' * 80)
        print('OS Error: ' + str(e) + ': Please check the platform settings in Config.py')
        print('*' * 80)
        exit(1)
        
        
