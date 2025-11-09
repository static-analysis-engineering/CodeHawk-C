# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
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

import multiprocessing

import subprocess
import os
import shutil

from typing import List, Optional, Tuple, TYPE_CHECKING

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger


if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile


class AnalysisManager:
    """Provide the interface to the codehawk (ocaml) analyzer."""

    def __init__(
            self,
            capp: "CApplication",
            wordsize: int = 0,
            unreachability: bool = False,
            thirdpartysummaries: List[str] = [],
            keep_system_includes: bool = False,
            verbose: bool = False,
            collectdiagnostics: bool = False
    ) -> None:
        """Initialize the analyzer location and target file location.

        Args:
            capp (CApplication): application entry point

        Keyword args:
            wordsize (int): architecture wordsize (0,16,32,64) (default 0 (unspecified))
            unreachability (bool): use unreachability as justification to discharge
                                   (default False)
            thirdpartysummaries (string list): names of function summary jars
            verbose (bool): display analyzer output (default True)
            nofilter (bool): don't remove functions with absolute filename (default True)
        """

        self._capp = capp
        self._config = Config()
        self._keep_system_includes = keep_system_includes
        self.wordsize = wordsize
        self.thirdpartysummaries = thirdpartysummaries
        self.unreachability = unreachability
        self.verbose = verbose
        self._collectdiagnostics = collectdiagnostics

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def keep_system_includes(self) -> bool:
        return self._keep_system_includes

    @property
    def collect_diagnostics(self) -> bool:
        return self._collectdiagnostics

    @property
    def contractpath(self) -> Optional[str]:
        return self.capp.contractpath

    @property
    def config(self) -> Config:
        return self._config

    @property
    def chsummaries(self) -> str:
        return self.config.summaries

    @property
    def canalyzer(self) -> str:
        return self.config.canalyzer

    @property
    def projectpath(self) -> str:
        return self.capp.projectpath

    @property
    def targetpath(self) -> str:
        return self.capp.targetpath

    @property
    def projectname(self) -> str:
        return self.capp.projectname

    def reset(self) -> None:
        """Remove all file- and function-level files produced by the analysis."""

        def remove(f: str) -> None:
            if os.path.isfile(f):
                os.remove(f)

        for fi in self.capp.cfiles:
            for fn in fi.get_functions():
                fnargs: Tuple[str, str, Optional[str], str, str] = (
                    fn.targetpath, fn.projectname, fn.cfilepath, fn.cfilename, fn.name)
                remove(UF.get_api_filename(*fnargs))
                remove(UF.get_ppo_filename(*fnargs))
                remove(UF.get_spo_filename(*fnargs))
                remove(UF.get_pod_filename(*fnargs))
                remove(UF.get_invs_filename(*fnargs))
                remove(UF.get_vars_filename(*fnargs))
            fiargs: Tuple[str, str, Optional[str], str] = (
                fi.targetpath, fi.projectname, fi.cfilepath, fi.cfilename)
            remove(UF.get_cfile_contexttablename(*fiargs))
            remove(UF.get_cfile_predicate_dictionaryname(*fiargs))
            remove(UF.get_cfile_interface_dictionaryname(*fiargs))
            remove(UF.get_cfile_assignment_dictionaryname(*fiargs))
            remove(UF.get_cxreffile_filename(*fiargs))

        remove(UF.get_global_definitions_filename(
            self.capp.targetpath, self.capp.projectname))

    def reset_logfiles(self) -> None:
        """Remove all log files from semantics directory."""

        def remove(f: str) -> None:
            if os.path.isfile(f):
                os.remove(f)

        for fi in self.capp.cfiles:
            fiargs: Tuple[str, str, Optional[str], str] = (
                fi.targetpath, fi.projectname, fi.cfilepath, fi.cfilename)
            for kind in [
                    "gencheck.chlog", "gencheck.infolog", "gencheck.errorlog",
                    "primary.chlog", "primary.infolog", "primary.errorlog"]:
                fkargs = fiargs + (kind, )
                remove(UF.get_cfile_logfile_name(*fkargs))

    def reset_tables(self, cfile: "CFile") -> None:
        """Reload dictionaries from file (to get updated data from analyzer)."""

        cfilename = cfile.name
        chklogger.logger.debug("Reset tables for %s", cfilename)
        cfile.reinitialize_tables()
        cfile.reload_ppos()
        cfile.reload_spos()

    def _execute_cmd(self, CMD: List[str]) -> None:
        try:
            print(CMD)
            result = subprocess.check_output(CMD)
            print(result.decode("utf-8"))
        except subprocess.CalledProcessError as args:
            print(str(args.output))
            print(args)
            exit(1)

    def _create_file_primary_proofobligations_cmd_partial(
            self, po_cmd="undefined-behavior-primary"
    ) -> List[str]:
        cmd: List[str] = [
            self.canalyzer, "-summaries", self.chsummaries, "-command", po_cmd]
        if not (self.thirdpartysummaries is None):
            for s in self.thirdpartysummaries:
                cmd.extend(["-summaries", s])
        if not (self.contractpath is None):
            cmd.extend(["-contractpath", self.contractpath])
        cmd.extend(["-projectname", self.capp.projectname])

        if self.keep_system_includes:
            cmd.append("-keep_system_includes")
        if self.wordsize > 0:
            cmd.extend(["-wordsize", str(self.wordsize)])
        if self.collect_diagnostics:
            cmd.append("-diagnostics")
        cmd.append(self.targetpath)
        cmd.append("-cfilename")
        return cmd

    def create_file_primary_proofobligations(
            self,
            cfilename: str,
            cfilepath: Optional[str] = None,
            po_cmd: str = "undefined-behavior-primary"
    ) -> None:
        """Call analyzer to create primary proof obligations for a single file."""

        chklogger.logger.info(
            "Create primiary proof obligations for file %s with path %s",
            cfilename, ("none" if cfilepath is None else cfilepath))
        try:
            cmd = self._create_file_primary_proofobligations_cmd_partial(
                po_cmd=po_cmd)
            cmd.append(cfilename)
            if cfilepath is not None:
                cmd.extend(["-cfilepath", cfilepath])
            chklogger.logger.info(
                "Ocaml analyzer is called with %s", str(cmd))
            if self.verbose:
                print(str(cmd))
                result = subprocess.call(
                    cmd, cwd=self.targetpath, stderr=subprocess.STDOUT)
                print("\nResult: " + str(result))
            else:
                result = subprocess.call(
                    cmd,
                    cwd=self.targetpath,
                    stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )
            if result != 0:
                print("Error in creating primary proof obligations")
                exit(1)
            pcfilename = (
                cfilename if cfilepath is None
                else os.path.join(cfilepath, cfilename))
            cfile = self.capp.get_file(pcfilename)
            cfile.reinitialize_tables()
            cfile.reload_ppos()
            cfile.reload_spos()
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def create_app_primary_proofobligations(
            self,
            po_cmd: str = "undefined-behavior-primary",
            processes: int = 1) -> None:
        """Call analyzer to create ppo's for all application files."""

        if processes > 1:

            def f(cfile: "CFile") -> None:
                cmd = self._create_file_primary_proofobligations_cmd_partial(
                    po_cmd=po_cmd)
                cmd.append(cfile.cfilename)
                if cfile.cfilepath is not None:
                    cmd.extend(["-cfilepath", cfile.cfilepath])
                self._execute_cmd(cmd)
                pcfilename = (
                    cfile.cfilename if cfile.cfilepath is None
                    else os.path.join(cfile.cfilepath, cfile.cfilename))
                cfile = self.capp.get_file(pcfilename)
                cfile.reinitialize_tables()
                cfile.reload_ppos()
                cfile.reload_spos()

            self.capp.iter_files_parallel(f, processes)
        else:

            def f(cfile: "CFile") -> None:
                self.create_file_primary_proofobligations(
                    cfile.cfilename, cfile.cfilepath)

            self.capp.iter_files(f)

    def _generate_and_check_file_cmd_partial(
            self, cfilepath: Optional[str], domains: str) -> List[str]:
        cmd: List[str] = [
            self.canalyzer,
            "-summaries",
            self.chsummaries,
            "-command",
            "generate_and_check",
            "-domains",
            domains,
        ]
        if not (self.thirdpartysummaries is None):
            for s in self.thirdpartysummaries:
                cmd.extend(["-summaries", s])
        if not (self.contractpath is None):
            cmd.extend(["-contractpath", self.contractpath])
        cmd.extend(["-projectname", self.capp.projectname])
        if self.keep_system_includes:
            cmd.append("-keep_system_includes")
        if self.wordsize > 0:
            cmd.extend(["-wordsize", str(self.wordsize)])
        if self.unreachability:
            cmd.append("-unreachability")
        if self.verbose:
            cmd.append("-verbose")
        if self.collect_diagnostics:
            cmd.append("-diagnostics")
        cmd.append(self.targetpath)
        if cfilepath is not None:
            cmd.extend(["-cfilepath", cfilepath])
        cmd.append("-cfilename")
        return cmd

    def generate_and_check_file(
            self,
            cfilename: str,
            cfilepath: Optional[str],
            domains: str) -> None:
        """Generate invariants and check proof obligations for a single file."""

        try:
            cmd = self._generate_and_check_file_cmd_partial(cfilepath, domains)
            cmd.append(cfilename)
            chklogger.logger.info(
                "Calling AI to generate invariants: %s",
                " ".join(cmd))
            if self.verbose:
                result = subprocess.call(
                    cmd, cwd=self.targetpath, stderr=subprocess.STDOUT)
                print("\nResult: " + str(result))
            else:
                result = subprocess.call(
                    cmd,
                    cwd=self.targetpath,
                    # stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )
            if result != 0:
                chklogger.logger.error(
                    "Error in generating invariants for %s", cfilename)
                exit(1)
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def generate_and_check_app(self, domains: str, processes: int = 1) -> None:
        """Generate invariants and check proof obligations for application."""

        if processes > 1:

            def f(cfile: "CFile") -> None:
                cmd = self._generate_and_check_file_cmd_partial(
                    cfile.cfilepath, domains)
                cmd.append(cfile.cfilename)
                self._execute_cmd(cmd)

            self.capp.iter_files_parallel(f, processes)
        else:

            def f(cfile: "CFile") -> None:
                self.generate_and_check_file(
                    cfile.cfilename, cfile.cfilepath, domains)

            self.capp.iter_files(f)
        self.capp.iter_files(self.reset_tables)


if __name__ == "__main__":

    pass
