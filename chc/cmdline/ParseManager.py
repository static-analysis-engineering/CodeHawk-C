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

import os
import sys
import subprocess
import shlex
import shutil

import xml.etree.ElementTree as ET

from typing import Any, Dict, List, Optional, Tuple

from chc.util.Config import Config

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger
import chc.util.xmlutil as UX


class ParseManager(object):
    """Utility functions to support preprocessing and parsing source code.

    Naming conventions:

    - cfilename     base name of cfile analyzed (without extension)
    - cfilename_c   idem, with .c extension
    - projectpath   full-path in which cfilename_c resides (in case of a
                      single file analyzed) or in which the Makefile of
                      the project resides (in case of a multi-file project)
    - targetpath    full-path of directory in which results are saved
    - projectname   name under which results are saved

    Auxiliary names:

    - cchpath       full-path of analysis results (targetpath/projectname.cch)
    - cchname       base name of cchpath (projectname.cch)
    - cchtarname    projectname.cch.tar
    - cchtargzname  projectname.cch.tar.gz
    - cchtarfile    targetpath/projectname.cch.tar
    - cchtargzfile  targetpath/projectname.cch.tar.gz
    """

    def __init__(
            self,
            projectpath: str,
            projectname: str,
            targetpath: str,
            filter: bool = False,
            posix: bool = False,
            verbose: bool = True,
            keepUnused: bool = False,
            tgtplatform: str = "-m64",
    ) -> None:
        """Initialize paths to code, results, and parser executable.

        Args:
            cpath: absolute path to toplevel C source directory
            tgtpath: absolute path to analysis directory
            sempathname: local name of semantics directory

        Effects:
            creates tgtpath and subdirectories if necessary.
        """
        self._projectpath = projectpath
        self._projectname = projectname
        self._targetpath = targetpath
        self._cchpath = UF.get_cchpath(self._targetpath, self._projectname)
        self._savedsourcepath = UF.get_savedsource_path(
            self._targetpath, self._projectname)
        self._analysisresultspath = UF.get_analysisresults_path(
            self._targetpath, self._projectname)
        self._filter = filter
        self._posix = posix
        self._keepUnused = keepUnused
        self._verbose = verbose
        # compile to 32 bit or 64 bit platform (default 64 bit)
        self._tgtplatform = tgtplatform
        if not (self.tgtplatform in ["-m64", "-m32"]):
            print(
                "Warning: invalid target platform: "
                + self.tgtplatform
                + ". Target platform is set to -m64"
            )
            self._tgtplatform = "-m64"
        self.config = Config()

    @property
    def projectpath(self) -> str:
        return self._projectpath

    @property
    def targetpath(self) -> str:
        return self._targetpath

    @property
    def projectname(self) -> str:
        return self._projectname

    @property
    def cchpath(self) -> str:
        return self._cchpath

    @property
    def cchname(self) -> str:
        return os.path.basename(self.cchpath)

    @property
    def cchtarname(self) -> str:
        return self.cchname + ".tar"

    @property
    def cchtargzname(self) -> str:
        return self.cchtarname + ".gz"

    @property
    def cchtarfile(self) -> str:
        return os.path.join(self.targetpath, self.cchtarname)

    @property
    def cchtargzfile(self) -> str:
        return os.path.join(self.targetpath, self.cchtargzname)

    @property
    def savedsourcepath(self) -> str:
        return self._savedsourcepath

    @property
    def analysisresultspath(self) -> str:
        return self._analysisresultspath

    @property
    def tgtplatform(self) -> str:
        return self._tgtplatform

    @property
    def filter(self) -> bool:
        return self._filter

    @property
    def posix(self) -> bool:
        return self._posix

    @property
    def verbose(self) -> bool:
        return self._verbose

    @property
    def keepUnused(self) -> bool:
        """If true keep variables parsed that are never used."""

        return self._keepUnused

    def remove_semantics(self) -> None:
        if os.path.isdir(self.cchpath):
            chklogger.logger.info(
                "Removing semantics directory %s", self.cchpath)
            shutil.rmtree(self.cchpath)
            if os.path.isfile(self.cchtargzfile):
                chklogger.logger.info(
                    "Removing semantics tar.gz %s", self.cchtargzfile)
                os.remove(self.cchtargzfile)

    def save_semantics(self) -> None:
        """Save the semantics directory as a tar.gz file."""

        chklogger.logger.info("change directory to %s", self.targetpath)
        cwd = os.getcwd()
        os.chdir(self.targetpath)
        if os.path.isfile(self.cchtarname):
            chklogger.logger.info("Remove tar file %s", self.cchtarname)
            os.remove(self.cchtarname)
        if os.path.isfile(self.cchtargzname):
            chklogger.logger.info("Remove tar.gz file %s", self.cchtargzname)
            os.remove(self.cchtargzname)
        tarcmd = ["tar", "cf", self.cchtarname, self.cchname]
        chklogger.logger.debug("tar command: %s", " ".join(tarcmd))
        if self.verbose:
            subprocess.call(tarcmd, stderr=subprocess.STDOUT)
        else:
            subprocess.call(
                tarcmd,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        gzipcmd = ["gzip", self.cchtarname]
        chklogger.logger.debug("gzip command: %s", " ".join(gzipcmd))
        if self.verbose:
            subprocess.call(gzipcmd, stderr=subprocess.STDOUT)
        else:
            subprocess.call(
                gzipcmd,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        os.chdir(cwd)

    def preprocess_file_with_gcc(
            self,
            cfilename: str,
            copyfiles: bool = True,
            moreoptions: List[str] = []) -> str:
        """Invoke gcc preprocessor on c source file.

        Args:
            cfilename: c source code filename relative to cpath
            moreoptions: list of additional options to be given to the
                           preprocessor

        Effects:
            invokes the gcc preprocessor on the c source file and optionally
            copies the original source file and the generated .i file to the
            tgtpath/sourcefiles directory
        """

        chklogger.logger.info("Preprocess file with gcc: %s", cfilename)
        cwd = os.getcwd()
        mac = self.config.platform == "mac"
        ifilename = cfilename[:-1] + "i"
        macoptions = [
            "-U___BLOCKS___", "-D_DARWIN_C_SOURCE", "-D_FORTIFY_SOURCE=0"]
        cmd = [
            "gcc",
            "-fno-inline",
            "-fno-builtin",
            "-E",
            "-g",
            self.tgtplatform,
            "-o",
            ifilename,
            cfilename,
        ]
        if mac:
            cmd = cmd[:1] + macoptions + cmd[1:]
        cmd = cmd[:1] + moreoptions + cmd[1:]
        chklogger.logger.info("Changing directory to %s", self.projectpath)
        os.chdir(self.projectpath)
        if self.verbose:
            chklogger.logger.info("Preprocess file: " + str(cmd))
            p = subprocess.call(
                cmd, cwd=self.projectpath, stderr=subprocess.STDOUT)
            if p != 0:
                chklogger.logger.warning("Result of preprocessing: " + str(p))
        else:
            chklogger.logger.info("Preprocess file: " + str(cmd))
            subprocess.call(
                cmd,
                cwd=self.projectpath,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        if copyfiles:
            tgtcfilename = os.path.join(self.savedsourcepath, cfilename)
            tgtifilename = os.path.join(self.savedsourcepath, ifilename)
            if not os.path.isdir(os.path.dirname(tgtcfilename)):
                os.makedirs(os.path.dirname(tgtcfilename))
            if cfilename != tgtcfilename:
                chklogger.logger.info("Copy %s to %s", cfilename, tgtcfilename)
                shutil.copy(cfilename, tgtcfilename)
                chklogger.logger.info("Copy %s to %s", ifilename, tgtifilename)
                shutil.copy(ifilename, tgtifilename)
        os.chdir(cwd)
        return ifilename

    def get_file_length(self, fname: str) -> int:
        """Return the number of lines in named file."""

        with open(fname) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def normalize_filename(self, filename: str) -> str:
        """Make filename relative to project directory (if in project
        directory)."""

        filename = os.path.normpath(filename)
        if filename.startswith(self.projectpath):
            return filename[(len(self.projectpath) + 1):]
        else:
            return filename

    def has_platform(self, cmd: List[str]) -> bool:
        return ("-m32" in cmd) or ("-m64" in cmd)

    def get_platform_index(self, cmd: List[str]) -> int:
        if "-m32" in cmd:
            return cmd.index("-m32")
        elif "-m64" in cmd:
            return cmd.index("-m64")
        else:
            return -1

    def set_platform(self, cmd: List[str]) -> None:
        index = self.get_platform_index(cmd)
        if index >= 0:
            platform = cmd[index]
            if platform == self.tgtplatform:
                return
            else:
                cmd[index] = self.tgtplatform
        else:
            cmd.append(self.tgtplatform)

    def preprocess(
            self,
            ccommand: Dict[str, Any],
            copyfiles: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """Modify and replay compile_commands.json file produced by bear."""

        if self.verbose:
            print("\n\n" + ("=" * 80))
        if self.verbose:
            print("***** " + str(ccommand["file"]) + " *****")
        if self.verbose:
            print("=" * 80)
        for p in ccommand:
            print(str(p) + ": " + str(ccommand[p]))
        if "arguments" in ccommand:
            command: List[str] = ccommand["arguments"]
        else:
            command = shlex.split(ccommand["command"], self.posix)
        ecommand = command[:]
        cfilename: str = os.path.join(ccommand["directory"], ccommand["file"])
        if cfilename.endswith(".c"):
            ifilename = cfilename[:-1] + "i"
            try:
                outputflagindex = command.index("-o")
                ecommand[outputflagindex + 1] = ifilename
            except ValueError:
                ecommand.append("-o")
                ecommand.append(ifilename)
            try:
                ecommand.remove("-O2")
            except BaseException:
                pass
            ecommand.append("-g")
            ecommand.append("-E")
            ecommand.append("-fno-stack-protector")
            ecommand.append("-fno-inline")
            ecommand.append("-fno-builtin")
            ecommand.append("-fno-asm")
            self.set_platform(ecommand)

            # issue modified command to produce i files
            if self.verbose:
                print("\nIssue command: " + str(ecommand) + "\n")
                resultcode = subprocess.call(
                    ecommand,
                    cwd=ccommand["directory"],
                    stderr=subprocess.STDOUT
                )
                print("result: " + str(resultcode))
            else:
                subprocess.call(
                    ecommand,
                    cwd=ccommand["directory"],
                    stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )

            # issue original command
            if self.verbose:
                print("\nIssue original command: " + str(command) + "\n")
                resultcode = subprocess.call(
                    command, cwd=ccommand["directory"], stderr=subprocess.STDOUT
                )
                print("result: " + str(resultcode))
            else:
                subprocess.call(
                    command,
                    cwd=ccommand["directory"],
                    stdout=open(os.devnull, "w"),
                    stderr=subprocess.STDOUT,
                )

            if copyfiles:
                tgtcfilename = os.path.join(
                    self.savedsourcepath, self.normalize_filename(cfilename)
                )
                tgtifilename = os.path.join(
                    self.savedsourcepath, self.normalize_filename(ifilename)
                )
                tgtcdir = os.path.dirname(tgtcfilename)
                if not os.path.isdir(tgtcdir):
                    os.makedirs(tgtcdir)
                os.chdir(self.projectpath)
                if os.path.normpath(cfilename) != os.path.normpath(tgtcfilename):
                    shutil.copy(cfilename, tgtcfilename)
                    shutil.copy(ifilename, tgtifilename)
            return (cfilename, ifilename)
        else:
            print("\nCCWarning: Filename not recognized: " + cfilename)
            return (None, None)

    def parse_with_ccommands(
            self,
            compilecommands: List[Dict[str, Any]],
            copyfiles: bool = True) -> None:
        """Preprocess and call C parser to produce xml semantics files."""

        cfiles: Dict[str, int] = {}
        targetfiles = TargetFiles()
        for c in compilecommands:
            (cfilename, ifilename) = self.preprocess(c, copyfiles)
            if cfilename is None:
                continue
            if ifilename is None:
                continue
            cfilename = os.path.abspath(cfilename)
            ifilename = os.path.abspath(ifilename)
            command = [
                self.config.cparser,
                "-projectpath",
                self.projectpath,
                "-targetdirectory",
                self.analysisresultspath
            ]
            if not self.filter:
                command.append("-nofilter")
            if self.keepUnused:
                command.append("-keepUnused")
            command.append(ifilename)
            cfilelen = self.get_file_length(cfilename)
            cfiles[cfilename] = cfilelen
            if self.verbose:
                print("\nRun the parser: " + str(command) + "\n")
            sys.stdout.flush()
            if self.verbose:
                subprocess.call(command)
                print("\n" + ("-" * 80) + "\n\n")
            else:
                subprocess.call(command, stdout=open(os.devnull, "w"))

        if self.verbose:
            print("\n\nCollect c files")
        for n in cfiles:
            n = os.path.abspath(n)
            name = self.normalize_filename(n)
            if self.verbose:
                print("   Add " + name + " (" + str(cfiles[n]) + " lines)")
            targetfiles.add_file(name)
        targetfiles.save_xml_file(self.analysisresultspath)
        linecount = sum(cfiles[n] for n in cfiles)
        if self.verbose:
            print(
                "\nTotal "
                + str(len(cfiles))
                + " files ("
                + str(linecount)
                + " lines)"
            )
        os.chdir(self.projectpath)
        shutil.copy("compile_commands.json", self.savedsourcepath)

    def parse_ifiles(self, copyfiles: bool = True) -> None:
        """Run the CodeHawk C parser on all .i files in the directory."""

        chklogger.logger.info("Change directory to %s", self.projectpath)
        os.chdir(self.projectpath)
        targetfiles = TargetFiles()
        for d, dnames, fnames in os.walk(self.projectpath):
            for fname in fnames:
                if fname.endswith(".i"):
                    self.parse_ifile(fname)
                    basename = fname[:-2]
                    cfile = basename + ".c"
                    targetfiles.add_file(self.normalize_filename(cfile))
        targetfiles.save_xml_file(self.analysisresultspath)

    def parse_cfiles(self, copyfiles: bool = True) -> None:
        """Preprocess (with gcc) and run the CodeHawk C parser on all .c
        files in the directory."""

        os.chdir(self.projectpath)
        targetfiles = TargetFiles()
        for d, dnames, fnames in os.walk(self.projectpath):
            for fname in fnames:
                if fname.endswith(".c"):
                    fname = self.normalize_filename(os.path.join(d, fname))
                    if fname.startswith("semantics"):
                        continue
                    ifilename = self.preprocess_file_with_gcc(fname, copyfiles)
                    self.parse_ifile(ifilename)
                    targetfiles.add_file(self.normalize_filename(fname))
        targetfiles.save_xml_file(self.analysisresultspath)

    def parse_ifile(self, ifilename: str) -> int:
        """Invoke the CodeHawk C parser frontend on preprocessed source file

        Args:
            ifilename: preprocessed source code filename relative to cpath

        Effects:
            invokes the parser frontend to produce an xml representation
            of the semantics of the file
        """

        ifilename = os.path.join(self.projectpath, ifilename)
        cmd = [
            self.config.cparser,
            "-projectpath",
            self.projectpath,
            "-targetdirectory",
            self.analysisresultspath,
        ]
        if not self.filter:
            cmd.append("-nofilter")
        if self.keepUnused:
            cmd.append("-keepUnused")
        cmd.append(ifilename)
        chklogger.logger.info("Parse file: %s", str(cmd))
        if self.verbose:
            p = subprocess.call(cmd, stderr=subprocess.STDOUT)
        else:
            p = subprocess.call(
                cmd, stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
        sys.stdout.flush()
        return p

    def initialize_paths(self) -> None:
        """Create directories for the target path."""
        if not os.path.isdir(self.cchpath):
            chklogger.logger.info("Make directory %s", self.cchpath)
            os.mkdir(self.cchpath)
        if not os.path.isdir(self.analysisresultspath):
            chklogger.logger.info("Make directory %s", self.analysisresultspath)
            os.mkdir(self.analysisresultspath)
        if not os.path.isdir(self.savedsourcepath):
            chklogger.logger.info("Make directory %s", self.savedsourcepath)
            os.mkdir(self.savedsourcepath)


class TargetFiles:

    def __init__(self) -> None:
        self.files: Dict[str, int] = {}   # filename -> file length

    def add_file(self, fname: str) -> None:
        self.files.setdefault(fname, len(self.files))

    def save_xml_file(self, tgtpath: str) -> None:
        tgtroot = UX.get_xml_header("target_files", "c-files")
        cfilesnode = ET.Element("c-files")
        tgtroot.append(cfilesnode)
        for name in sorted(self.files):
            xcfile = ET.Element("c-file")
            xcfile.set("name", name)
            xcfile.set("id", str(self.files[name]))
            cfilesnode.append(xcfile)
        cfilesnode.set("file-count", str(len(self.files)))
        tgtfilename = os.path.join(tgtpath, "target_files.xml")
        with open(tgtfilename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(tgtroot)))


if __name__ == "__main__":

    # preprocess and parse single files with gcc
    thisdir = os.path.dirname(os.path.abspath(__file__))
    topdir = os.path.dirname(os.path.dirname(thisdir))
    testsdir = os.path.join(topdir, "tests")
    kendradir = os.path.join(testsdir, "kendra")
    id115dir = os.path.join(kendradir, "id115Q")
    pm = ParseManager(id115dir, "kendra115", id115dir)
    pm.initialize_paths()
    for f in ["id115.c", "id116.c", "id117.c", "id118.c"]:
        ifilename = pm.preprocess_file_with_gcc(f)
        pm.parse_ifile(ifilename)
