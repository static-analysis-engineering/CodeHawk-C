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
from chc.app.CPrettyPrinter import CPrettyPrinter

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager
import chc.cmdline.jsonresultutil as JU

from chc.linker.CLinker import CLinker

import chc.reporting.ProofObligations as RP

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel

if TYPE_CHECKING:
    from chc.app.CAttributes import CAttributes
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CInstr import CInstr
    from chc.app.CStmt import CInstrsStmt, CStmt
    from chc.app.CTyp import (
        CTypComp, CTypFloat, CTypFun, CTypInt, CTypPtr)
    from chc.proof.CFunctionPO import CFunctionPO


def print_error(m: str) -> None:
    sys.stderr.write(("*" * 80) + "\n")
    sys.stderr.write("F:" + m + "\n")
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
    keep_system_includes: bool = args.keep_system_includes
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

    parsemanager = ParseManager(
        projectpath, projectname, targetpath, keep_system_includes=keep_system_includes)
    parsemanager.remove_semantics()
    parsemanager.initialize_paths()
    parsemanager.parse_with_ccommands(compilecommands, copyfiles=True)
    parsemanager.save_semantics()

    exit(0)


def cproject_scan_op(args: argparse.Namespace) -> NoReturn:

    # arguments
    tgtpath: str = args.tgtpath
    projectname: str = args.projectname
    jsonoutput: bool = args.json
    outputfilename: Optional[str] = args.output
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

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
        msg="c-project scan-output-parameters invoked")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath)

    def has_const_attribute(attrs: "CAttributes") -> bool:
        for attr in attrs.attributes:
            if "const" in attr.name:
                return True
        return False

    cfilecandidates: List[Dict[str, Any]] = []
    opcandidates: List[Dict[str, Any]] = []
    disqualifiersum: Dict[str, int] = {}
    qualifiersum: Dict[str, int] = {}
    structsum: Dict[str, int] = {}

    totalfunctioncount = 0
    totalptrargcount = 0
    totalcandidatefns = 0

    for cfile in capp.cfiles:
        if cfile.cfilepath is not None:
            cfilename = os.path.join(cfile.cfilepath, cfile.cfilename)
        else:
            cfilename = cfile.cfilename

        candidates: List[Dict[str, Any]] = []
        for cfun in cfile.gfunctions.values():
            if cfun.varinfo.vname == "main":
                continue
            pp = CPrettyPrinter()
            fndecl = pp.function_declaration_str(cfun.varinfo).strip()
            cfuntyp = cfun.varinfo.vtype
            if not cfuntyp.is_function:
                continue
            cfuntyp = cast("CTypFun", cfuntyp)
            cfunargs = cfuntyp.funargs
            if cfunargs is None:
                continue
            cfunarguments = cfunargs.arguments
            if not any(cfunarg.typ.is_pointer for cfunarg in cfunarguments):
                continue
            candidate: Dict[str, Any] = {}
            candidate["name"] = cfun.vname
            candidate["signature"] = fndecl
            ptrargs = candidate["ptrargs"] = []
            for (index, cfunarg) in enumerate(cfunarguments):
                argtyp = cfunarg.typ.expand()
                if argtyp.is_pointer:
                    totalptrargcount += 1
                    disqualifiers: List[str] = []
                    t = cast("CTypPtr", argtyp).pointedto_type.expand()
                    ptrarg: Dict[str, Any] = {}
                    ptrarg["index"] = index
                    ptrarg["name"] = cfunarg.name
                    ptrarg["target-type"] = str(t)
                    if cfunarg.typ.attributes.length > 0:
                        ptrarg["attributes"] = (
                            [str(attr) for attr in cfunarg.typ.attributes.attributes])
                        if has_const_attribute(cfunarg.typ.attributes):
                            disqualifiers.append("const")
                    if t.attributes.length > 0:
                        ptrarg["attributes"] = (
                            [str(attr) for attr in t.attributes.attributes])
                        if has_const_attribute(t.attributes):
                            disqualifiers.append("const")
                        disqualifiersum.setdefault("const", 0)
                        disqualifiersum["const"] += 1
                    if t.is_int:
                        ptrarg["kind"] = ["int", cast("CTypInt", t).ikind]
                        if "ichar" in ptrarg["kind"]:
                            disqualifiers.append("ichar")
                            disqualifiersum.setdefault("char", 0)
                            disqualifiersum["char"] == 1
                        elif "iuchar" in ptrarg["kind"]:
                            disqualifiers.append("iuchar")
                            disqualifiersum.setdefault("char", 0)
                            disqualifiersum["char"] += 1
                    elif t.is_float:
                        ptrarg["kind"] = ["float", cast("CTypFloat", t).fkind]
                    elif t.is_void:
                        ptrarg["kind"] = ["void"]
                        disqualifiers.append("void")
                        disqualifiersum.setdefault("void", 0)
                        disqualifiersum["void"] += 1
                    elif t.is_pointer:
                        ptrarg["kind"] = ["pointer"]
                        disqualifiers.append("pointer")
                        disqualifiersum.setdefault("pointer", 0)
                        disqualifiersum["pointer"] += 1
                    elif t.is_struct:
                        structname = cast("CTypComp", t).name
                        ptrarg["kind"] = ["struct", structname]
                        structsum.setdefault(structname, 0)
                        structsum[structname] += 1
                    elif t.is_union:
                        ptrarg["kind"] = ["union", cast("CTypComp", t).name]
                        disqualifiers.append("union")
                        disqualifiersum.setdefault("union", 0)
                        disqualifiersum["union"] += 1
                    else:
                        ptrarg["kind"] = ["other"]
                    if len(disqualifiers) > 0:
                        ptrarg["disqualifiers"] = disqualifiers
                    else:
                        opcandidate: Dict[str, Any] = {}
                        opcandidate["file"] = cfilename
                        opcandidate["function"] = cfun.varinfo.vname
                        opcandidate["arg-index"] = index
                        opcandidate["arg-name"] = cfunarg.name
                        opcandidate["arg-target-type"] = str(t)
                        if t.is_struct:
                            opcandidate["struct-name"] = cast("CTypComp", t).name
                        opcandidates.append(opcandidate)
                    ptrargs.append(ptrarg)
            candidates.append(candidate)
            totalcandidatefns += 1
        cfilecandidate: Dict[str, Any] = {}
        cfilecandidate["filename"] = cfilename
        cfilecandidate["candidates"] = candidates
        cfilecandidate["function-count"] = len(cfile.gfunctions.keys())
        totalfunctioncount += len(cfile.gfunctions.keys())
        cfilecandidates.append(cfilecandidate)

    results: Dict[str, Any] = {}
    results["files"] = cfilecandidates
    results["op-candidates"] = opcandidates
    results["struct-summary"] = structsum
    results["disqualifier-summary"] = disqualifiersum
    results["file-count"] = len(list(capp.cfiles))
    results["total-function-count"] = totalfunctioncount
    results["total-function-candidate-count"] = totalcandidatefns
    results["total-argptr-count"] = totalptrargcount
    results["op-candidate-count"] = len(opcandidates)

    if jsonoutput:
        jsonresult = JU.cproject_output_parameters_to_json_result(projectname, results)
        jsonok = JU.jsonok("scan_output_parameters", jsonresult.content)
        if outputfilename is not None:
            with open(outputfilename, "w") as fp:
                json.dump(jsonok, fp, indent=2)
        else:
            resultstring = json.dumps(jsonok, indent=2)
            print(resultstring)

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
    keep_system_includes: bool = args.keep_system_includes
    maxprocesses: int = args.maxprocesses
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode
    excludefiles: List[str] = args.exclude

    if excludefiles is None:
        excludefiles = []

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
        projectpath,
        projectname,
        targetpath,
        contractpath,
        keep_system_includes=keep_system_includes,
        excludefiles=excludefiles)

    def save_xrefs(f: "CFile") -> None:
        capp.indexmanager.save_xrefs(
            capp.projectpath, projectname, f.cfilepath, f.cfilename, f.index)

    linker = CLinker(capp)
    linker.link_compinfos()
    linker.link_varinfos()
    capp.iter_files(save_xrefs)
    linker.save_global_compinfos()

    capp = CApplication(
        projectpath,
        projectname,
        targetpath,
        contractpath,
        keep_system_includes=keep_system_includes,
        excludefiles=excludefiles)

    am = AnalysisManager(capp, verbose=True, keep_system_includes=keep_system_includes)

    with timing("analysis"):

        try:
            am.create_app_primary_proofobligations(processes=maxprocesses)
            capp.reinitialize_tables()
            capp.collect_post_assumes()
        except UF.CHError as e:
            print(str(e.wrap()))
            exit(1)

        for i in range(1):
            am.generate_and_check_app("visp", processes=maxprocesses)
            capp.reinitialize_tables()
            capp.update_spos()

        for i in range(5):
            capp.update_spos()
            am.generate_and_check_app("visp", processes=maxprocesses)
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
