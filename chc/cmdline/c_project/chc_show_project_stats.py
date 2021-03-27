# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017 Kestrel Technology LLC
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

import argparse
import os

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication
from chc.cmdline.AnalysisManager import AnalysisManager
from chc.linker.CLinker import CLinker


def parse():
    usage = (
        "\nCall with the directory that holds the semantics files\n\n"
        + "  Example: python chc_analyze_project ~/gitrepo/ktadvance/tests/sard/zitser/id1284"
    )
    description = (
        "Analyzes a c project for which the semantics files have already been "
        + "produced by the parser front end (use chc_parse_project.py to "
        + "produce the semantics file, if not yet available)."
    )
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument(
        "path", help="directory that holds the semantics directory (or tar.gz file)"
    )
    args = parser.parse_args()
    return args


def savexrefs(f):
    capp.indexmanager.savexrefs(capp.path, f.name, f.index)


if __name__ == "__main__":

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_semantics(cpath)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)
    sempath = os.path.join(cpath, "semantics")

    capp = CApplication(sempath)
    print("Global entities")
    print(str(capp.declarations.get_stats()))
    print("\nFile line and function counts\n")
    print(capp.get_line_counts())

    request = {
        "mem": lambda v: v.is_mem(),
        "tmp": lambda v: v.is_tmpvar(),
        "var": lambda v: v.is_var and not v.is_tmpvar(),
    }

    lhosts = {}

    def f(cfile):
        lhosts[cfile.name] = cfile.declarations.dictionary.get_distribution(
            "lhost", request
        )

    capp.iter_files(f)
    flen = capp.get_max_filename_length()

    print("\nDistribution of lvalue hosts")
    print("file".ljust(flen) + "mem".rjust(12) + "var".rjust(12) + "tmp".rjust(12))
    print("-" * (flen + 36))
    for name in sorted(lhosts):
        d = lhosts[name]
        print(
            name.ljust(flen)
            + str(d["mem"]).rjust(12)
            + str(d["var"]).rjust(12)
            + str(d["tmp"]).rjust(12)
        )
    print("-" * (flen + 36))
    memtotal = sum(lhosts[n]["mem"] for n in lhosts)
    vartotal = sum(lhosts[n]["var"] for n in lhosts)
    tmptotal = sum(lhosts[n]["tmp"] for n in lhosts)
    print(
        "total".ljust(flen)
        + str(memtotal).rjust(12)
        + str(vartotal).rjust(12)
        + str(tmptotal).rjust(12)
    )
