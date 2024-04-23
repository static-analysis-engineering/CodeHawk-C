#!/usr/bin/env python3
# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023-2024  Aarno Labs, LLC
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
import json
import os
import sys

from typing import Any, Dict, List, NoReturn, Optional, Set, Tuple

from chc.app.CApplication import CApplication
from chc.cmdline.kendra.TestManager import TestManager
from chc.cmdline.kendra.TestManager import FileParseError
from chc.cmdline.kendra.TestManager import AnalyzerMissingError
from chc.cmdline.kendra.TestSetRef import TestSetRef
from chc.cmdline.ParseManager import ParseManager

import chc.reporting.DictionaryTables as DT
import chc.reporting.ProofObligations as RP

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel


def print_error(m: str) -> None:
    sys.stderr.write(("*" * 80) + "\n")
    sys.stderr.write(m + "\n")
    sys.stderr.write(("*" * 80) + "\n")


def set_logging(
        level: str,
        path: str,
        logfilename: Optional[str],
        msg: str = "",
        mode: str = "a") -> None:

    if level in LogLevel.all() or logfilename is not None:
        if logfilename is not None:
            logfilename = os.path.join(path, logfilename)

        chklogger.set_chkc_logger(
            msg, level=level, logfilename=logfilename, mode=mode)


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


def kendra_clean_set(args: argparse.Namespace) -> NoReturn:
    """Removes the analysis artifacts of a kendra test set."""

    # arguments
    testname = args.testset
    try:
        projectpath = UF.get_kendra_testpath(testname)
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    testmanager = TestManager(projectpath, projectpath, testname)
    testmanager.clean()

    exit(0)


def run_test(testname: str, verbose: bool, line_summary: bool = False) -> None:
    try:
        projectpath = UF.get_kendra_testpath(testname)
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    reftestfilename = os.path.join(projectpath, testname + ".json")
    if not os.path.isfile(reftestfilename):
        print_error(
            "Test directory does not contain a test specification.\n"
            + "Expected to find the file "
            + reftestfilename)
        exit(1)

    testmanager = TestManager(
        projectpath, projectpath, testname, verbose=verbose)
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
    """Parses and analyzes a testset and compares the result with a reference"""

    # arguments
    testname: str = args.testset
    verbose: bool = args.verbose
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        UF.check_parser()
        UF.check_analyzer()
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)

    try:
        projectpath = UF.get_kendra_testpath(testname)
    except UF.CHError as e:
        print_error(str(e.wrap()))
        exit(1)


    set_logging(
        loglevel,
        projectpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="cfile parse invoked")

    run_test(testname, verbose)
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
    cfilename_c: str = args.cfilename
    showinvs: bool = args.show_invariants

    try:
        cpath = UF.get_kendra_cpath(cfilename_c)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    projectpath = cpath
    targetpath = projectpath
    cfilename = cfilename_c[:-2]
    projectname = os.path.basename(projectpath)
    contractpath = os.path.join(cpath, "chcontracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    print(RP.file_code_tostring(cfile, showinvs=showinvs))
    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)


def kendra_show_file_table(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename_c: str = args.cfilename
    tablename: str = args.tablename

    try:
        cpath = UF.get_kendra_cpath(cfilename_c)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    projectpath = cpath
    targetpath = projectpath
    cfilename = cfilename_c[:-2]
    projectname = os.path.basename(projectpath)
    contractpath = os.path.join(cpath, "chcontracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    print(str(DT.get_file_table(cfile, tablename)))

    exit(0)


def kendra_show_function_table(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename_c: str = args.cfilename
    functionname: str = args.functionname
    tablename: str = args.tablename

    try:
        cpath = UF.get_kendra_cpath(cfilename_c)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    projectpath = cpath
    targetpath = projectpath
    cfilename = cfilename_c[:-2]
    projectname = os.path.basename(projectpath)
    contractpath = os.path.join(cpath, "cXhcontracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    print(str(DT.get_function_table(cfile, functionname, tablename)))

    exit(0)


def get_ppo_count(spec: Dict[str, Any]) -> int:
    """Returns the number of ppos in the spec file."""
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            total += len(spec["cfiles"][f]["functions"][ff]["ppos"])
    return total


def get_spo_count(spec: Dict[str, Any]) -> int:
    """Returns the number of spos in the spec file."""
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            if "spos" in spec["cfiles"][f]["functions"][ff]:
                total += len(spec["cfiles"][f]["functions"][ff]["spos"])
    return total


def get_ppos(spec: Dict[str, Any], f: str) -> List[Any]:
    ppos: List[Any] = []
    for ff in spec["cfiles"][f]["functions"]:
        ppos.extend(spec["cfiles"][f]["functions"][ff]["ppos"])
    return ppos


def get_spos(spec: Dict[str, Any], f: str) -> List[Any]:
    spos: List[Any] = []
    for ff in spec["cfiles"][f]["functions"]:
        if "spos" in spec["cfiles"][f]["functions"][ff]:
            spos.extend(spec["cfiles"][f]["functions"][ff]["spos"])
    return spos


def get_violation_predicates(spec: Dict[str, Any]) -> Set[str]:
    predicates: Set[str] = set([])
    for f in spec["cfiles"]:
        for ppo in get_ppos(spec, f):
            status = ppo["tgtstatus"]
            if status in ["violation", "violation:delegated"]:
                predicates.add(ppo["predicate"])
        for spo in get_spos(spec, f):
            status = spo["tgtstatus"]
            if status == "violation":
                predicates.add(ppo["predicate"])
    return predicates


def get_perc(x: int, y: int, width: int) -> str:
    fmt = "{:>" + str(width) + ".1f}"
    if y > 0:
        perc = float(x) / float(y) * 100.0
        return fmt.format(perc)
    else:
        return " - ".rjust(width)


def get_status_ppo_counts(spec: Dict[str, Any], status: str) -> Tuple[int, int]:
    count = 0
    tgtcount = 0
    for f in spec["cfiles"]:
        for ppo in get_ppos(spec, f):
            if ppo["tgtstatus"] == status:
                tgtcount += 1
                if ppo["status"] == status:
                    count += 1
    return (count, tgtcount)


def get_open_ppo_count(spec: Dict[str, Any]) -> int:
    count = 0
    for f in spec["cfiles"]:
        for ppo in get_ppos(spec, f):
            if ppo["status"] == "open":
                count += 1
    return count


def get_safe_ppo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    return get_status_ppo_counts(spec, "safe")


def get_safe_ppo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_safe_ppo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_violation_ppo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    return get_status_ppo_counts(spec, "violation")


def get_violation_ppo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_violation_ppo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_delegated_ppo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    (safecnt, safetgtcnt) = get_status_ppo_counts(spec, "safe:delegated")
    (vcnt, vtgtcnt) = get_status_ppo_counts(spec, "violation:delegated")
    return (safecnt + vcnt, safetgtcnt + vtgtcnt)


def get_delegated_ppo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_delegated_ppo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_status_spo_counts(spec: Dict[str, Any], status: str) -> Tuple[int, int]:
    count = 0
    tgtcount = 0
    for f in spec["cfiles"]:
        for spo in get_spos(spec, f):
            if spo["tgtstatus"] == status:
                tgtcount += 1
                if spo["status"] == status:
                    count += 1
    return (count, tgtcount)


def get_open_spo_count(spec: Dict[str, Any]) -> int:
    count = 0
    for f in spec["cfiles"]:
        for spo in get_spos(spec, f):
            if spo["status"] == "open":
                count += 1
    return count


def get_safe_spo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    return get_status_spo_counts(spec, "safe")


def get_safe_spo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_safe_spo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_violation_spo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    return get_status_spo_counts(spec, "violation")


def get_violation_spo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_violation_spo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_delegated_spo_counts(spec: Dict[str, Any]) -> Tuple[int, int]:
    (safecnt, safetgtcnt) = get_status_spo_counts(spec, "safe:delegated")
    (vcnt, vtgtcnt) = get_status_spo_counts(spec, "violation:delegated")
    return (safecnt + vcnt, safetgtcnt + vtgtcnt)


def get_delegated_spo_perc(spec: Dict[str, Any], width: int) -> str:
    (cnt, tgtcnt) = get_delegated_spo_counts(spec)
    return get_perc(cnt, tgtcnt, width)


def get_ppo_results(spec: Dict[str, Any]) -> str:
    opencnt = get_open_ppo_count(spec)
    s_opencnt = "-" if opencnt == 0 else str(opencnt)
    return (
        str(get_ppo_count(spec)).rjust(6)
        + get_safe_ppo_perc(spec, 12)
        + get_violation_ppo_perc(spec, 12)
        + get_delegated_ppo_perc(spec, 12)
        + s_opencnt.rjust(10)
    )


def get_spo_results(spec: Dict[str, Any]) -> str:
    spocount = get_spo_count(spec)
    s_spocount = "-" if spocount == 0 else str(spocount)
    opencnt = get_open_spo_count(spec)
    s_opencount = "-" if opencnt == 0 else str(opencnt)
    return (
        str(spocount).rjust(6)
        + get_safe_spo_perc(spec, 12)
        + get_violation_spo_perc(spec, 12)
        + get_delegated_spo_perc(spec, 12)
        + str(opencnt).rjust(10)
    )


def dashboard_header() -> str:
    lines: List[str] = []
    header = "testcase".ljust(9)
    headerppos = (
        "ppos".rjust(6)
        + "   "
        + "%safe".center(12)
        + "%violation".center(12)
        + "%delegated".center(12)
        + "%open".center(12)
    )
    headerspos = (
        "spos".rjust(6)
        + "  "
        + "%safe".center(12)
        + "%violation".center(12)
        + "%delegated".center(12)
        + "%open".center(12)
    )
    headerline2 = (
        " ".ljust(18)
        + "proven".center(12)
        + "proven".center(12)
        + "-".ljust(32)
        + "proven".center(12)
        + "proven".center(12)
    )
    lines.append(header + headerppos + headerspos)
    lines.append(headerline2)
    lines.append("-" * 150)
    return "\n".join(lines)


def kendra_dashboard(args: argparse.Namespace) -> NoReturn:

    kendrapath = UF.get_kendra_path()
    testcases = [(i, "id" + str(i) + "Q") for i in range(115, 394, 4)]

    lines: List[str] = []

    lines.append(dashboard_header())

    for (i, t) in testcases:
        if (i % 100) < 4:
            lines.append("-" * 120)
        specfilename = os.path.join(os.path.join(kendrapath, t), t + ".json")
        with open(specfilename) as fp:
            spec = json.load(fp)
        lines.append(
            t.ljust(9)
            + get_ppo_results(spec)
            + "  | "
            + get_spo_results(spec)
            + " ".ljust(6)
            + ",".join(get_violation_predicates(spec)))
    lines.append("-" * 150)

    print("\n".join(lines))

    exit(0)
