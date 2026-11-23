# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2026 Aarno Labs LLC
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
"""Command-line interface for systems of separately analyzed projects.

A system is a set of CodeHawk-C projects (modules) that call each other, such
as the cFS core (cFE), its libraries and its apps. Verification proceeds in two
passes: every module is analyzed cold, the boundary between the modules is
collected and drafted as external companions, the user reviews them, and every
module is verified again against the reviewed companions.
"""

import argparse
import os
import sys

from typing import Dict, List, NoReturn

from chc.app.CApplication import CApplication
from chc.reporting.SystemBoundary import SystemBoundary
import chc.util.fileutil as UF


def print_error(m: str) -> None:
    sys.stderr.write(("*" * 80) + "\n")
    sys.stderr.write("F:" + m + "\n")
    sys.stderr.write(("*" * 80) + "\n")


def csystem_collect_boundary(args: argparse.Namespace) -> NoReturn:
    """CLI command to collect the boundary of a system of projects analyzed
    cold, and to write draft external companions for review."""

    # arguments
    tgtpath: str = args.tgtpath
    projectnames: List[str] = args.projectnames
    analysislevel: str = args.analysis_level
    optoutput: str = args.output

    targetpath = os.path.abspath(tgtpath)
    if len(set(projectnames)) != len(projectnames):
        print_error("A project is listed more than once")
        exit(1)
    for p in projectnames:
        if not UF.has_analysisresults_path(targetpath, p):
            print_error(f"No analysis results found for {p} in {targetpath}")
            exit(1)

    outdir = (
        os.path.abspath(optoutput) if optoutput is not None
        else os.path.join(targetpath, "chc_boundary"))

    contractpath = os.path.join(targetpath, "chc_contracts")
    capps: Dict[str, CApplication] = {}
    for p in projectnames:
        print("Loading " + p + " ...", file=sys.stderr)
        capps[p] = CApplication(targetpath, p, targetpath, contractpath)

    boundary = SystemBoundary(targetpath, capps, level=analysislevel)
    written = boundary.write(outdir)
    print(boundary.summary())
    print("\nDraft companions, summary.txt and boundary.json written to "
          + outdir + " (" + str(len(written) - 2) + " draft companions)")
    exit(0)
