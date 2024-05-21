# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs LLC
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
"""Main access point to the analysis of a C application.

"""

from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING)
import os
import multiprocessing
import sys

from chc.api.CGlobalContract import CGlobalContract

from chc.app.CCompInfo import CCompInfo
from chc.app.CFile import CFile
from chc.app.CVarInfo import CVarInfo
from chc.app.IndexManager import IndexManager, FileVarReference, FileKeyReference
from chc.app.CGlobalDeclarations import CGlobalDeclarations
from chc.app.CGlobalDictionary import CGlobalDictionary

from chc.source.CSrcFile import CSrcFile

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger


if TYPE_CHECKING:
    from chc.app.CFunction import CFunction
    from chc.app.CInstr import CCallInstr
    from chc.proof.CFunctionCallsiteSPOs import CFunctionCallsiteSPOs
    from chc.proof.CFunctionPO import CFunctionPO


class CApplication(object):
    """Primary access point for source code and analysis results.

    An application can consist of a single file, or of multiple files managed
    by a Makefile.

    In case of a single file the following call on CApplication initializes
    the single file:

    - capp.initialize_single_file(cfilename)

    The filepath in this case is assumed to be empty. The file index is set
    to 0.

    In case of multiple files the following file is assumed to be present in
    the top analysis-results directory:

    - <projectpath>/<projectname>.cch/a/target_files.xml

    This file, normally created by the CodeHawk-C parser, is expected to
    contain a list of c-file entries that provide the attributes:

    - id: a unique file index, a number greater than zero;
    - name: a string denoting the relative path of the file w.r.t. the project
      directory (e.g., src/cgi/buffer.c)

    """

    def __init__(
            self,
            projectpath: str,
            projectname: str,
            targetpath: str,
            contractpath: str,
            singlefile: bool = False,
            excludefiles: List[str] = []) -> None:
        self._projectpath = projectpath
        self._projectname = projectname
        self._targetpath = targetpath
        self._contractpath = contractpath
        self._singlefile = singlefile
        self._excludefiles = excludefiles
        self._indexmanager = IndexManager(singlefile)
        self._globalcontract: Optional[CGlobalContract] = None
        self._dictionary: Optional[CGlobalDictionary] = None
        self._declarations: Optional[CGlobalDeclarations] = None
        self._files: Optional[Dict[int, CFile]] = None  # file-index -> CFile
        self._callgraph: Optional[
            Dict[Tuple[int, int],
                 List[Tuple[Tuple[int, int], "CFunctionCallsiteSPOs"]]]] = None
        self._revcallgraph: Optional[
            Dict[Tuple[int, int],
                 List[Tuple[Tuple[int, int], "CFunctionCallsiteSPOs"]]]] = None

    @property
    def projectpath(self) -> str:
        return self._projectpath

    @property
    def projectname(self) -> str:
        return self._projectname

    @property
    def targetpath(self) -> str:
        return self._targetpath

    @property
    def contractpath(self) -> str:
        return self._contractpath

    @property
    def globalcontract(self) -> CGlobalContract:
        if self._globalcontract is None:
            self._globalcontract = CGlobalContract(self)
        return self._globalcontract

    @property
    def is_singlefile(self) -> bool:
        return self._singlefile

    @property
    def excludefiles(self) -> List[str]:
        return self._excludefiles

    @property
    def files(self) -> Dict[int, CFile]:
        """Returns a map from file-indexes to CFile objects."""

        if self._files is None:
            self._files = {}
            if self.is_singlefile:
                chklogger.logger.error(
                    "Single-file application should be initialized via "
                    + " the call initialize_single_file(cfilename)")
                raise UF.CHCError("Single file not yet initialized")
            else:
                self._initialize_from_target_files()
        return self._files

    @property
    def cfiles(self) -> Iterable[CFile]:
        return self.files.values()

    @property
    def filenames(self) -> List[str]:
        """Returns full filenames relative to the project path (without .c)."""

        return [cfile.name for cfile in self.files.values()]

    def is_application_header(self, name: str) -> bool:
        """Returns true if the name corresponds to an application file."""

        for n in self.filenames:
            if name == os.path.basename(n):
                return True
        else:
            return False

    @property
    def filexref(self) -> Dict[str, int]:
        """Returns a map from c filenames to file-indexes.

        Note: filenames include extension and paths relative to project
        directory.
        """
        return {cfile.name: index for (index, cfile) in self.files.items()}

    @property
    def indexmanager(self) -> IndexManager:
        return self._indexmanager

    @property
    def dictionary(self) -> CGlobalDictionary:
        if self._dictionary is None:
            xnode = UF.get_global_dictionary_xnode(
                self.targetpath, self.projectname)
            self._dictionary = CGlobalDictionary(self, xnode)
        return self._dictionary

    @property
    def declarations(self) -> CGlobalDeclarations:
        if self._declarations is None:
            xnode = UF.get_global_declarations_xnode(
                self.targetpath, self.projectname)
            self._declarations = CGlobalDeclarations(self, xnode)
        return self._declarations

    def get_max_filename_length(self) -> int:
        return max([len(x) for x in self.filenames])

    def get_cfile(self) -> CFile:
        """Returns the CFile object in a single-file project."""

        if self.is_singlefile:
            if 0 in self.files:
                return self.files[0]
            else:
                raise UF.CHCError("Single file has not been initialized")
        else:
            raise UF.CHCError(
                "This application is not a single-file application")

    def get_file(self, fname: str) -> CFile:
        """Access to file with full relative path and no extension."""

        if fname in self.filexref:
            return self.files[self.filexref[fname]]
        else:
            chklogger.logger.error("File not found: %s", fname)
            raise UF.CHCError(f"File with name {fname} not found")

    def has_file(self, fname: str) -> bool:
        return fname in self.filexref

    def get_file_by_index(self, index: int) -> CFile:
        if index in self.files:
            return self.files[index]
        else:
            raise UF.CHCError(f"File with index {index} not found")

    def has_file_index(self, index: int) -> bool:
        return index in self.files

    def get_function(self, filevar: FileVarReference) -> "CFunction":
        if self.has_file_index(filevar.fid):
            cfile = self.get_file_by_index(filevar.fid)
            if cfile.has_function_by_index(filevar.vid):
                return cfile.get_function_by_index(filevar.vid)
            else:
                raise UF.CHCError(
                    f"Function with index {filevar.vid} not found in file {cfile.name}")
        else:
            raise UF.CHCError(f"File with index {filevar.fid} not found")

    def has_function(self, filevar: FileVarReference) -> bool:
        if self.has_file_index(filevar.fid):
            cfile = self.get_file_by_index(filevar.fid)
            return cfile.has_function_by_index(filevar.vid)
        else:
            return False

    def get_callsites(
            self,
            fid: int,
            vid: int) -> List[Tuple[Tuple[int, int], "CFunctionCallsiteSPOs"]]:
        """Return a list of ((fid, vid), callsitespos)."""

        if (fid, vid) in self.revcallgraph:
            return self.revcallgraph[(fid, vid)]
        return []

    def iter_files(self, f: Callable[[CFile], None]) -> None:
        chklogger.logger.info(
            "Iter files over %d cfiles", len(list(self.cfiles)))
        for file in list(self.cfiles):
            f(file)

    def iter_files_parallel(
            self, f: Callable[[CFile], None], processes: int) -> None:
        for cfile in self.cfiles:
            while len(multiprocessing.active_children()) >= processes:
                pass

            p = multiprocessing.Process(target=f, args=(cfile,))
            p.start()

        while len(multiprocessing.active_children()) > 0:
            pass

    def iter_functions(self, f: Callable[["CFunction"], None]) -> None:
        def g(fi: CFile) -> None:
            fi.iter_functions(f)

        self.iter_files(g)

    def iter_functions_parallel(
            self, f: Callable[["CFunction"], None], maxprocesses: int) -> None:
        def g(fi: CFile) -> None:
            fi.iter_functions(f)

        self.iter_files_parallel(g, maxprocesses)

    def resolve_vid_function(
            self, filevar: FileVarReference) -> Optional["CFunction"]:
        """Returns the function def for the local file-index fid and vid.

        Note: the function definition may or may not reside in the same file,
        that is, the c-file with index fid may have a function declaration
        for the function with index vid, but not a a definition.

        The location of the definition is obtained from the index manager via
        the corresponding global index of the (local) vid (as initialized by
        the linker).
        """
        defvar = self.indexmanager.resolve_vid(filevar)
        if defvar is not None:
            if defvar.fid in self.files:
                deffile = self.files[defvar.fid]
                if deffile.has_function_by_index(defvar.vid):
                    return deffile.get_function_by_index(defvar.vid)
                else:
                    chklogger.logger.warning(
                        ("Function definition %d not found in file %d for "
                         + "(fid:%d, vid:%d)"),
                        defvar.vid,
                        defvar.fid,
                        filevar.fid,
                        filevar.vid)
                    return None
            else:
                chklogger.logger.warning(
                    "File with index %d not found for (fid: %d, vid: %d)",
                    defvar.fid, filevar.fid, filevar.vid)
                return None
        else:
            chklogger.logger.warning(
                "No function definition found for (fid: %d, vid: %d)",
                filevar.fid, filevar.vid)
            return None

    def convert_vid(self, filevar: FileVarReference, tgtfid: int) -> int:
        cvid = self.indexmanager.convert_vid(filevar, tgtfid)
        if cvid is None:
            raise UF.CHCError("Error in convert_vid: " + str(filevar.vid))
        return cvid

    def get_gckey(self, filekey: FileKeyReference) -> Optional[int]:
        return self.indexmanager.get_gckey(filekey)

    def get_function_by_index(self, index: int) -> "CFunction":
        for f in self.files:
            if self.files[f].has_function_by_index(index):
                return self.files[f].get_function_by_index(index)
        else:
            raise UF.CHCError(f"Function with index {index} not found")

    def get_callinstrs(self) -> List["CCallInstr"]:
        result: List["CCallInstr"] = []

        def f(fi: CFile) -> None:
            result.extend(fi.get_callinstrs())

        self.iter_files(f)
        return result

    # ------------------- Application statistics -----------------------------
    def get_line_counts(self) -> str:
        counts: Dict[str, Tuple[int, int, int]] = {}

        def f(cfile: CFile) -> None:
            counts[cfile.name] = (
                cfile.declarations.get_max_line(),
                cfile.declarations.get_code_line_count(),
                cfile.functioncount,
            )

        self.iter_files(f)

        flen = self.get_max_filename_length()
        lines: List[str] = []
        lines.append(
            "file".ljust(flen)
            + "LOC".rjust(12)
            + "CLOC".rjust(12)
            + "functions".rjust(12)
        )
        lines.append("-" * (flen + 36))
        for (c, (ml, mc, fc)) in sorted(counts.items()):
            lines.append(
                c.ljust(flen)
                + str(ml).rjust(12)
                + str(mc).rjust(12)
                + str(fc).rjust(12)
            )
        lines.append("-" * (flen + 36))
        mltotal = sum(x[0] for x in counts.values())
        mctotal = sum(x[1] for x in counts.values())
        fctotal = sum(x[2] for x in counts.values())
        lines.append(
            "total".ljust(flen)
            + str(mltotal).rjust(12)
            + str(mctotal).rjust(12)
            + str(fctotal).rjust(12)
        )
        return "\n".join(lines)

    def get_project_counts(
            self,
            filefilter: Callable[[str], bool] = lambda f: True
    ) -> Tuple[int, int, int]:
        linecounts: List[int] = []
        clinecounts: List[int] = []
        cfuncounts: List[int] = []

        def f(cfile: CFile) -> None:
            if filefilter(cfile.name):
                decls = cfile.declarations
                linecounts.append(decls.get_max_line())
                clinecounts.append(decls.get_code_line_count())
                cfuncounts.append(cfile.functioncount)

        self.iter_files(f)
        return (sum(linecounts), sum(clinecounts), sum(cfuncounts))

    def update_spos(self) -> None:
        """Create supporting proof obligations for all call sites."""

        def f(fn: "CFunction") -> None:
            fn.update_spos()
            fn.save_spos()
            fn.save_pod()

        def h(cfile: CFile) -> None:
            cfile.iter_functions(f)
            cfile.save_predicate_dictionary()
            cfile.save_interface_dictionary()
            cfile.save_declarations()

        self.iter_files(h)

    def collect_post_assumes(self) -> None:
        """Collect postconditions from callee's contracts and add as assume."""

        for fi in self.cfiles:
            fi.collect_post_assumes()

    def distribute_post_guarantees(self) -> None:
        """add callee postcondition guarantees to call sites as assumptions"""

        if self.contractpath is None:
            return  # no contracts provided

        def f(fn: "CFunction") -> None:
            fn.distribute_post_guarantees()
            fn.save_spos()
            fn.save_pod()

        def h(cfile: CFile) -> None:
            cfile.iter_functions(f)
            cfile.save_predicate_dictionary()
            cfile.save_interface_dictionary()
            cfile.save_declarations()

        self.iter_files(h)

    def reinitialize_tables(self) -> None:

        def f(fi: CFile) -> None:
            fi.reinitialize_tables()

        self.iter_files(f)

    def reload_ppos(self) -> None:
        """Reload primary proof obligations after analyzer has run."""

        def f(fn: "CFunction") -> None:
            fn.reload_ppos()

        self.iter_functions(f)

    def reload_spos(self) -> None:
        """Reload supporting proof obligations after analyzer has run."""

        def f(fn: "CFunction") -> None:
            fn.reload_spos()

        self.iter_functions(f)

    def get_contract_condition_violations(
            self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        result: List[Tuple[str, List[Tuple[str, str]]]] = []

        def f(fn: "CFunction") -> None:
            if fn.violates_contract_conditions():
                result.append((fn.name, fn.get_contract_condition_violations()))

        self.iter_functions(f)
        return result

    def get_ppos(self) -> List["CFunctionPO"]:
        result: List["CFunctionPO"] = []

        def f(fn: "CFunction") -> None:
            result.extend(fn.get_ppos())

        self.iter_functions(f)
        return result

    def get_spos(self) -> List["CFunctionPO"]:
        result: List["CFunctionPO"] = []

        def f(fn: "CFunction") -> None:
            result.extend(fn.get_spos())

        self.iter_functions(f)
        return result

    def get_open_ppos(self) -> List["CFunctionPO"]:
        result: List["CFunctionPO"] = []

        def f(fn: "CFunction") -> None:
            result.extend(fn.get_open_ppos())

        self.iter_functions(f)
        return result

    def get_ppos_violated(self) -> List["CFunctionPO"]:
        result: List["CFunctionPO"] = []

        def f(fn: "CFunction") -> None:
            result.extend(fn.get_ppos_violated())

        self.iter_functions(f)
        return result

    def get_ppos_delegated(self) -> List["CFunctionPO"]:
        result: List["CFunctionPO"] = []

        def f(fn: "CFunction") -> None:
            result.extend(fn.get_ppos_delegated())

        self.iter_functions(f)
        return result

    def initialize_files(self, filenames: Dict[int, str]) -> None:
        self._files = {}
        for (index, fname) in filenames.items():
            self._files[index] = self._initialize_file(index, fname)

    def _initialize_from_target_files(self) -> None:
        chklogger.logger.info("Initialize from target files")
        tgtxnode = UF.get_targetfiles_xnode(self.targetpath, self.projectname)
        if tgtxnode is None:
            raise UF.CHCXmlParseError(self.targetpath, 0, (0, 0))

        self._files = {}

        for c in tgtxnode.findall("c-file"):
            cfilename_c = c.get("name")
            if cfilename_c is None:
                raise UF.CHCXmlParseError(self.targetpath, 0, (0, 0))
            if cfilename_c in self.excludefiles:
                continue
            id = c.get("id")
            if id is None:
                chklogger.logger.error(
                    "No id found for target file %s", cfilename_c)
            else:
                fid = int(id)
                self._files[fid] = self._initialize_file(fid, cfilename_c)

    def initialize_single_file(self, fname: str) -> None:
        xcfile = UF.get_cfile_xnode(
            self.targetpath, self.projectname, None, fname)
        if xcfile is not None:
            cfile = CFile(self, 0, fname, None)
            self._files = {}
            self._files[0] = cfile
            self.indexmanager.add_file(cfile)
            chklogger.logger.info("Single c file was initialized %s", fname)
        else:
            chklogger.logger.error("c_file could not be extracted %s", fname)

    def _initialize_file(self, index: int, fname: str) -> CFile:
        xcfilepath = os.path.dirname(fname)
        cfilename = os.path.basename(fname)
        if xcfilepath == "":
            cfilepath: Optional[str] = None
        else:
            cfilepath = xcfilepath
        chklogger.logger.info(
            "Initialize file name: %s, file path: %s", cfilename, str(cfilepath))
        cfile = CFile(self, index, cfilename[:-2], cfilepath)
        self.indexmanager.add_file(cfile)
        chklogger.logger.info("initialized cfile %s", fname)
        return cfile

    @property
    def callgraph(self) -> Dict[
            Tuple[int, int],
            List[Tuple[Tuple[int, int], "CFunctionCallsiteSPOs"]]]:
        if self._callgraph is None:
            self._callgraph = {}
            for (fid, cfile) in self.files.items():
                for (vid, cfun) in cfile.functions.items():
                    for cs in cfun.proofs.spos.callsite_spos.values():
                        if cs.has_callee() and cs.callee is not None:
                            fncallee = FileVarReference(fid, cs.callee.vid)
                            fundef = self.indexmanager.resolve_vid(fncallee)
                            if fundef is not None:
                                self._callgraph.setdefault((fid, vid), [])
                                self._callgraph[(fid, vid)].append(
                                    (fundef.tuple, cs))
        return self._callgraph

    @property
    def revcallgraph(self) -> Dict[
            Tuple[int, int],
            List[Tuple[Tuple[int, int], "CFunctionCallsiteSPOs"]]]:
        if self._revcallgraph is None:
            self._revcallgraph = {}
            for s in self.callgraph:
                for (t, cs) in self.callgraph[s]:
                    self._revcallgraph.setdefault(t, [])
                    self._revcallgraph[t].append((s, cs))
        return self._revcallgraph
