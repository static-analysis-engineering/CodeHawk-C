#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023  Aarno Labs, LLC
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
"""Command-line interface to the CodeHawk C Analyzer."""

import argparse
import os
import sys

from typing import List, NoReturn

from chc.app.CApplication import CApplication
from chc.cmdline.kendra.TestManager import TestManager
from chc.cmdline.kendra.TestManager import FileParseError
from chc.cmdline.kendra.TestManager import AnalyzerMissingError
from chc.cmdline.kendra.TestSetRef import TestSetRef
from chc.cmdline.ParseManager import ParseManager

import chc.reporting.DictionaryTables as DT
import chc.reporting.ProofObligations as RP

import chc.util.fileutil as UF


def print_error(m: str) -> None:
    sys.stderr.write(("*" * 80) + "\n")
    sys.stderr.write(m + "\n")
    sys.stderr.write(("*" * 80) + "\n")


def kendra_list(args: argparse.Namespace) -> NoReturn:
    """Prints out the list of kendra tests available in the test directory."""

    #arguments

    path = UF.get_kendra_path()

    result: List[str] = []

    if os.path.isdir(path):
        for d1 in os.listdir(path):
            if d1.startswith("id"):
                result.append(d1)

    print("Kendra test sets currently provided (" + str(len(result)) + "):")
    print("-" * 80)
    for d in sorted(result):
        print("  " + d)

    exit(0)


def kendra_show_set(args: argparse.Namespace) -> NoReturn:
    """Prints out the reference information of a kendra test set."""

    # arguments
    ctestset = args.testset
    try:
        cpath = UF.get_kendra_testpath(ctestset)
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    testfilename = os.path.join(cpath, ctestset + ".json")
    if not os.path.isfile(testfilename):
        print_error(
            "Test directory does not contain a test specification.\n"
            + "Expected to find the file "
            + testfilename)
        exit(1)

    testsetref = TestSetRef(testfilename)
    print(str(testsetref))

    exit(0)


def run_test(testname: str, verbose: bool, line_summary: bool = False) -> None:
    try:
        cpath = UF.get_kendra_testpath(testname)
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    reftestfilename = os.path.join(cpath, testname + ".json")
    if not os.path.isfile(reftestfilename):
        print_error(
            "Test directory does not contain a test specification.\n"
            + "Expected to find the file "
            + reftestfilename)
        exit(1)

    testmanager = TestManager(cpath, cpath, testname, verbose=verbose)
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
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_spo_proofs(delaytest=True)
            testmanager.test_spo_proofs()
            if testmanager.verbose:
                testmanager.print_test_results()
            elif line_summary:
                testmanager.print_test_results_line_summary()
            else:
                testmanager.print_test_results_summary()
    except FileParseError as e:
        print_error(": Unable to parse " + str(e))
        exit(1)

    except OSError as e:
        print_error(
            "OS Error: "
            + str(e)
            + ": Please check the platform settings in Config.py")

    except UF.CHCError as e:
        print_error(
            "Error in test " + testname + ": " + str(e))
        raise


def kendra_test_set(args: argparse.Namespace) -> NoReturn:
    """Parses and analyzes a testset and compares the result with the reference results."""

    # arguments
    ctestset: str = args.testset
    logfile: str = args.logfile
    loglevel: str = args.loglevel
    verbose: bool = args.verbose

    try:
        UF.check_parser()
        UF.check_analyzer()
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    run_test(ctestset, verbose)
    exit(0)


skips = [139, 151, 163, 363, 391]
    

def kendra_test_sets(args: argparse.Namespace) -> NoReturn:

    # arguments
    verbose = args.verbose

    for id in range(115, 403, 4):

        if id in skips:
            continue

        testname = "id" + str(id) + "Q"

        run_test(testname, verbose, line_summary=True)

    exit(0)


def kendra_report_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.cfilename
    showinvs: bool = args.show_invariants

    try:
        cpath = UF.get_kendra_cpath(cfilename)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath, "semantics")
    contractpath = os.path.join(cpath, "chcontracts")
    cfapp = CApplication(sempath, cfilename, contractpath=contractpath)
    cfile = cfapp.get_cfile()

    print(RP.file_code_tostring(cfile, showinvs=showinvs))
    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)


def kendra_show_file_table(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.cfilename
    tablename: str = args.tablename

    try:
        cpath = UF.get_kendra_cpath(cfilename)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath, "semantics")
    cfapp = CApplication(sempath, cfilename)
    if cfapp.has_single_file():
        cfile = cfapp.get_cfile()

        print(str(DT.get_file_table(cfile, tablename)))

    else:
        print_error(
            "File not found. Please make sure the test has been analyzed")
        exit(1)

    exit(0)


def kendra_show_function_table(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.cfilename
    functionname: str = args.functionname
    tablename: str = args.tablename

    try:
        cpath = UF.get_kendra_cpath(cfilename)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath, "semantics")
    cfapp = CApplication(sempath, cfilename)
    if cfapp.has_single_file():
        cfile = cfapp.get_cfile()

        print(str(DT.get_function_table(cfile, functionname, tablename)))

    else:
        print_error(
            "File not found. Please make sure the test has been analyzed")
        exit(1)

    exit(0)
