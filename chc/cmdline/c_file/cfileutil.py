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
"""Command-line interface to the CodeHawk C Analyzer.

The functions in this module support the commands available in the single-file
mode of the CodeHawk-C analyzer.

Naming conventions used in this module:

- pcfilename_c    full-path name of cfile analyzed
- cfilename       base name of cfile analyzed (without extension)
- cfilename_c     idem, with .c extension
- projectpath     full-path of directory in which cfilename_c resides
- targetpath      full-path of directory in which results are saved
- projectname     name under which results are saved

Unless specified otherwise the following defaults are used:

- targetpath : set equal to projectpath
- projectname: set to cfilename

The results are stored in the directory

  targetpath/projectname.cch

"""

import argparse
import json
import os
import shutil
import subprocess
import sys

from typing import Callable, List, NoReturn, Optional, TYPE_CHECKING

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager
import chc.cmdline.jsonresultutil as JU

from chc.app.CApplication import CApplication

import chc.reporting.ProofObligations as RP

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel

if TYPE_CHECKING:
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


def cfile_parse_file(args: argparse.Namespace) -> NoReturn:
    """Parses a single file and saves the results in the .cch directory.

    This command runs the gcc preprocessor on the single c-file presented and
    then calls the ocaml C analyzer to parse (using the goblint cil parser)
    the resulting .i file into ocaml data structures. These data structures
    are saved in the <projectname>.cch/a directory. The original c-file and
    the preprocessed i-file are saved in the <projectname>.cch/s directory.

    Note: When run on a MacOSX platform, the CIL parser may not be able to
    handle the syntax of the MacOS standard header files, if these are included
    in the c-file.
    """

    # arguments
    pcfilename: str = os.path.abspath(args.filename)
    opttgtpath: Optional[str] = args.tgtpath
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        UF.check_parser()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if not os.path.isfile(os.path.abspath(pcfilename)):
        print_error("C source code file " + pcfilename + " not found")
        exit(1)

    if not pcfilename.endswith(".c"):
        print_error("C source code file should have extension .c")
        exit(1)

    projectpath = os.path.dirname(pcfilename)
    targetpath = projectpath if opttgtpath is None else opttgtpath
    cfilename_c = os.path.basename(pcfilename)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    if not os.path.isdir(targetpath):
        print_error("Target directory: " + targetpath + " does not exist")
        exit(1)

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="cfile parse invoked")

    chklogger.logger.info("Target path: %s", targetpath)

    parsemanager = ParseManager(projectpath, projectname, targetpath)
    parsemanager.remove_semantics()
    parsemanager.initialize_paths()

    try:
        cfilename_i = parsemanager.preprocess_file_with_gcc(cfilename_c)
        result = parsemanager.parse_ifile(cfilename_i)
        if result != 0:
            print("*" * 80)
            print("Error in parsing " + cfilename_c)
            if Config().platform == "macOS":
                print("  (Problem may be related to standard header files on macOS)")
            print("*" * 80)
            exit(1)
    except OSError as e:
        print_error("Error when parsing file: " + str(e))
        exit(1)

    parsemanager.save_semantics()

    chklogger.logger.info("cfile parse completed")

    exit(0)


def cfile_analyze_file(args: argparse.Namespace) -> NoReturn:
    """Analyzes a single c-file and saves the results in the .cch directory.

    This command runs the ocaml C analyzer to

    1. generate proof obligations for the declarations and functions represented
       by the data structures saved by the parse command,
    2. generate invariants for these functions (targeted for the proof obligations),
    3. attempts to discharge the generated proof obligations with the generated
       invariants
    4. generates supporting proof obligations for proof obligations that were
       discharged against an api assumption (on the python side)
    5. repeats steps 2-4 until convergence (or some preset maximum is reached)

    All results are saved in the <projectname>.cch/a/ directory

    """

    # arguments
    xcfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    wordsize: int = args.wordsize
    verbose: bool = args.verbose
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectpath = os.path.dirname(os.path.abspath(xcfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    targetpath = os.path.abspath(targetpath)
    cfilename_ext = os.path.basename(xcfilename)
    cfilename = cfilename_ext[:-2]
    projectname = cfilename

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="Command cfile analyze was invoked")

    chklogger.logger.info(
        "Project path: %s; target path: %s", projectpath, targetpath)

    parsearchive = UF.get_parse_archive(targetpath, projectname)

    if not os.path.isfile(parsearchive):
        print_error("Please run parser first on c file")
        exit(1)

    cchpath = UF.get_cchpath(targetpath, projectname)

    if os.path.isdir(cchpath):
        chklogger.logger.info("Old analysis results: %s are removed", cchpath)
        shutil.rmtree(cchpath)

    if os.path.isfile(parsearchive):
        chklogger.logger.info("Directory is changed to %s", targetpath)
        os.chdir(targetpath)
        tarname = os.path.basename(parsearchive)
        cmd = ["tar", "xfz", os.path.basename(tarname)]
        chklogger.logger.info("Semantics is extracted from %s", tarname)
        result = subprocess.call(cmd, cwd=targetpath, stderr=subprocess.STDOUT)
        if result != 0:
            print_error("Error in extracting " + tarname)
            exit(1)
        chklogger.logger.info(
            "Semantics was successfully extracted from %s", tarname)

    contractpath = os.path.join(targetpath, "chc_contracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)

    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    am = AnalysisManager(capp, verbose=verbose, wordsize=wordsize)

    am.create_file_primary_proofobligations(cfilename)
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    am.generate_and_check_file(cfilename, "llrvisp")
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    for k in range(5):
        capp.update_spos()
        am.generate_and_check_file(cfilename, "llrvisp")
        am.reset_tables(cfile)

    chklogger.logger.info("cfile analyze completed")

    exit(0)


def cfile_report_file(args: argparse.Namespace) -> NoReturn:
    """Reports the analysis results for a single file.

    This command loads the analysis results saved by the analysis command and
    prints the result statistics (in terms of proof obligations discharged),
    and optionally prints the indivual proof obligations embedded in the
    original source code (if available from the <projectname>.cch/s/ directory).

    """

    # arguments
    xcfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    cshowcode: bool = args.showcode
    cfunctions: Optional[List[str]] = args.functions
    copen: bool = args.open
    jsonoutput: bool = args.json
    outputfile: Optional[str] = args.output
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectpath = os.path.dirname(os.path.abspath(xcfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    targetpath = os.path.abspath(targetpath)
    cfilename_c = os.path.basename(xcfilename)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="Command cfile report was invoked")

    cchpath = UF.get_cchpath(targetpath, projectname)
    contractpath = os.path.join(targetpath, "chc_contracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    if jsonoutput:
        jsonresult = JU.file_proofobligations_to_json_result(cfile)
        if jsonresult.is_ok:
            jsonokresult = JU.jsonok("fileproofobligations", jsonresult.content)
            if outputfile:
                with open(outputfile + ".json", "w") as fp:
                    json.dump(jsonokresult, fp, indent=2)
            else:
                print(json.dumps(jsonokresult, indent=2))
        exit(0)

    if cfunctions is None:
        if cshowcode:
            if args.open:
                pofilter = lambda po: (not po.is_closed)
            else:
                pofilter = lambda po: True

            print(RP.file_code_tostring(cfile, pofilter=pofilter))

        print(RP.file_proofobligation_stats_tostring(cfile))
        exit(0)

    for fnname in cfunctions:
        if cfile.has_function_by_name(fnname):
            cfun = cfile.get_function_by_name(fnname)

            if args.open:
                pofilter = lambda po: (not po.is_closed)
            else:
                pofilter = lambda po: True

            print(RP.function_code_tostring(cfun, pofilter=pofilter))

    print(RP.file_proofobligation_stats_tostring(cfile))
    exit(0)


def cfile_investigate_file(args: argparse.Namespace) -> NoReturn:
    """Shows a list of open, delegated, and violated proof obligations.

    The proof obligations are presented grouped by proof obliigation type and
    function. The proof obligation types can be optionally restricted by listing
    the proof obliigations of interest (e.g., not-null) explicitly.
    """

    # arguments
    xcfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    predicates: Optional[List[str]] = args.predicates
    referrals: bool = args.referrals
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectpath = os.path.dirname(os.path.abspath(xcfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    targetpath = os.path.abspath(targetpath)
    cfilename_c = os.path.basename(xcfilename)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="Command cfile report was invoked")

    cchpath = UF.get_cchpath(targetpath, projectname)
    contractpath = os.path.join(targetpath, "chc_contracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    pofilter: Callable[["CFunctionPO"], bool] = lambda po: True

    if predicates is not None:

        # need to reassign predicates to satisfy mypy
        xpredicates: List[str] = predicates
        pofilter = lambda po: po.predicate_name in xpredicates

    openppos = cfile.get_open_ppos()
    violations = cfile.get_ppos_violated()
    delegated = cfile.get_ppos_delegated()

    # TODO: add spos

    lines: List[str] = []

    def header(s: str) -> str:
        return (s + ":\n" + ("=" * 80))

    if len(openppos) > 0:
        lines.append(header("Open primary proof obligations"))
        lines.append(RP.tag_file_function_pos_tostring(openppos, pofilter=pofilter))

    if len(violations) > 0:
        lines.append(header("Primary proof obligations violated"))
        lines.append(RP.tag_file_function_pos_tostring(
            violations, pofilter=pofilter))

    if len(delegated) > 0:
        lines.append(header("Primary proof obligations delegated"))
        lines.append(RP.tag_file_function_pos_tostring(delegated, pofilter=pofilter))

    if referrals:

        # TODO: associate with proof obligation

        lines.append(header("Referrals"))
        result: List["CFunctionPO"] = []
        for ppo in openppos:
            if ppo.has_referral_diagnostic():
                result.append(ppo)

        for ppo in result:
            referral = ppo.get_referral_diagnostics()
            for k in referral:
                lines.append(f"  {k}: {referral[k]}")

    print("\n".join(lines))

    exit(0)


def cfile_testlibc_summary(args: argparse.Namespace) -> NoReturn:
    """Runs one of the programs in tests/libcsummaries

    A combination of a header file and a function name from that header may
    have a test program associated with it (see tests/testfiles.json).
    """

    # arguments
    cheader: str = args.header
    cfnname: str = args.function
    cshowcode: bool = args.showcode
    copen: bool = args.open
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        (projectpath, cfilename_c) = UF.get_libc_summary_test(cheader, cfnname)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    targetpath = projectpath
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    if not os.path.isdir(targetpath):
        print_error(f"Target directory: {targetpath} does not exist")
        exit(1)

    set_logging(
        loglevel,
        targetpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="cfile test-libc-summary invoked")

    parsemanager = ParseManager(projectpath, projectname, targetpath)
    parsemanager.remove_semantics()
    parsemanager.initialize_paths()

    try:
        cfilename_i = parsemanager.preprocess_file_with_gcc(cfilename_c)
        result = parsemanager.parse_ifile(cfilename_i)
        if result != 0:
            print("*" * 80)
            print("Error in parsing " + cfilename_c)
            if Config().platform == "macOS":
                print("  (Problem may be related to standard header files on macOS)")
            print("*" * 80)
            exit(1)
    except OSError as e:
        print_error("Error when parsing file: " + str(e))
        exit(1)

    chklogger.logger.info("cfile parse completed")

    cchpath = UF.get_cchpath(targetpath, projectname)

    contractpath = os.path.join(targetpath, "chc_contracts")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)

    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    am = AnalysisManager(capp, verbose=False, wordsize=32)

    am.create_file_primary_proofobligations(cfilename)
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    am.generate_and_check_file(cfilename, "llrvisp")
    am.reset_tables(cfile)
    capp.collect_post_assumes()

    for k in range(5):
        capp.update_spos()
        am.generate_and_check_file(cfilename, "llrvisp")
        am.reset_tables(cfile)

    chklogger.logger.info("cfile analyze completed")

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()

    if cshowcode:
        if copen:
            pofilter = lambda po: (not po.is_closed)
        else:
            pofilter = lambda po: True

        print(RP.file_code_tostring(cfile, pofilter=pofilter))

    print(RP.file_proofobligation_stats_tostring(cfile))

    # TODO: add investigation output

    exit(0)
