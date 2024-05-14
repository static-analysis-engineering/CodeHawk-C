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
"""Commands to display dictionary tables."""


import argparse
import json
import os
import sys

from typing import NoReturn, Optional, TYPE_CHECKING

from chc.app.CApplication import CApplication

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger, LogLevel

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction


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


def get_cfile_access(args: argparse.Namespace, cmd: str, table: str) -> "CFile":
    """Checks existence of and provides access to c-file analysis results."""

    # arguments
    xcfilename: str = args.filename
    opttgtpath: Optional[str] = args.tgtpath

    projectpath = os.path.dirname(os.path.abspath(xcfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    targetpath = os.path.abspath(targetpath)
    cfilename_c = os.path.basename(xcfilename)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    cchpath = UF.get_cchpath(targetpath, projectname)
    contractpath = os.path.join(targetpath, "chc_contracts")

    checkresults = UF.check_cfile_results(targetpath, projectname, "", cfilename)
    if checkresults is not None:
        print_error(checkresults)
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    return capp.get_cfile()


def get_cfun_access(
        args: argparse.Namespace, cmd: str, table: str) -> "CFunction":

    # arguments
    xcfilename: str = args.filename
    fnname: str = args.function
    opttgtpath: Optional[str] = args.tgtpath

    projectpath = os.path.dirname(os.path.abspath(xcfilename))
    targetpath = projectpath if opttgtpath is None else opttgtpath
    targetpath = os.path.abspath(targetpath)
    cfilename_c = os.path.basename(xcfilename)
    cfilename = cfilename_c[:-2]
    projectname = cfilename

    cchpath = UF.get_cchpath(targetpath, projectname)
    contractpath = os.path.join(targetpath, "chc_contracts")

    checkresults = UF.check_cfun_results(
        targetpath, projectname, "", cfilename, fnname)
    if checkresults is not None:
        print_error(checkresults)
        exit(1)

    capp = CApplication(
        projectpath, projectname, targetpath, contractpath, singlefile=True)
    capp.initialize_single_file(cfilename)
    cfile = capp.get_cfile()
    if cfile.has_function_by_name(fnname):
        return cfile.get_function_by_name(fnname)
    else:
        print_error(f"Function {fnname} not found in {cfilename_c}")
        exit(1)


def cfile_attrparam_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed attribute parameters in a c-file."""

    cfile = get_cfile_access(args, "file table", "attrparam")
    print(cfile.dictionary.objectmap_to_string("attrparam"))

    exit(0)


def cfile_attribute_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed attributes of variables and types in a c-file."""

    cfile = get_cfile_access(args, "file table", "attribute")
    print(cfile.dictionary.objectmap_to_string("attribute"))

    exit(0)

# Tables from CDictionary

def cfile_attributes_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed attribute lists in a c-file."""

    cfile = get_cfile_access(args, "file table", "attributes")
    print(cfile.dictionary.objectmap_to_string("attributes"))

    exit(0)


def cfile_constant_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed constants in a c-file."""

    cfile = get_cfile_access(args, "file table", "constant")
    print(cfile.dictionary.objectmap_to_string("constant"))

    exit(0)


def cfile_exp_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed C expressions in a c-file."""

    cfile = get_cfile_access(args, "file table", "exp")
    print(cfile.dictionary.objectmap_to_string("exp"))

    exit(0)


def cfile_funarg_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed function arguments in a c-file."""

    cfile = get_cfile_access(args, "file table", "funarg")
    print(cfile.dictionary.objectmap_to_string("funarg"))

    exit(0)


def cfile_funargs_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed lists of function arguments in a c-file."""

    cfile = get_cfile_access(args, "file table", "funargs")
    print(cfile.dictionary.objectmap_to_string("funargs"))

    exit(0)


def cfile_lhost_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed lhs base variable locations in a c-file."""

    cfile = get_cfile_access(args, "file-table", "lhost")
    print(cfile.dictionary.objectmap_to_string("lhost"))

    exit(0)


def cfile_lval_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed left-hand side values in a c-file."""

    cfile = get_cfile_access(args, "file-table", "lval")
    print(cfile.dictionary.objectmap_to_string("lval"))

    exit(0)


def cfile_offset_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed variable offsets in a c-file."""

    cfile = get_cfile_access(args, "file-table", "offset")
    print(cfile.dictionary.objectmap_to_string("offset"))

    exit(0)


def cfile_typ_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed variable types in a c-file."""

    cfile = get_cfile_access(args, "file-table", "typ")
    print(cfile.dictionary.objectmap_to_string("typ"))

    exit(0)


def cfile_typsig_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed attribute type signatures in a c-file."""

    cfile = get_cfile_access(args, "file-table", "typsig")
    print(cfile.dictionary.objectmap_to_string("typsig"))

    exit(0)


def cfile_typsiglist_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed lists of attribute type signatures in a c-file."""

    cfile = get_cfile_access(args, "file-table", "typsiglist")
    print(cfile.dictionary.objectmap_to_string("typsiglist"))

    exit(0)


# Tables from CFileDeclarations ------------------------------------------------

def cfile_compinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of global compinfo (struct/union) declarations/definitions."""

    cfile = get_cfile_access(args, "file-table", "compinfo")
    print(cfile.declarations.objectmap_to_string("compinfo"))

    exit(0)


def cfile_enuminfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of global enuminfo declarations/definitions."""

    cfile = get_cfile_access(args, "file-table", "enuminfo")
    print(cfile.declarations.objectmap_to_string("enuminfo"))

    exit(0)


def cfile_enumitem_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of global enumitem declarations/definitions."""

    cfile = get_cfile_access(args, "file-table", "enumitem")
    print(cfile.declarations.objectmap_to_string("enumitem"))

    exit(0)


def cfile_fieldinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of global fieldinfo declarations/definitions."""

    cfile = get_cfile_access(args, "file-table", "fieldinfo")
    print(cfile.declarations.objectmap_to_string("fieldinfo"))

    exit(0)


def cfile_initinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of global initinfo declarations/definitions."""

    cfile = get_cfile_access(args, "file-table", "initinfo")
    print(cfile.declarations.objectmap_to_string("initinfo"))

    exit(0)


def cfile_location_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed locations in a c-file."""

    cfile = get_cfile_access(args, "file-table", "location")
    print(cfile.declarations.objectmap_to_string("location"))

    exit(0)


def cfile_offsetinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed offsetinfos in a c-file."""

    cfile = get_cfile_access(args, "file-table", "offsetinfo")
    print(cfile.declarations.objectmap_to_string("offsetinfo"))

    exit(0)


def cfile_typeinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed typeinfos in a c-file."""

    cfile = get_cfile_access(args, "file-table", "typeinfo")
    print(cfile.declarations.objectmap_to_string("typeinfo"))

    exit(0)


def cfile_varinfo_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed varinfos in a c-file."""

    cfile = get_cfile_access(args, "file-table", "varinfo")
    print(cfile.declarations.objectmap_to_string("varinfo"))

    exit(0)


# From CContextDictionary ------------------------------------------------------

def cfile_pcontext_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed program contexts in a c-file."""

    cfile = get_cfile_access(args, "file-table", "program-context")
    print(cfile.contextdictionary.objectmap_to_string("p"))

    exit(0)


def cfile_expcontext_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed expression contexts in a c-file."""

    cfile = get_cfile_access(args, "file-table", "exp-context")
    print(cfile.contextdictionary.objectmap_to_string("exp"))

    exit(0)


def cfile_cfgcontext_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed cfg contexts in a c-file."""

    cfile = get_cfile_access(args, "file-table", "cfg-context")
    print(cfile.contextdictionary.objectmap_to_string("cfg"))

    exit(0)


# Tables from InterfaceDictionary ----------------------------------------------

def cfile_apiparam_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed api parameters in a c-file."""

    cfile = get_cfile_access(args, "file-table", "api-param")
    print(cfile.interfacedictionary.objectmap_to_string("apiparam"))

    exit(0)


def cfile_postassume_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed assumptions on post conditions in a c-file."""

    cfile = get_cfile_access(args, "file-table", "post-assume")
    print(cfile.interfacedictionary.objectmap_to_string("postassume"))

    exit(0)


def cfile_postrequest_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed requests for a post conditions in a c-file."""

    cfile = get_cfile_access(args, "file-table", "post-request")
    print(cfile.interfacedictionary.objectmap_to_string("postrequest"))

    exit(0)


def cfile_sterm_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed terms in external expressions in a c-file."""

    cfile = get_cfile_access(args, "file-table", "s-term")
    print(cfile.interfacedictionary.objectmap_to_string("sterm"))

    exit(0)


def cfile_soffset_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed offsets in external expressions in a c-file."""

    cfile = get_cfile_access(args, "file-table", "s-offset")
    print(cfile.interfacedictionary.objectmap_to_string("soffset"))

    exit(0)


def cfile_xpred_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed external predicates in a c-file."""

    cfile = get_cfile_access(args, "file-table", "xpredicate")
    print(cfile.interfacedictionary.objectmap_to_string("xpred"))

    exit(0)


# Tables in CFilePredicateDictionary -------------------------------------------

def cfile_predicate_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed proof-obligation predicates in a c-file."""

    cfile = get_cfile_access(args, "file-table", "predicate")
    print(cfile.predicatedictionary.objectmap_to_string("predicate"))

    exit(0)


# Function tables in CFunXprDictionary

def cfile_numerical_table(args: argparse.Namespace) -> NoReturn:
    """Shows a list of indexed numerical terms in a function."""

    cfun = get_cfun_access(args, "function-table", "numerical")
    print(cfun.vardictionary.xd.objectmap_to_string("numerical"))

    exit(0)
