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
import shutil
import subprocess
import sys

from typing import List, Optional, NoReturn

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager
import chc.cmdline.jsonresultutil as JU

from chc.app.CApplication import CApplication

import chc.reporting.ProofObligations as RP

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


def cfile_parse_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        UF.check_parser()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    abscfilename = os.path.abspath(cfilename)
    cpath = os.path.dirname(abscfilename)
    cfilename = os.path.basename(abscfilename)
    if not os.path.isfile(abscfilename):
        print("C source code file %s not found", abscfilename)
        exit(1)

    if not abscfilename.endswith(".c"):
        print_error("C source code file should have extension .c")
        exit(1)

    set_logging(
        loglevel,
        cpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="cfile parse invoked")

    if opttgtpath is None:
        ctgtpath = cpath
    else:
        ctgtpath = os.path.abspath(opttgtpath)
    chklogger.logger.info("Target path: %s", ctgtpath)

    sempathname = cfilename + "ch"
    sempath = os.path.join(ctgtpath, sempathname)
    tarname = sempathname + ".tar.gz"
    abstarname = os.path.join(ctgtpath, tarname)

    chklogger.logger.info("Change directory to %s", ctgtpath)
    os.chdir(ctgtpath)
    if os.path.isdir(sempath):
        chklogger.logger.info("Removing semantics directory %s", sempath)
        shutil.rmtree(sempath)

    if os.path.isfile(abstarname):
        chklogger.logger.info("Removing tarfile %s", abstarname)
        os.remove(abstarname)

    parsemanager = ParseManager(cpath, ctgtpath, sempathname)
    parsemanager.initialize_paths()

    try:
        ifilename = parsemanager.preprocess_file_with_gcc(cfilename)
        result = parsemanager.parse_ifile(ifilename)
        if result != 0:
            print("*" * 80)
            print("Error in parsing " + cfilename)
            if Config().platform == "macOS":
                print("  (Problem may be related to standard header files on macOS)")
            print("*" * 80)
            exit(1)
    except OSError as e:
        print_error("Error when parsing file: " + str(e))
        exit(1)

    parsemanager.save_semantics()

    exit(0)


def cfile_analyze_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectpath = os.path.dirname(os.path.abspath(cfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    cfilename = os.path.basename(cfilename)
    projectname = cfilename[:-2]

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

    capp.initialize_single_file(cfilename[:-2])

    am = AnalysisManager(capp)

    am.create_file_primary_proofobligations(cfilename[:-2])
    am.reset_tables(cfilename[:-2])
    capp.collect_post_assumes()

    am.generate_and_check_file(cfilename[:-2], "llrvisp")
    am.reset_tables(cfilename[:-2])
    capp.collect_post_assumes()

    for k in range(5):
        capp.update_spos()
        am.generate_and_check_file(cfilename[:-2], "llrvisp")
        am.reset_tables(cfilename[:-2])

    chklogger.logger.info("cfile analyze completed")

    exit(0)


def cfile_report_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath
    cshowcode: bool = args.showcode
    copen: bool = args.open
    jsonoutput: bool = args.json
    outputfile: Optional[str] = args.output
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    projectpath = os.path.dirname(os.path.abspath(cfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    cfilename = os.path.basename(cfilename)
    projectname = cfilename[:-2]

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
    capp.initialize_single_file(cfilename[:-2])
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


    if cshowcode:
        if args.open:
            pofilter = lambda po: (not po.is_closed)
        else:
            pofilter = lambda po: True

        print(RP.file_code_tostring(cfile, pofilter=pofilter))

    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)
