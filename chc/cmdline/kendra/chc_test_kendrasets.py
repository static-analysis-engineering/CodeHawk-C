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

import chc.util.fileutil as UF

from chc.util.Config import Config
from chc.cmdline.ParseManager import ParseManager
from chc.cmdline.kendra.TestManager import TestManager
from chc.cmdline.kendra.TestManager import FileParseError
from chc.cmdline.kendra.TestManager import AnalyzerMissingError


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", help="print verbose output", action="store_true")
    args = parser.parse_args()
    return args


skips = [163, 363, 391]

if __name__ == "__main__":
    args = parse()

    try:
        UF.check_parser()
        UF.check_analyzer()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    for id in range(115, 403, 4):

        if id in skips:
            continue

        testname = "id" + str(id) + "Q"

        try:
            cpath = UF.get_kendra_testpath(testname)
        except UF.CHError as e:
            print(str(e.wrap()))
            continue

        testfilename = os.path.join(cpath, testname + ".json")
        if not os.path.isfile(testfilename):
            print("*" * 80)
            print("Test directory does not contain a test specification.")
            print("Expected to find the file")
            print("    " + testfilename + ".")
            print("*" * 80)
            exit(1)

        testmanager = TestManager(cpath, cpath, testname, verbose=args.verbose)
        testmanager.clean()
        try:
            if testmanager.test_parser():
                testmanager.test_ppos()
                testmanager.test_ppo_proofs(delaytest=True)
                testmanager.test_spos(delaytest=True)
                testmanager.test_spo_proofs(delaytest=True)
                testmanager.test_spos(delaytest=True)
                testmanager.test_spo_proofs(delaytest=True)
                testmanager.test_ppo_proofs()
                testmanager.test_spos()
                testmanager.test_spo_proofs()
                if testmanager.verbose:
                    testmanager.print_test_results()
                else:
                    testmanager.print_test_results_line_summary()
        except FileParseError as e:
            print(": Unable to parse " + str(e))
            exit(1)

        except OSError as e:
            print("*" * 80)
            print(
                "OS Error: "
                + str(e)
                + ": Please check the platform settings in Config.py"
            )
            print("*" * 80)
            exit(1)
