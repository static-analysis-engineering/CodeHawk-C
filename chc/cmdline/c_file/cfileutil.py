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
import os
import shutil
import sys

from typing import List, Optional, NoReturn

from chc.cmdline.AnalysisManager import AnalysisManager
from chc.cmdline.ParseManager import ParseManager

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
    filename: str = args.filename
    savesemantics: bool = args.save_semantics

    try:
        UF.check_parser()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    cfilename = os.path.abspath(args.filename)
    if not os.path.isfile(cfilename):
        print("*" * 80)
        print("C source code file " + cfilename + " not found")
        print("*" * 80)
        exit(1)

    if not cfilename.endswith(".c"):
        print("*" * 80)
        print("C source code file should have extension .c")
        print("*" * 80)
        exit(1)

    cpath = os.path.dirname(cfilename)
    targetpath = cpath

    os.chdir(targetpath)
    if os.path.isdir("semantics"):
        print("Removing semantics directory")
        shutil.rmtree("semantics")

    if os.path.isfile("semantics_linux.tar.gz"):
        print("Removing semantics_linux.tar.gz")
        os.remove("semantics_linux.tar.gz")

    parsemanager = ParseManager(cpath, targetpath)
    parsemanager.initialize_paths()

    try:
        basename = os.path.basename(cfilename)
        ifilename = parsemanager.preprocess_file_with_gcc(basename)
        result = parsemanager.parse_ifile(ifilename)
        if result != 0:
            print("*" * 80)
            print("Error in parsing " + cfilename)
            if Config().platform == "macOS":
                print("  (Problem may be related to standard header files on macOS)")
            print("*" * 80)
            exit(1)
    except OSError as e:
        print("Error when parsing file: " + str(e))
        exit(1)

    parsemanager.save_semantics()

    exit(0)


def cfile_analyze_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cpath = args.path
    cfilename = args.filename
    loglevel: str = args.loglevel
    logfilename: Optional[str] = args.logfilename
    logfilemode: str = args.logfilemode

    try:
        cpath = UF.get_project_path(cpath)
        UF.check_cfile(cpath, cfilename)
        UF.check_semantics(cpath)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    set_logging(
        loglevel,
        cpath,
        logfilename=logfilename,
        mode=logfilemode,
        msg="cfile analyze invoked")

    sempath = os.path.join(cpath, "semantics")
    contractpath = os.path.join(cpath, "chc_contracts")

    capp = CApplication(sempath, cfilename, contractpath=contractpath)
    chcpath = capp.path

    try:
        xfilename = UF.get_cfile_filename(chcpath, cfilename)
        UF.check_cfile(chcpath, xfilename)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    am = AnalysisManager(capp)

    am.create_file_primary_proofobligations(cfilename)
    am.reset_tables(cfilename)
    capp.collect_post_assumes()

    am.generate_and_check_file(cfilename, "llrvisp")
    am.reset_tables(cfilename)
    capp.collect_post_assumes()

    for k in range(5):
        capp.update_spos()
        am.generate_and_check_file(cfilename, "llrvisp")
        am.reset_tables(cfilename)

    chklogger.logger.info("cfile analyze completed")

    exit(0)


def cfile_report_file(args: argparse.Namespace) -> NoReturn:

    # arguments
    cpath = args.path
    cfile = args.filename
    cshowcode: bool = args.showcode
    copen: bool = args.open

    cpath = os.path.abspath(cpath)

    try:
        UF.check_semantics(cpath)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(args.path, "semantics")

    cfapp = CApplication(sempath, cfile)
    cfile = cfapp.get_cfile()

    if cshowcode:
        if args.open:
            pofilter = lambda po: (not po.is_closed)
        else:
            pofilter = lambda po: True

        print(RP.file_code_tostring(cfile, pofilter=pofilter))

    print(RP.file_proofobligation_stats_tostring(cfile))

    exit(0)
