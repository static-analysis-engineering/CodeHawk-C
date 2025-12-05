# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2024-2025  Aarno Labs, LLC
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
"""Implementation of commands for processing c projects in the CLI."""

import argparse
import codecs
import json
import os
import shutil
import subprocess
import sys
import time

from contextlib import contextmanager

from typing import (
    Any, cast, Dict, Generator, List, Optional, NoReturn, Tuple, TYPE_CHECKING)

from chc.app.CApplication import CApplication

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager
import chc.cmdline.jsonresultutil as JU

from chc.linker.CLinker import CLinker

import chc.reporting.ProofObligations as RP

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CInstr import CInstr
    from chc.app.CStmt import CInstrsStmt, CStmt
    from chc.invariants.CInvariantFact import CInvariantNRVFact
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
def timing(activity: str) -> Generator:
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


def cproject_parse_project(args: argparse.Namespace) -> NoReturn:

    # arguments
    projectpath: str = args.path
    projectname: str = args.projectname
    opttgtpath: Optional[str] = args.tgtpath
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        UF.check_parser()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if not os.path.isdir(projectpath):
        print_error(f"Project directory {projectpath} not found")
        exit(1)

    compilecommandsfile = os.path.join(projectpath, "compile_commands.json")
    if not os.path.isfile(compilecommandsfile):
        print_error(f"File {compilecommandsfile} not found")
        exit(1)

    projectpath = os.path.abspath(projectpath)

    if opttgtpath is not None:
        if not os.path.isdir(opttgtpath):
            print_error(f"Target directory {opttgtpath} not found")
            exit(1)

        targetpath = os.path.abspath(opttgtpath)
    else:
        targetpath = projectpath

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="c-project parse invoked")

    chklogger.logger.info("Target path: %s", targetpath)

    with codecs.open(compilecommandsfile, "r", encoding="utf-8") as fp:
        compilecommands = json.load(fp)

    if len(compilecommands) == 0:
        print_error("The compile_commands.json file was found empty")
        exit(1)

    parsemanager = ParseManager(projectpath, projectname, targetpath)
    parsemanager.remove_semantics()
    parsemanager.initialize_paths()
    parsemanager.parse_with_ccommands(compilecommands, copyfiles=True)
    parsemanager.save_semantics()

    exit(0)


def cproject_mk_headerfile(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    userdatafile: Optional[str] = args.userdata
    includepaths: List[str] = args.includepaths
    includedirs: List[str] = args.includedirs
    excludepaths: List[str] = args.excludepaths
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    if not os.path.isdir(tgtpath):
        print_error(f"Target directory {tgtpath} not found")
        exit(1)

    if userdatafile and not os.path.isfile(userdatafile):
        print_error(f"Userdata file {userdatafile} not found")
        exit(1)

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(projectpath, "cch_contracts")

    if userdatafile:
        with open(userdatafile, "r") as fp:
            userdata = json.load(fp).get("userdata", {})
    else:
        userdata = {}

    fnnames: Dict[str, str] = userdata.get("function-names", {})
    gvarnames: Dict[str, str] = userdata.get("symbolic-addresses", {})

    fnnames = {v: k for (k, v) in fnnames.items()}
    gvarnames = {v: k for (k, v) in gvarnames.items()}

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="c-project mk-headerfile invoked")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    lines: List[str] = []

    def is_included(path: Optional[str]) -> bool:
        if path is None:
            return True
        if len(includepaths) > 0:
            return any(path.startswith(p) for p in includepaths)
        elif len(includedirs) > 0:
            return path in includedirs
        elif len(excludepaths) > 0:
            return not (any(path.startswith(p) for p in excludepaths))
        else:
            return True

    for cfile in capp.cfiles:
        if not is_included(cfile.cfilepath):
            continue
        fheader = cfile.header_declarations(gvarnames, fnnames)
        lines.append(fheader)

    print("\n\n".join(lines))

    exit(0)


def cproject_analyze_project(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    maxprocesses: int = args.maxprocesses
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode
    excludefiles: List[str] = args.exclude

    if not os.path.isdir(tgtpath):
        print_error(f"Target directory {tgtpath} not found")
        exit(1)

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(projectpath, "cch_contracts")

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="c-project analyze invoked")

    try:
        UF.check_cch_semantics(projectpath, projectname, deletesemantics=True)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, excludefiles=excludefiles)

    def save_xrefs(f: "CFile") -> None:
        capp.indexmanager.save_xrefs(
            capp.projectpath, projectname, f.cfilepath, f.cfilename, f.index)

    linker = CLinker(capp)
    linker.link_compinfos()
    linker.link_varinfos()
    capp.iter_files(save_xrefs)
    linker.save_global_compinfos()

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, excludefiles=excludefiles)

    am = AnalysisManager(capp, verbose=True)

    with timing("analysis"):

        try:
            am.create_app_primary_proofobligations(processes=maxprocesses)
            capp.reinitialize_tables()
            capp.collect_post_assumes()
        except UF.CHError as e:
            print(str(e.wrap()))
            exit(1)

        for i in range(1):
            am.generate_and_check_app("llrvisp", processes=maxprocesses)
            capp.reinitialize_tables()
            capp.update_spos()

        for i in range(5):
            capp.update_spos()
            am.generate_and_check_app("llrvisp", processes=maxprocesses)
            capp.reinitialize_tables()

    timestamp = os.stat(UF.get_cchpath(targetpath, projectname)).st_ctime

    result = RP.project_proofobligation_stats_to_dict(capp)
    result["timestamp"] = timestamp
    result["project"] = projectpath
    UF.save_project_summary_results(targetpath, projectname, result)
    UF.save_project_summary_results_as_xml(targetpath, projectname, result)

    exit(0)


def cproject_report(args: argparse.Namespace) -> NoReturn:
    """CLI command to output statistics on proof obligations for the project."""

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath

    result = UF.read_project_summary_results(targetpath, projectname)
    if result is not None:
        print(RP.project_proofobligation_stats_dict_to_string(result))
        exit(0)

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    contractpath = os.path.join(targetpath, "chc_contracts")
    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    timestamp = os.stat(UF.get_cchpath(targetpath, projectname)).st_ctime
    fresult = RP.project_proofobligation_stats_to_dict(capp)
    fresult["timestamp"] = timestamp
    fresult["project"] = projectpath
    UF.save_project_summary_results(targetpath, projectname, fresult)
    UF.save_project_summary_results_as_xml(targetpath, projectname, fresult)

    result = UF.read_project_summary_results(targetpath, projectname)
    if result is not None:
        print(RP.project_proofobligation_stats_dict_to_string(result))
    else:
        print_error("Results were not readable")
        exit(1)

    exit(0)


def cproject_report_file(args: argparse.Namespace) -> NoReturn:
    """CLI command to output the results for a single file in a c project."""

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    filename: str = args.filename
    showcode: bool = args.showcode
    showopen: bool = args.open
    showinvariants: bool = args.showinvariants

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    cfilename_c = os.path.basename(filename)
    cfilename = cfilename_c[:-2]
    cfilepath = os.path.dirname(filename)

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    contractpath = os.path.join(targetpath, "chc_contracts")
    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    if capp.has_file(filename[:-2]):
        cfile = capp.get_file(filename[:-2])
    else:
        print_error(f"File {filename} not found")
        exit(1)

    def pofilter(po: "CFunctionPO") -> bool:
        if showopen:
            return not po.is_closed
        else:
            return True

    if showcode:
        print(RP.file_code_tostring(
            cfile, pofilter=pofilter, showinvs=showinvariants))

    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)


def cproject_query_invariants(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    filename: str = args.filename
    xfunction: str = args.function
    xline: int = args.line

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    cfilename_c = os.path.basename(filename)
    cfilename = cfilename_c[:-2]
    cfilepath = os.path.dirname(filename)

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    contractpath = os.path.join(targetpath, "chc_contracts")
    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    if capp.has_file(filename[:-2]):
        cfile = capp.get_file(filename[:-2])
    else:
        print_error(f"File {filename} not found")
        exit(1)

    if not cfile.has_function_by_name(xfunction):
        print_error("No function found with name " + xfunction)
        exit(1)

    cfun = cfile.get_function_by_name(xfunction)
    ppos = cfun.get_ppos()
    contexts = {ppo.context for ppo in ppos if ppo.line == xline}

    print("Invariants for function " + xfunction + ", line " + str(xline))
    if len(contexts) == 0:
        print("\nNo ast positions found with invariants on line " + str(xline) + ".")
        exit(0)

    for ctxt in contexts:
        print("\nAST position: " + str(ctxt))
        print("-" * (len(str(ctxt)) + 14))
        invs = cfun.invarianttable.get_sorted_invariants(ctxt)
        nrvfacts: List[str] = []
        for inv in invs:
            if inv.is_nrv_fact:
                inv = cast("CInvariantNRVFact", inv)
                if not inv.variable.is_check_variable:
                    nrvfacts.append(str(inv))
        print("\n".join(nrvfacts))

    exit(0)


def cproject_count_stmts(args: argparse.Namespace) -> NoReturn:
    """CLI command to output size statistics for a c project."""

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    verbose: bool = args.verbose

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(targetpath, "chc_contracts")

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    result: Dict[str, Dict[str, Dict[str, int]]] = {}
    asminstrs: Dict[str, List["CInstr"]] = {}  # function name -> instr
    unknowninstrs: Dict[str, List["CInstr"]] = {}   # function name -> instr

    def f(cfile: "CFile") -> None:
        fname = cfile.name
        result.setdefault(fname, {})

        for cfun in cfile.get_functions():
            fnname = cfun.name
            if fnname not in result[fname]:
                result[fname][fnname] = {}
                result[fname][fnname]["stmts"] = 0
                result[fname][fnname]["calls"] = 0
                result[fname][fnname]["assigns"] = 0
                result[fname][fnname]["asms"] = 0

            def h(stmt: "CStmt"):
                result[fname][fnname]["stmts"] += 1

                if stmt.is_instrs_stmt:
                    stmt = cast("CInstrsStmt", stmt)
                    for instr in stmt.instrs:
                        entry = result[fname][fnname]
                        if instr.is_assign:
                            entry["assigns"] += 1
                        elif instr.is_call:
                            entry["calls"] += 1
                        elif instr.is_asm:
                            entry["asms"] += 1
                            asminstrs.setdefault(fnname, [])
                            asminstrs[fnname].append(instr)
                        else:
                            unknowninstrs.setdefault(fnname, [])
                            unknowninstrs[fnname].append(instr)

                stmt.iter_stmts(h)

            cfun.sbody.iter_stmts(h)

    capp.iter_files(f)

    lines: List[str] = []

    if verbose:
        for fname in sorted(result):
            lines.append(fname)
            for fnname in sorted(result[fname]):
                lines.append("  " + fnname)
                for s in sorted(result[fname][fnname]):
                    lines.append(
                        "    "
                        + str(s).ljust(10)
                        + ": "
                        + str(result[fname][fnname][s]).rjust(4))

    nStmts: int = 0
    nCalls: int = 0
    nAssigns: int = 0
    nAsms: int = 0

    for fname in result:
        for fnname in result[fname]:
            entry = result[fname][fnname]
            nStmts += entry["stmts"]
            nCalls += entry["calls"]
            nAssigns += entry["assigns"]
            nAsms += entry["asms"]

    def statline(s: str, n: int) -> str:
        return (s.ljust(27) + ": " + str(n).rjust(5))

    lines.append("=" * 80)
    lines.append(statline("Statements", nStmts))
    lines.append(statline("  Call instructions", nCalls))
    lines.append(statline("  Assignment instructions", nAssigns))
    lines.append(statline("  Assembly instructions", nAsms))

    if len(asminstrs) > 0:
        lines.append("\nAssembly instructions")
        lines.append("-" * 80)
        for (fnname, instrs) in asminstrs.items():
            lines.append("Function " + fnname + ":")
            for i in instrs:
                lines.append(str(i))
        lines.append("-" * 80)

    if len(unknowninstrs) > 0:
        lines.append("\nUnknown instructions")
        lines.append("-" * 80)
        for (fnname, instrs) in unknowninstrs.items():
            lines.append("Function " + fnname)
            for i in instrs:
                lines.append(str(i))
        lines.append("-" * 80)

    print("\n".join(lines))

    exit(0)


def cproject_make_callgraph(args: argparse.Namespace) -> NoReturn:
    """CLI command to output (and optionally save) the callgraph."""

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    save: Optional[str] = args.save

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(targetpath, "chc_contracts")

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    result: Dict[str, Dict[str, Dict[str, int]]] = {}
    revresult: Dict[str, Dict[str, int]] = {}

    def collect_fn_callees(cfun: "CFunction") -> None:
        callees = [str(i.callee) for i in cfun.call_instrs]
        fnresult = result[cfun.name] = {}
        fncallees = fnresult["callees"] = {}
        for c in callees:
            fncallees.setdefault(c, 0)
            fncallees[c] += 1
            revresult.setdefault(c, {})
            revresult[c].setdefault(cfun.name, 0)
            revresult[c][cfun.name] += 1

    def collect_fi_callees(cfile: "CFile") -> None:
        cfile.iter_functions(collect_fn_callees)

    capp.iter_files(collect_fi_callees)

    lines: List[str] = []

    lines.append("Callgraph")
    lines.append("=" * 80)
    for name in sorted(result):
        lines.append("\n" + name)
        for c in sorted(result[name]["callees"]):
            lines.append(
                "  "
                + str(result[name]["callees"][c]).rjust(4)
                + "  "
                + str(c))

    lines.append("\nReverse callgraph")
    lines.append("=" * 80)
    for name in sorted(revresult):
        lines.append("\n" + name)
        for c in sorted(revresult[name]):
            lines.append(
                "  "
                + str(revresult[name][c]).rjust(4)
                + "  "
                + str(c))

    if save is not None:
        saveresult: Dict[str, Any] = {}
        saveresult["callgraph"] = result
        saveresult["rev-callgraph"] = revresult
        with open(save + ".json", "w") as fp:
            json.dump(saveresult, fp)

    print("\n".join(lines))

    exit(0)


def cproject_collect_call_arguments(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(targetpath, "chc_contracts")

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    # callee -> (file, caller) -> arguments
    result: Dict[str, Dict[Tuple[int, str, str], List[str]]] = {}

    counter: int = 0
    for cfile in capp.cfiles:
        for cfun in cfile.get_functions():
            for instr in cfun.call_instrs:
                callee = str(instr.callee)
                callargs = instr.callargs
                result.setdefault(callee, {})
                result[callee][(counter, cfile.cfilename, cfun.name)] = [
                    str(i) for i in callargs]
                counter += 1

    lines: List[str] = []

    for callee in sorted(result):
        lines.append("\n" + callee)
        lines.append("-" * len(callee))
        for (index, cfilename, caller) in sorted(result[callee]):
            calltxt = (
                callee
                + "("
                + ", ".join(result[callee][(index, cfilename, caller)])
                + ")")
            lines.append(
                ("[" + cfilename + ".c:" + caller + "] ").ljust(35)
                + calltxt)

    print("\n".join(lines))

    exit(0)


def cproject_missing_summaries(args: argparse.Namespace) -> NoReturn:
    """CLI command to output library functions without summaries."""

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    showall: bool = args.all

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(targetpath, "chc_contracts")

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    resultheaders: Dict[str, Dict[str, int]] = {}
    result: Dict[str, int] = {}

    def get_fn_missing_summaries(cfun: "CFunction") -> None:
        missingsummaries = cfun.api.missing_summaries
        for s in missingsummaries:
            names = s.split("/")
            if len(names) == 2:
                resultheaders.setdefault(names[0], {})
                resultheaders[names[0]].setdefault(names[1], 0)
                resultheaders[names[0]][names[1]] += 1
            else:
                result.setdefault(s, 0)
                result[s] += 1

    def get_fi_missing_summaries(cfile: "CFile") -> None:
        cfile.iter_functions(get_fn_missing_summaries)

    capp.iter_files(get_fi_missing_summaries)

    lines: List[str] = []

    lines.append("Headers")
    lines.append("=" * 80)
    for h in sorted(resultheaders):
        if not showall and capp.is_application_header(h):
            continue
        lines.append("\n" + h)
        for m in sorted(resultheaders[h]):
            lines.append("  " + str(resultheaders[h][m]).rjust(4) + "  " + m)

    if len(result) > 0:
        lines.append("\n\nOthers")
        for m in sorted(result):
            lines.append(str(result[m]).rjust(4) + "  " + m)

    print("\n".join(lines))

    exit(0)


def cproject_create_header_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname

    targetpath = os.path.abspath(tgtpath)
    projectpath = targetpath
    contractpath = os.path.join(targetpath, "chc_contracts")

    if not UF.has_analysisresults_path(targetpath, projectname):
        print_error(
            f"No analysis results found for {projectname} in {targetpath}")
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    for cfile in capp.cfiles:
        for gfun in cfile.gfunctions.values():
            if gfun.is_system_function:
                continue
            print(str(gfun.varinfo))

    exit(0)
