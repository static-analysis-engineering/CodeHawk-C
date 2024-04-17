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

from typing import List, Optional, TYPE_CHECKING

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
        nofilter: bool = True,
        verbose: bool = True,
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
        # self.contractpath = capp.contractpath
        self._config = Config()
        # self.chsummaries = self.config.summaries
        # self.path = self.capp.path
        # self.canalyzer = self.config.canalyzer
        # self.gui = self.config.chc_gui
        self.nofilter = nofilter
        self.wordsize = wordsize
        self.thirdpartysummaries = thirdpartysummaries
        self.unreachability = unreachability
        self.verbose = verbose

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def contractpath(self) -> Optional[str]:
        return None

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

    def reset(self) -> None:
        """Remove all file- and function-level files produced by the analysis."""

        def remove(f: str) -> None:
            if os.path.isfile(f):
                os.remove(f)

        def g(fi: "CFile") -> None:
            cfiledir = UF.get_cfile_directory(self.path, fi.name)
            if os.path.isdir(cfiledir):
                for f in os.listdir(cfiledir):
                    if len(f) > 10 and (
                        f[-8:-4] in ["_api", "_ppo", "_spo", "_pod"]
                        or f[-9:-4] in ["_invs", "_vars"]
                    ):
                        os.remove(os.path.join(cfiledir, f))
            remove(UF.get_cfile_predicate_dictionaryname(self.capp.path, fi.name))
            remove(UF.get_cfile_interface_dictionaryname(self.capp.path, fi.name))
            remove(UF.get_cfile_assignment_dictionaryname(self.capp.path, fi.name))
            remove(UF.get_cxreffile_filename(self.capp.path, fi.name))
            remove(UF.get_cfile_contexttablename(self.capp.path, fi.name))

        self.capp.iter_files(g)
        remove(UF.get_global_definitions_filename(self.capp.path))

    def reset_logfiles(self) -> None:
        """Remove all log files from semantics directory."""

        def g(fi: "CFile") -> None:
            logfiledir = UF.get_cfile_logfiles_directory(self.path, fi.name)
            if os.path.isdir(logfiledir):
                for f in os.listdir(logfiledir):
                    if (
                        f.endswith("chlog")
                        or f.endswith("infolog")
                        or f.endswith("errorlog")
                    ):
                        os.remove(os.path.join(logfiledir, f))

        self.capp.iter_files(g)

    def reset_tables(self, cfilename: str) -> None:
        """Reload dictionaries from file (to get updated data from analyzer)."""

        cfile = self.capp.get_file(cfilename)
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

    def _create_file_primary_proofobligations_cmd_partial(self) -> List[str]:
        cmd: List[str] = [
            self.canalyzer, "-summaries", self.chsummaries, "-command", "primary"]
        if not (self.thirdpartysummaries is None):
            for s in self.thirdpartysummaries:
                cmd.extend(["-summaries", s])
        if not (self.contractpath is None):
            cmd.extend(["-contractpath", self.contractpath])
        cmd.extend(["-projectname", self.capp.projectname])

        if self.nofilter:
            cmd.append("-nofilter")
        if self.wordsize > 0:
            cmd.extend(["-wordsize", str(self.wordsize)])
        cmd.append(self.targetpath)
        cmd.append("-cfilename")
        return cmd

    def rungui(self, name: str, outputpath: Optional[str] = None) -> None:
        semdir = os.path.dirname(self.path)
        analysisdir = os.path.dirname(semdir)
        if outputpath is None:
            outputpath = analysisdir
        if self.gui is None:
            print("Gui has not been configured.")
            exit(1)
        cmd: List[str] = [
            self.gui,
            "-summaries",
            self.chsummaries,
            "-output",
            outputpath,
            "-name",
            name,
            "-xpm",
            self.config.utildir,
            "-analysisdir",
            analysisdir,
            "-contractpath",
            self.contractpath,
        ]
        print(cmd)
        try:
            result = subprocess.call(
                cmd,
                cwd=self.path,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def create_file_primary_proofobligations(
            self, cfilename: str, cfilepath: Optional[str] = None) -> None:
        """Call analyzer to create primary proof obligations for a single file."""

        try:
            cmd = self._create_file_primary_proofobligations_cmd_partial()
            cmd.append(cfilename)
            if cfilepath is not None:
                cmd.extend(["-cfilepath", cfilepath])
            if self.verbose:
                chklogger.logger.info(
                    "Primary proof obligations are created for %s", cfilename)
                chklogger.logger.info(
                    "Ocaml analyzer is called with %s", str(cmd))
                result = subprocess.call(
                    cmd, cwd=self.targetpath, stderr=subprocess.STDOUT)
                print("\nResult: " + str(result))
                # self.capp.get_file(cfilename).predicatedictionary.initialize()
            else:
                result = subprocess.call(
                    cmd,
                    cwd=self.path,
                    stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )
            if result != 0:
                print("Error in creating primary proof obligations")
                exit(1)
            cfile = self.capp.get_file(cfilename)
            cfile.reinitialize_tables()
            cfile.reload_ppos()
            cfile.reload_spos()
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def create_app_primary_proofobligations(self, processes: int = 1) -> None:
        """Call analyzer to create primary proof obligations for all application files."""

        if processes > 1:

            def f(cfile: str) -> None:
                cmd = self._create_file_primary_proofobligations_cmd_partial()
                cmd.append(cfile)
                self._execute_cmd(cmd)

            self.capp.iter_filenames_parallel(f, processes)
        else:

            def f(cfile: str) -> None:
                self.create_file_primary_proofobligations(cfile)

            self.capp.iter_filenames(f)

    def _generate_and_check_file_cmd_partial(self, domains: str) -> List[str]:
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
        if self.nofilter:
            cmd.append("-nofilter")
        if self.wordsize > 0:
            cmd.extend(["-wordsize", str(self.wordsize)])
        if self.unreachability:
            cmd.append("-unreachability")
        if self.verbose:
            cmd.append("-verbose")
        cmd.append(self.targetpath)
        cmd.append("-cfilename")
        return cmd

    def generate_and_check_file(self, cfilename: str, domains: str) -> None:
        """Generate invariants and check proof obligations for a single file."""

        try:
            cmd = self._generate_and_check_file_cmd_partial(domains)
            cmd.append(cfilename)
            if self.verbose:
                print(
                    "Generating invariants and checking proof obligations for "
                    + cfilename
                )
                print(cmd)
                result = subprocess.call(
                    cmd, cwd=self.targetpath, stderr=subprocess.STDOUT)
                print("\nResult: " + str(result))
            else:
                result = subprocess.call(
                    cmd,
                    cwd=self.path,
                    stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )
            if result != 0:
                print("Error in generating invariants or checking proof obligations")
                exit(1)
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def generate_and_check_app(self, domains: str, processes: int = 1) -> None:
        """Generate invariants and check proof obligations for application."""

        if processes > 1:

            def f(cfile: str) -> None:
                cmd = self._generate_and_check_file_cmd_partial(domains)
                cmd.append(cfile)
                self._execute_cmd(cmd)

            self.capp.iter_filenames_parallel(f, processes)
        else:

            def f(cfile: str) -> None:
                self.generate_and_check_file(cfile, domains)

            self.capp.iter_filenames(f)
        self.capp.iter_filenames(self.reset_tables)


if __name__ == "__main__":

    pass
