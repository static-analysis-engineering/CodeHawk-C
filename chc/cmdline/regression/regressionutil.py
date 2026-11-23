# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2026  Aarno Labs, LLC
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
"""Command-line interface to run regression tests."""

import argparse
import json
import os
import subprocess
import shutil
import sys

from typing import Any, Dict, List, NoReturn

from chc.app.CApplication import CApplication
from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager
from chc.proof.ConsolidatedStatus import ConsolidatedStatus
from chc.reporting.VerificationReport import (
    VerificationReport, findings_tostring)

import chc.util.fileutil as UF


def print_error(m: str) -> None:
    sys.stderr.write(("*" * 80) + "\n")
    sys.stderr.write(m + "\n")
    sys.stderr.write(("*" * 80) + "\n")


def get_tests() -> List[Dict[str, Any]]:
    testsfile = UF.get_regression_tests_json_file()

    with open(testsfile, "r") as fp:
        return json.load(fp).get("tests", [])
    return []


def has_test(cfilename: str) -> bool:
    tests = get_tests()

    return any(test.get("filename", "?") == cfilename for test in tests)


def get_test(cfilename: str) -> Dict[str, Any]:
    for test in get_tests():
        if test.get("filename", "?") == cfilename:
            return test
    raise UF.CHError("No test found with name " + cfilename)


def regression_list(args: argparse.Namespace) -> NoReturn:

    testsfile = UF.get_regression_tests_json_file()

    with open(testsfile, "r") as fp:
        testlist = json.load(fp).get("tests", [])

    print("Regression tests listed:")
    for testrec in testlist:
        print(" - " + testrec.get("filename"))

    exit(0)


def run_regression_test_file(
        testspec: Dict[str, Any],
        loglevel="WARNING") -> str:

    try:
        UF.check_parser()
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    cfilename = testspec.get("filename", "?")

    def returnmsg(s: str) -> str:
        return cfilename.ljust(32) + "[" + s.ljust(50) + "]"

    pcfile_c = UF.get_regression_testfile_path(cfilename)
    projectpath = os.path.dirname(os.path.abspath(pcfile_c))
    targetpath = projectpath
    cfilename_c = os.path.basename(pcfile_c)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    po_cmd = "undefined-behavior-primary"
    analysisdomains = "llrvisp"

    parsemanager = ParseManager(
        projectpath,
        projectname,
        targetpath,
        tgtplatform=testspec.get("tgtplatform"),
        contractpath=os.path.join(projectpath, "cch_contracts"))
    parsemanager.remove_semantics()
    parsemanager.initialize_paths()

    try:
        cfilename_i = parsemanager.preprocess_file_with_cc(cfilename_c)
        result = parsemanager.parse_ifile(cfilename_i, chloglevel=loglevel)
        if result != 0:
            return returnmsg("Error in parsing")
    except OSError as e:
        return returnmsg("Failed: Error in parsing: " + str(e))

    parsemanager.save_semantics()
    parsearchive = UF.get_parse_archive(targetpath, projectname)

    if not os.path.isfile(parsearchive):
        print_error("Please run parser first on c file")
        exit(1)

    cchpath = UF.get_cchpath(targetpath, projectname)

    if os.path.isdir(cchpath):
        shutil.rmtree(cchpath)

    if os.path.isfile(parsearchive):
        os.chdir(targetpath)
        tarname = os.path.basename(parsearchive)
        cmd = ["tar", "xfz", os.path.basename(tarname)]
        result = subprocess.call(cmd, cwd=targetpath)
        if result != 0:
            return returnmsg("Failed: Error in extracting")

    contractpath = os.path.join(targetpath, "chc_contracts")

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        singlefile=True,
        keep_system_includes=True)

    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    am = AnalysisManager(
        capp,
        verbose=False,
        collectdiagnostics=False,
        keep_system_includes=True)

    status = am.create_file_primary_proofobligations(
        cfilename, po_cmd=po_cmd, return_status=True, chloglevel=loglevel)
    if status != 0:
        return returnmsg("Failed in creating primary proof obligations")
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    status = am.generate_and_check_file(
        cfilename,
        None,
        analysisdomains,
        0,
        return_status=True,
        chloglevel=loglevel)
    if status != 0:
        return returnmsg("Failed in generate-and-check (round 0)")
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    for k in range(5):
        capp.update_spos()
        status = am.generate_and_check_file(
            cfilename, None, analysisdomains, k + 1, return_status=True)
        if status != 0:
            return returnmsg("Failed in generate-and-check (round "
                             + str(k + 1) + ")")
        am.reset_tables(cfile)

    statusresults: Dict[str, int] = {}

    for fn in cfile.get_functions():
        ppos = fn.get_ppos()
        for ppo in ppos:
            statusresults.setdefault(ppo.status, 0)
            statusresults[ppo.status] += 1

    expected = testspec.get("expected", {})
    for (s, c) in expected.items():
        if s in statusresults:
            if not statusresults[s] == expected[s]:
                resultmsg = (
                    "Failed: Expected " + s + ":" + str(c)
                    + ", but found " + s + ":" + str(statusresults[s]))
                break
        else:
            resultmsg = (
                "Failed: Expected " + s + ":" + str(c)
                + ", but found none for " + s)
            break

    else:
        resultmsg = "Passed " + ("." * 43)

    # optional: status counts of the supporting proof obligations (e.g.,
    # return-site proof obligations that check contract postconditions)
    expectedspo = testspec.get("expected-spo", {})
    if resultmsg.startswith("Passed") and len(expectedspo) > 0:
        spostatus: Dict[str, int] = {}
        for fn in cfile.get_functions():
            for spo in fn.get_spos():
                spostatus.setdefault(spo.status, 0)
                spostatus[spo.status] += 1
        for (s, c) in expectedspo.items():
            if spostatus.get(s, 0) != c:
                resultmsg = (
                    "Failed: Expected spo " + s + ":" + str(c)
                    + ", but found " + s + ":" + str(spostatus.get(s, 0)))
                break

    # number of primary proof obligations at locations that some domain
    # proves unreachable
    expectedunr = testspec.get("expected-unreachable")
    if resultmsg.startswith("Passed") and expectedunr is not None:
        nunr = sum(
            1 for fn in cfile.get_functions() for ppo in fn.get_ppos()
            if len(ppo.unreachable_domains) > 0)
        if nunr != expectedunr:
            resultmsg = (
                "Failed: Expected unreachable:" + str(expectedunr)
                + ", but found " + str(nunr))

    # consolidated status of the primary proof obligations
    expectedcons = testspec.get("expected-consolidated", {})
    if resultmsg.startswith("Passed") and len(expectedcons) > 0:
        consoptions = testspec.get("consolidated-options", {})
        cons = ConsolidatedStatus(
            capp,
            closedprogram=consoptions.get("closed-program", False),
            entrypoints=consoptions.get("entry-points", ["main"]))
        conscounts = cons.count(
            [ppo for fn in cfile.get_functions() for ppo in fn.get_ppos()])
        for (s, c) in expectedcons.items():
            if conscounts.get(s, 0) != c:
                resultmsg = (
                    "Failed: Expected consolidated " + s + ":" + str(c)
                    + ", but found " + str(conscounts.get(s, 0)))
                break

    # verification report
    expectedvr = testspec.get("expected-verification", {})
    if resultmsg.startswith("Passed") and len(expectedvr) > 0:
        vroptions = testspec.get("consolidated-options", {})
        vr = VerificationReport(
            capp,
            "implementation-defined",
            closedprogram=vroptions.get("closed-program", False),
            entrypoints=vroptions.get("entry-points", ["main"]))
        vrcounts = vr.counts()
        for (s, c) in expectedvr.items():
            if vrcounts.get(s, 0) != c:
                resultmsg = (
                    "Failed: Expected verification " + s + ":" + str(c)
                    + ", but found " + str(vrcounts.get(s, 0)))
                break

    # text of the FINDINGS section, including the caveat on open proof
    # obligations and missing information
    expectedfindings = testspec.get("expected-findings")
    if resultmsg.startswith("Passed") and expectedfindings is not None:
        vroptions = testspec.get("consolidated-options", {})
        vr = VerificationReport(
            capp,
            "implementation-defined",
            closedprogram=vroptions.get("closed-program", False),
            entrypoints=vroptions.get("entry-points", ["main"]))
        found = findings_tostring(
            vr.findings(), results=vr.results(),
            boundary=vr.boundary()).split("\n")
        if found != expectedfindings:
            diffs = [
                i for i in range(max(len(found), len(expectedfindings)))
                if i >= len(found) or i >= len(expectedfindings)
                or found[i] != expectedfindings[i]]
            i = diffs[0]
            print_error(
                cfilename + ": FINDINGS line " + str(i + 1) + ": expected\n  "
                + (expectedfindings[i] if i < len(expectedfindings) else "(none)")
                + "\nbut found\n  "
                + (found[i] if i < len(found) else "(none)"))
            resultmsg = (
                "Failed: FINDINGS text differs at line " + str(i + 1))

    return returnmsg(resultmsg)


def regression_test_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.cfilename

    if not has_test(cfilename):
        print_error("File " + cfilename + " not found")
        exit(1)

    print(run_regression_test_file(get_test(cfilename)))

    exit(0)


def regression_run_tests(args: argparse.Namespace) -> NoReturn:

    # arguments
    loglevel: str = args.loglevel

    lines: List[str] = []
    for test in get_tests():
        if test.get("status", "pass") == "fail":
            continue
        lines.append(run_regression_test_file(test, loglevel=loglevel))

    print("\n".join(lines))

    exit(0)
