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
"""Implementation of juliet commands in the command-line interpreter."""

import argparse
import json
import os
import shutil
import sys

from typing import Any, Dict, List, NoReturn, Optional, Tuple

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

    lines.append("\n  " + "directory".ljust(44) + "analysis time    score time")
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
    """Convert a juliet tar.gz semantics file into new format."""

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
        projectpath, projectname, projectpath, contractpath)

    def save_xrefs(f):
        capp.indexmanager.save_xrefs(
            capp.projectpath, projectname, None, f.name, f.index)
        
    linker = CLinker(capp)
    linker.link_compinfos()
    linker.link_varinfos()
    capp.iter_files(save_xrefs)
    linker.save_global_compinfos()

    capp = CApplication(
        projectpath, projectname, projectpath, contractpath)

    am = AnalysisManager(capp, verbose=verbose)    

    try:
        am.create_app_primary_proofobligations(processes=jmaxproc)
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

    def filefilter(filename):
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

    print("No summary found")
    exit(0)


def juliet_report_file(args: argparse.Namespace) -> NoReturn:
    """Rerports on a single c file within a juliet test."""

    # arguments
    jcwe: str = args.cwe
    jtest: str = args.test
    jcfilename_c: str = args.filename

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

    print(RP.file_code_tostring(cfile, pofilter=pofilter))

    print(RP.file_proofobligation_stats_tostring(cfile))    

    exit(0)
        
                                
def juliet_score(args: argparse.Namespace) -> NoReturn:
    """Prints out the score for a single juliet test."""

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

    d = UF.get_juliet_scorekey(jcwe, jtest)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    testset = JulietTestSetRef(d)

    julietppos = JTS.get_julietppos(testset)

    ppopairs = JTS.get_ppo_pairs(julietppos, capp)
    print(JTS.testppo_results_tostring(ppopairs, capp))

    testsummary: Dict[Any, Any] = {}
    JTS.initialize_testsummary(testset, testsummary)
    JTS.fill_testsummary(ppopairs, testsummary, capp)
    totals = JTS.get_testsummarytotals(testsummary)

    print(JTS.testsummary_tostring(testsummary, totals))
          
    exit(0)
