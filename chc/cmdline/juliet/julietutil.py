# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2024  Aarno Labs, LLC
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
"""Implementation of juliet commands in the CLI."""

import argparse
import json
import os
import shutil
import subprocess
import time
import sys

from contextlib import contextmanager
from multiprocessing import Pool

from typing import (
    Any, Callable, cast, Dict, List, NoReturn, Optional, Tuple, TYPE_CHECKING)

from chc.app.CApplication import CApplication

from chc.cmdline.AnalysisManager import AnalysisManager

import chc.cmdline.juliet.JulietTestScoring as JTS
from chc.cmdline.juliet.JulietTestSetRef import JulietTestSetRef

from chc.linker.CLinker import CLinker

import chc.reporting.ProofObligations as RP
import chc.reporting.reportutil as UR

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionPO import CFunctionPO


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


@contextmanager
def timing(activity):
    t0 = time.time()
    yield
    print(
        "\n"
        + ("=" * 80)
        + "\nCompleted "
        + activity
        + " in "
        + str(time.time() - t0)
        + " secs"
        + "\n"
        + ("=" * 80)
    )


def juliet_check_config(args: argparse.Namespace) -> NoReturn:

    config = Config()

    width = 15

    def itemstr(name: str, item: str, check: bool =True) -> str:
        if check:
            if os.path.isfile(item):
                found = " (found)"
            else:
                found = " (** not found **)"
        else:
            found = ""
        return name.ljust(width) + ": " + str(item) + found

    lines: List[str] = []
    lines.append("Analyzer configuration:")
    lines.append(itemstr("base directory", config.topdir, check=False))
    lines.append(itemstr("C parser", config.cparser))
    lines.append(itemstr("C analyzer", config.canalyzer))
    lines.append(itemstr("summaries", config.summaries))
    lines.append(itemstr("juliet tests", config.targets["juliet"]))
    lines.append("-" * 80)

    print("\n".join(lines))

    try:
        testcases = UF.get_juliet_testcases()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    total = 0

    lines = []
    lines.append("Juliet Tests: ")
    for cwe in sorted(testcases):
        lines.append("  " + cwe.ljust(10))
        for subset in sorted(testcases[cwe]):
            total += len(testcases[cwe][subset])
            lines.append(
                "    "
                + subset.ljust(10)
                + str(len(testcases[cwe][subset])).rjust(4)
                + (" tests" if len(testcases[cwe][subset]) > 1 else " test")
            )
    lines.append("-" * 80)
    lines.append("  Total:".ljust(12) + str(total).rjust(4) + " test sets")

    print("\n".join(lines))
    exit(0)



def juliet_list(args: argparse.Namespace) -> NoReturn:
    """Prints out the list of juliet tests available in the configured repo."""

    # arguments
    argcwe: Optional[str] = args.cwe

    cwerequested: str = "all" if argcwe is None else argcwe

    try:
        testcases = UF.get_flattened_juliet_testcases()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    result: Dict[str, Tuple[str, str]] = {}

    for cwe in sorted(testcases):
        if not (cwerequested == "all" or cwerequested == cwe):
            continue
        for t in sorted(testcases[cwe]):
            name = cwe + ":" + t
            result[name] = UF.get_juliet_result_times(cwe, t)

    lines: List[str] = []

    lines.append(UR.reportheader(
        "Juliet test sets currently provided (" + str(len(result)) + ")"))

    lines.append(
        "\n  " + "directory".ljust(44) + "last analysis     last scoring")
    lines.append("-" * 80)
    for name in sorted(result):
        (chmodtime, scmodtime) = result[name]
        if chmodtime == "0":
            chmodtime = "no results"
        if scmodtime == "0":
            scmodtime = "no results"
        lines.append(
            "  "
            + name.ljust(44)
            + chmodtime.rjust(16)
            + "  "
            + scmodtime.rjust(16))
    lines.append("-" * 80)

    print("\n".join(lines))

    exit(0)


def juliet_convert(args: argparse.Namespace) -> NoReturn:
    """Converts a juliet tar.gz semantics file into new format."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    jtgtpath: str = args.targetpath

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
        UF.check_semantics(projectpath, deletesemantics=True)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    targetpath = os.path.abspath(jtgtpath)
    projectname = jcwe + "_" + jtest
    cchpath = UF.get_cchpath(targetpath, projectname)

    print("projectpath: " + projectpath)
    print("targetpath: " + targetpath)
    print("cchpath: " + cchpath)

    if not os.path.isdir(cchpath):
        os.mkdir(cchpath)

    projectsourcepath = os.path.join(
        os.path.join(projectpath, "semantics"), "sourcefiles")
    projectparsepath = os.path.join(
        os.path.join(projectpath, "semantics"), "ktadvance")
    savedsourcepath = UF.get_savedsource_path(targetpath, projectname)
    analysisresultspath = UF.get_analysisresults_path(
        targetpath, projectname)

    if not os.path.isdir(savedsourcepath):
        os.mkdir(savedsourcepath)

    # copy .c and .i files
    for fname in os.listdir(projectsourcepath):
        absname = os.path.join(projectsourcepath, fname)
        tgtname = os.path.join(savedsourcepath, fname)
        shutil.copy(absname, tgtname)
        chklogger.logger.info("copied %s to %s", absname, tgtname)

    if not os.path.isdir(analysisresultspath):
        os.mkdir(analysisresultspath)

    # copy parse results files
    targetfiles = os.path.join(projectparsepath, "target_files.xml")
    if os.path.isfile(targetfiles):
        shutil.copy(targetfiles, os.path.join(analysisresultspath, "target_files.xml"))
    for fdir in os.listdir(projectparsepath):
        absdir = os.path.join(projectparsepath, fdir)
        if os.path.isdir(absdir):
            tgtfiledir = os.path.join(analysisresultspath, fdir)
            cdict = fdir + "_cdict.xml"
            cfile = fdir + "_cfile.xml"
            src_cdict = os.path.join(projectparsepath, cdict)
            src_cfile = os.path.join(projectparsepath, cfile)

            # copy file-level files
            tgtpath = UF.get_cfile_filepath(targetpath, projectname, None, fdir)
            if not os.path.isdir(tgtpath):
                os.mkdir(tgtpath)
            tgt_cfile = UF.get_cfile_cfile(targetpath, projectname, None, fdir)
            tgt_cdict = UF.get_cfile_dictionaryname(
                targetpath, projectname, None, fdir)
            shutil.copy(src_cdict, tgt_cdict)
            shutil.copy(src_cfile, tgt_cfile)

            tgtfns = UF.get_cfile_fnspath(targetpath, projectname, None, fdir)
            if not os.path.isdir(tgtfns):
                os.mkdir(tgtfns)
            for fname in os.listdir(absdir):
                if fname.endswith("_cfun.xml"):
                    fnname = fname[len(fdir) + 1:-9]
                    fntgtpath = os.path.join(tgtfns, fnname)
                    if not os.path.isdir(fntgtpath):
                        os.mkdir(fntgtpath)
                    srcfn = os.path.join(absdir, fname)
                    tgtfn = os.path.join(fntgtpath, fname)
                    shutil.copy(srcfn, tgtfn)
    exit(0)


def juliet_analyze(args: argparse.Namespace) -> NoReturn:
    """Analyzes a single juliet test."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    jmaxproc: int = args.maxprocesses
    jrounds: int = args.analysisrounds
    jwordsize: int = args.wordsize
    jcontractpath: Optional[str] = args.contractpath
    verbose = args.verbose
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectname = jcwe + "_" + jtest

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if jcontractpath is None:
        contractpath = os.path.join(projectpath, "cch_contracts")
    else:
        contractpath = jcontractpath

    excludefiles = ["io.c", "main_linux.c", "std_thread.c"]

    set_logging(
        loglevel,
        projectpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="juliet analyze invoked")

    try:
        UF.check_cch_semantics(projectpath, projectname, deletesemantics=True)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    capp = CApplication(
        projectpath,
        projectname,
        projectpath,
        contractpath,
        excludefiles=excludefiles)

    def save_xrefs(f: "CFile") -> None:
        capp.indexmanager.save_xrefs(
            capp.projectpath, projectname, None, f.name, f.index)

    linker = CLinker(capp)
    linker.link_compinfos()
    linker.link_varinfos()
    capp.iter_files(save_xrefs)
    linker.save_global_compinfos()

    capp = CApplication(
        projectpath,
        projectname,
        projectpath,
        contractpath,
        excludefiles=excludefiles)

    am = AnalysisManager(
        capp,
        verbose=verbose,
        unreachability=True,
        wordsize=jwordsize,
        thirdpartysummaries=[UF.get_juliet_summaries()])

    try:
        am.create_app_primary_proofobligations(processes=jmaxproc)
        capp.reinitialize_tables()
        capp.collect_post_assumes()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    for i in range(1):
        am.generate_and_check_app("llrvisp", processes=jmaxproc)
        capp.reinitialize_tables()
        capp.update_spos()

    for i in range(5):
        capp.update_spos()
        am.generate_and_check_app("llrvisp", processes=jmaxproc)
        capp.reinitialize_tables()

    def filefilter(filename: str) -> bool:
        return not (filename in ["io", "main_linux", "std_thread"])

    contractviolations = capp.get_contract_condition_violations()
    if len(contractviolations) > 0:
        print(f" --> {len(contractviolations)} contraction violations")

    timestamp = os.stat(capp.targetpath).st_ctime
    try:
        result = RP.project_proofobligation_stats_to_dict(
            capp, filefilter=filefilter)
        result["timestamp"] = timestamp
        result["path"] = capp.projectpath
        UF.save_project_summary_results(capp.targetpath, result)
    except Exception as e:
        print(str(e))
        exit(1)

    exit(0)


def analyze_test(testdata: Tuple[str, str, int]) -> int:
    """CLI command to run a juliet test case.

    Note: this function needs to be global for multiprocessing to work.
    """

    (cwe, testcase, index) = testdata
    cmd = ["chkc", "juliet", "analyze", cwe, testcase]
    result = subprocess.call(cmd, stderr=subprocess.STDOUT)
    return result


def juliet_analyze_sets(args: argparse.Namespace) -> NoReturn:
    """Analyzes all or a subset of the registered juliet tests."""

    # arguments
    jmaxproc: int = args.maxprocesses
    jcwes: List[str] = args.cwes

    maxptxt = "" if jmaxproc == 1 else f" (with {jmaxproc} processors)"

    pool = Pool(jmaxproc)
    testcases = []

    def excluded(cwe: str) -> bool:
        if len(jcwes) == 0:
            return False
        else:
            return cwe not in jcwes

    with timing("analysis" + maxptxt):
        count: int = 0
        juliettests = UF.get_juliet_testcases()
        for cwe in sorted(juliettests):
            if excluded(cwe):
                continue
            print(f"Analyzing testcases for cwe {cwe}")
            for subdir in sorted(juliettests[cwe]):
                for t in juliettests[cwe][subdir]:
                    testcases.append((cwe, t, count))
                    count += 1

        results = pool.map(analyze_test, testcases)

    print("\n" + ("=" * 80))
    if len(results) == results.count(0):
        print("All Juliet tests cases ran successfully.")
    else:
        for x in range(len(results)):
            if results[x] != 0:
                print(f"Error in testcase {testcases[x][0]}")
    print("=" * 80)

    exit(0)


def juliet_report(args: argparse.Namespace) -> NoReturn:
    """Reports on a single juliet test."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test

    projectname = jcwe + "_" + jtest

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    contractpath = os.path.join(projectpath, "cch_contracts")

    excludefiles = ["io.c", "main_linux.c", "std_thread.c"]
    targetpath = projectpath

    summary = UF.read_project_summary_results(targetpath)
    if summary is not None:
        print(RP.project_proofobligation_stats_dict_to_string(summary))
        exit(0)

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        excludefiles=excludefiles)

    def filefilter(f: str) -> bool:
        return f not in excludefiles

    print(
        RP.project_proofobligation_stats_tostring(
            capp, extradsmethods=["deadcode"], filefilter=filefilter))

    contract_condition_violations = capp.get_contract_condition_violations()

    if len(contract_condition_violations) > 0:
        print("=" * 80)
        print(
            str(len(contract_condition_violations))
            + " CONTRACT CONDITION FAILURES")
        print("=" * 80)
        for (fn, cc) in contract_condition_violations:
            print(fn + ":")
            for (name, desc) in cc:
                print("   " + name + ":" + desc)
        print("=" * 80)

    exit(0)


def juliet_report_file(args: argparse.Namespace) -> NoReturn:
    """Rerports on a single c file within a juliet test."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    jcfilename_c: str = args.filename
    jshowcode: bool = args.showcode
    jopen: bool = args.open
    jinvariants: bool = args.showinvariants

    projectname = jcwe + "_" + jtest
    cfilename = jcfilename_c[:-2]

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    targetpath = projectpath
    cchpath = UF.get_cchpath(targetpath, projectname)
    contractpath = os.path.join(projectpath, "cch_contracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    pofilter = lambda po: True

    if jshowcode:
        if jopen:
            print(RP.file_code_open_tostring(cfile, showinvs=jinvariants))
        else:
            print(RP.file_code_tostring(cfile, showinvs=jinvariants))

    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)


def juliet_score(args: argparse.Namespace) -> NoReturn:
    """Prints out (and saves) the score for a single juliet test."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectname = jcwe + "_" + jtest

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    set_logging(
        loglevel,
        projectpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="juliet score invoked")

    targetpath = projectpath
    contractpath = os.path.join(projectpath, "cch_contracts")

    excludefiles = ["io.c", "main_linux.c", "std_thread.c"]

    d = UF.get_juliet_scorekey(jcwe, jtest)

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        excludefiles=excludefiles)

    testset = JulietTestSetRef(d)

    julietppos = JTS.get_julietppos(testset)

    ppopairs = JTS.get_ppo_pairs(julietppos, capp)
    print(JTS.testppo_results_tostring(ppopairs, capp))

    testsummary: Dict[str, Dict[str, Dict[str, int]]] = {}
    JTS.initialize_testsummary(testset, testsummary)
    JTS.fill_testsummary(ppopairs, testsummary, capp)

    print(JTS.testsummary_tostring(testsummary))

    testsummary["total"] = JTS.get_testsummary_totals(testsummary)

    UF.save_juliet_test_summary(jcwe, jtest, testsummary)

    exit(0)


def score_test(testdata: Tuple[str, str, int]) -> int:
    """CLI command to score a juliet test case.

    Note: this function needs to be global for multiprocessing to work.
    """

    (cwe, testcase, index) = testdata
    cmd = ["chkc", "juliet", "score", cwe, testcase]
    result = subprocess.call(cmd, stderr=subprocess.STDOUT)
    return result


def juliet_score_sets(args: argparse.Namespace) -> NoReturn:
    """Scores all or a subset of the registered juliet tests."""

    # arguments
    jmaxproc: int = args.maxprocesses
    jcwes: List[str] = args.cwes

    maxptxt = "" if jmaxproc == 1 else f" (with {jmaxproc} processors)"

    pool = Pool(jmaxproc)
    testcases = []

    def excluded(cwe: str) -> bool:
        if len(jcwes) == 0:
            return False
        else:
            return cwe not in jcwes

    with timing("score-sets" + maxptxt):
        count: int = 0
        juliettests = UF.get_juliet_testcases()
        for cwe in sorted(juliettests):
            if excluded(cwe):
                continue
            print(f"Scoring testcases for cwe {cwe}")
            for subdir in sorted(juliettests[cwe]):
                for t in juliettests[cwe][subdir]:
                    testcases.append((cwe, t, count))

        results = pool.map(score_test, testcases)

    print("\n" + ("=" * 80))
    if len(results) == results.count(0):
        print("All Juliet tests cases were scored successfully.")
    else:
        for x in range(len(results)):
            if results[x] != 0:
                print(f"Error in testcase {testcases[x][0]}")
    print("=" * 80)

    exit(0)


def juliet_investigate(args: argparse.Namespace) -> NoReturn:
    """Lists problematic proof obligations."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    xdelegated: bool = args.xdelegated
    xviolated: bool = args.xviolated
    predicates: List[str] = args.predicates

    projectname = jcwe + "_" + jtest

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    targetpath = projectpath
    contractpath = os.path.join(projectpath, "cch_contracts")

    excludefiles = ["io.c", "main_linux.c", "std_thread.c"]

    pofilter: Callable[["CFunctionPO"], bool] = lambda po: True

    def header(s: str) -> str:
        return (s + ":\n" + ("=" * 80))

    if len(predicates) > 0:

        pofilter = lambda po: po.predicate_name in predicates

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        excludefiles=excludefiles)

    openppos = capp.get_open_ppos()
    violations = [] if xviolated else capp.get_ppos_violated()
    delegated = [] if xdelegated else capp.get_ppos_delegated()

    lines: List[str] = []

    if len(openppos) > 0:
        lines.append(header("Open primary proof obligations"))
        lines.append(
            RP.tag_file_function_pos_tostring(openppos, pofilter=pofilter))
    else:
        lines.append("No open proof obligations found")

    if not xviolated:
        if len(violations) > 0:
            lines.append(header("Primary proof obligations violated"))
            lines.append(
                RP.tag_file_function_pos_tostring(violations, pofilter=pofilter))
        else:
            lines.append("No violated proof obligations found")
            lines.append(
                " (Note that any open proof obligation is potential violation)")

    if not xdelegated:
        if len(delegated):
            lines.append(header("Primary proof obligations delegated"))
            lines.append(
                RP.tag_file_function_pos_tostring(delegated, pofilter=pofilter))
        else:
            lines.append("No delegated proof obligations found")

    print("\n".join(lines))

    exit(0)


def juliet_report_requests(args: argparse.Namespace) -> NoReturn:
    """Outputs open requests for postconditions and global assumptions."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test

    try:
        projectpath = UF.get_juliet_testpath(jcwe, jtest)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    projectname = jcwe + "_" + jtest

    targetpath = projectpath
    contractpath = os.path.join(projectpath, "cch_contracts")

    excludefiles = ["io.c", "main_linux.c", "std_thread.c"]

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        excludefiles=excludefiles)

    stats: Dict[str, int] = {}
    stats["npost"] = 0
    stats["nglobal"] = 0
    stats["ndepppo"] = 0
    stats["ndepspo"] = 0

    lines: List[str] = []

    def report_fn_requests(cfun: "CFunction") -> None:
        if cfun.api.has_outstanding_requests():
            lines.append("\n  " + cfun.name)
            if cfun.api.has_outstanding_postcondition_requests():
                lines.append("   postcondition requests")
                for p in cfun.api.postcondition_requests.values():
                    if p.has_open_pos():
                        lines.append("     " + str(p))
                        stats["npost"] += 1
                        stats["ndepppo"] += len(p.get_open_ppos())
                        stats["ndepspo"] += len(p.get_open_spos())
            if cfun.api.has_outstanding_global_requests():
                lines.append("   global assumption requests:")
                for a in cfun.api.global_assumption_requests.values():
                    if a.has_open_pos():
                        lines.append("    " + str(a))
                        stats["nglobal"] += 1
                        stats["ndepppo"] += len(a.get_open_ppos())
                        stats["ndepspo"] += len(a.get_open_spos())


    def report_requests(cfile: "CFile") -> None:
        if cfile.has_outstanding_fn_api_requests():
            lines.append(cfile.name)
            cfile.iter_functions(report_fn_requests)

    capp.iter_files(report_requests)

    def repline(t: str, v: int) -> str:
        return t.ljust(22) + ":" + str(v).rjust(4)

    lines.append("\n" + ("-" * 80))
    lines.append(repline("Postcondition requests", stats["npost"]))
    lines.append(repline("Global requests", stats["nglobal"]))
    lines.append(repline("Dependent ppos", stats["ndepppo"]))
    lines.append(repline("Dependent spos", stats["ndepspo"]))
    lines.append("-" * 80)

    print("\n".join(lines))

    exit(0)


def juliet_dashboard(args: argparse.Namespace) -> NoReturn:

    # arguments
    optcwe: Optional[str] = args.cwe
    optvariant: Optional[str] = args.variant

    cwerequested = "all" if optcwe is None else optcwe

    try:
        testcases = UF.get_flattened_juliet_testcases()
        variants = UF.get_juliet_variant_descriptions()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if optvariant is not None:
        if optvariant not in variants:
            print("Variant " + optvariant + " not recognized.")
            print("\nControl flow / data flow variants available:")
            print("-" * 80)
            for v in sorted(variants):
                print(v.ljust(5) + variants[v])
            print("-" * 80)
            exit(1)

    stotals: Dict[str, Dict[str, int]] = {}
    stotals["vs"] = {}
    stotals["sc"] = {}
    for c in JTS.violationcategories:
        stotals["vs"][c] = 0
    for c in JTS.safecontrolcategories:
        stotals["sc"][c] = 0

    vppototals = 0
    sppototals = 0
    vppohandled = 0
    sppohandled = 0

    tnamelength = 0
    for cwe in testcases:
        maxlen: int = max(len(t) for t in testcases[cwe]) + 3
        if maxlen > tnamelength:
            tnamelength = maxlen

    lines: List[str] = []
    if optvariant is None:
        lines.append("\nSummary\n")
    else:
        lines.append(
            f"\nSummary for control flow/data flow variant {optvariant}\n")
    lines.append(JTS.scoreheader("CWE", tnamelength))
    lines.append("-" * (tnamelength + 56))

    def dataline(cats: List[str], d: Dict[str, int]) -> str:
        return ("".join([str(d[c]).rjust(5) for c in cats]))


    for cwe in sorted(testcases):
        if not (cwe == cwerequested or cwerequested == "all"):
            continue

        lines.append("\n" + cwe)
        ctotals: Dict[str, Dict[str, int]] = {}
        ctotals["vs"] = {}
        ctotals["sc"] = {}
        for c in JTS.violationcategories:
            ctotals["vs"][c] = 0
        for c in JTS.safecontrolcategories:
            ctotals["sc"][c] = 0

        for cc in sorted(testcases[cwe]):
            testtotals = UF.read_juliet_test_summary(cwe, cc)
            if not (testtotals is None):
                if optvariant is None:
                    totals = testtotals["total"]
                else:
                    if optvariant in testtotals:
                        totals = testtotals[optvariant]
                    else:
                        lines.append(("  " + cc).ljust(tnamelength))
                        continue
                lines.append(
                    ("  " + cc).ljust(tnamelength)
                    + dataline(JTS.violationcategories, totals["vs"])
                    + "  |  "
                    + dataline(JTS.safecontrolcategories, totals["sc"]))

                for c in JTS.violationcategories:
                    cval = totals["vs"][c]
                    ctotals["vs"][c] += cval
                    stotals["vs"][c] += cval
                    vppototals += cval
                    if c in ["V"]:
                        vppohandled += cval

                for c in JTS.safecontrolcategories:
                    cval = totals["sc"][c]
                    ctotals["sc"][c] += cval
                    stotals["sc"][c] += cval
                    sppototals += cval
                    if c in ["S", "X"]:
                        sppohandled += cval

            else:
                lines.append(
                    ("  " + cc).ljust(tnamelength)
                    + ("-" * (44 - int(tnamelength / 2)))
                    + " not found "
                    + ("-" * (44 - int(tnamelength / 2))))

        lines.append("-" * (tnamelength + 56))
        lines.append(
            "total".ljust(tnamelength)
            + dataline(JTS.violationcategories, ctotals["vs"])
            + "  |  "
            + dataline(JTS.safecontrolcategories, ctotals["sc"]))

    lines.append("\n\n")
    lines.append("=" * (tnamelength + 56))
    lines.append(
        "grand total".ljust(tnamelength)
        + dataline(JTS.violationcategories, stotals["vs"])
        + "  |  "
        + dataline(JTS.safecontrolcategories, stotals["sc"]))

    ppototals = vppototals + sppototals
    ppohandled = vppohandled + sppohandled

    def perc(num: int, den: int) -> float:
        return float(num) / float(den) * 100.0 if den > 0 else 0.0

    def iline(s: str, n1: int, n2: int, n3: int) -> str:
        return s.ljust(20) + "".join([str(n).rjust(15) for n in [n1, n2, n3]])

    def fline(s: str, f1: float, f2: float, f3: float) -> str:
        return (
            s.ljust(20)
            + "".join([str("{:.1f}".format(f)).rjust(15) for f in [f1, f2, f3]]))

    vperc = perc(vppohandled, vppototals)
    sperc = perc(sppohandled, sppototals)
    aperc = perc(ppohandled, ppototals)

    lines.append("\n\n")
    lines.append(" ".ljust(28) + "violation       safe-control     total")
    lines.append("-" * 80)
    lines.append(iline("ppos", vppototals, sppototals, ppototals))
    lines.append(iline("reported", vppohandled, sppohandled, ppohandled))
    lines.append(fline("percent reported", vperc, sperc, aperc))
    lines.append("-" * 80)

    print("\n".join(lines))

    exit(0)


def juliet_project_dashboard(args: argparse.Namespace) -> NoReturn:

    # arguments
    optcwe: Optional[str] = args.cwe

    cwerequested = "all" if optcwe is None else optcwe

    try:
        testcases = UF.get_flattened_juliet_testcases()
        variants = UF.get_juliet_variant_descriptions()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    nosummary: List[str] = [] # tests without results
    corrupted: List[str] = [] # tests with invalid results

    ppo_project_totals: Dict[str, Dict[str, int]] = {}
    spo_project_totals: Dict[str, Dict[str, int]] = {}

    ppo_tag_totals: Dict[str, Dict[str, int]] = {}
    spo_tag_totals: Dict[str, Dict[str, int]] = {}

    analysistimes: Dict[str, int] = {}
    projectstats: Dict[str, Tuple[int, int, int]] = {}

    dsmethods = RP.get_dsmethods([])   # discharge methods

    lines: List[str] = []

    for cwe in sorted(testcases):
        if not (cwe == cwerequested or cwerequested == "all"):
            continue

        for test in testcases[cwe]:
            pname = f"{cwe}:{test}"
            path = UF.get_juliet_testpath(cwe, test)
            results = UF.read_project_summary_results(path)
            if results is None:
                nosummary.append(pname)
                continue

            try:
                ppod = results["tagresults"]["ppos"]
                spod = results["tagresults"]["spos"]
            except Exception as e:
                corrupted.append(pname)
                continue

            ppo_project_totals[pname] = {}
            spo_project_totals[pname] = {}

            if "stats" in results:
                # use casts to handle union type in loaded dictionary
                projectstats[pname] = cast(
                    Tuple[int, int, int], results["stats"])
                analysistimes[pname] = cast(int, results["timestamp"])
            else:
                projectstats[pname] = (0, 0, 0)

            for tag in ppod:
                ppod[tag].setdefault("violated", -1)
                ppod[tag].setdefault("contract", -1)
                ppo_tag_totals.setdefault(tag, {})
                for dm in ppod[tag]:
                    ppo_tag_totals[tag].setdefault(dm, 0)
                    ppo_tag_totals[tag][dm] += ppod[tag][dm]

            for tag in spod:
                spod[tag].setdefault("violated", -1)
                spod[tag].setdefault("contract", -1)
                spo_tag_totals.setdefault(tag, {})
                for dm in spod[tag]:
                    spo_tag_totals[tag].setdefault(dm, 0)
                    spo_tag_totals[tag][dm] += spod[tag][dm]

            for dm in dsmethods:
                ppo_project_totals[
                    pname][dm] = sum([ppod[tag][dm] for tag in ppod])
                spo_project_totals[
                    pname][dm] = sum([spod[tag][dm] for tag in spod])

    lines.append("Primary Proof Obligations")
    lines.append("\n".join(RP.totals_to_string(ppo_project_totals)))

    lines.append("\nPrimary Proof Obligations (in percentages)")
    lines.append("\n".join(RP.totals_to_string(ppo_project_totals, False)))

    lines.append("\nSupporting Proof Obligations")
    lines.append("\n".join(RP.totals_to_string(spo_project_totals)))

    lines.append("\nSupporting Proof Obligations")
    lines.append("\n".join(RP.totals_to_string(spo_project_totals, False)))

    lines.append("\nPrimary Proof Obligations")
    lines.append("\n".join(RP.totals_to_string(ppo_tag_totals)))

    lines.append("\nSupporting Proof Obligations")
    lines.append("\n".join(RP.totals_to_string(spo_tag_totals)))

    if len(nosummary) > 0:
        lines.append("\n\nNo summaryu results found for:")
        lines.append("-" * 28)
        lines.append("\n  ".join(p for p in nosummary))
        lines.append("-" * 28)

    maxname = max([len(p) for p in analysistimes])

    lines.append("\nProject statistics:")
    lines.append(
        "analysis date".ljust(16)
        + "  "
        + "project".ljust(maxname)
        + "LOC ".rjust(10)
        + "CLOC".rjust(10)
        + "functions".rjust(10))
    lines.append("-" * (maxname + 48))

    lctotal = 0
    clctotal = 0
    fctotal = 0

    for p in sorted(analysistimes, key=lambda p: analysistimes[p]):
        (lc, clc, fc) = projectstats[p]
        lctotal += lc
        clctotal += clc
        fctotal += fc
        lines.append(
            time.strftime("%Y-%m-%d %H:%M", time.localtime(analysistimes[p]))
            + "  "
            + p.ljust(maxname)
            + str(lc).rjust(10)
            + str(clc).rjust(10)
            + str(fc).rjust(10))
    lines.append("-" * (maxname + 48))
    lines.append(
        ("Total " + str(len(analysistimes)) + " test sets: ").ljust(maxname + 18)
        + str(lctotal).rjust(10)
        + str(clctotal).rjust(10)
        + str(fctotal).rjust(10))

    lines.append("\n\nProof obligation transfer")
    lines.append(
        "\n".join(
            RP.totals_to_presentation_string(
                ppo_project_totals, spo_project_totals, projectstats)))


    print("\n".join(lines))

    exit(0)
