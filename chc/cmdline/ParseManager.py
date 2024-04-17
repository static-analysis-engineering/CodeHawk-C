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

from chc.util.loggingutil import chklogger
import chc.util.xmlutil as UX


class ParseManager(object):
    """Utility functions to support preprocessing and parsing source code.

    Attributes:
        sempath (string): absolute path to semantics directory
        tgtxpath (string): absolute path to semantics/chcartifacts directory
        tgtspath (string): absolute path to semantics/sourcefiles directory
    """

    def __init__(
            self,
            cpath: str,
            tgtpath: str,
            sempathname: str,
            filter: bool = False,
            posix: bool = False,
            verbose: bool = True,
            keepUnused: bool = False,
            tgtplatform: str= "-m64",
    ) -> None:
        """Initialize paths to code, results, and parser executable.

        Args:
            cpath: absolute path to toplevel C source directory
            tgtpath: absolute path to analysis directory
            sempathname: local name of semantics directory

        Effects:
            creates tgtpath and subdirectories if necessary.
        """
        self._cpath = cpath
        self._tgtpath = tgtpath
        self._sempathname = sempathname
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
    def cpath(self) -> str:
        return self._cpath

    @property
    def tgtpath(self) -> str:
        return self._tgtpath

    @property
    def sempathname(self) -> str:
        return self._sempathname

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

    @property
    def sempath(self) -> str:
        return os.path.join(self._tgtpath, self.sempathname)

    @property
    def tgtxpath(self) -> str:
        """Return path to analysis results files."""

        return os.path.join(self.sempath, "a")

    @property
    def tgtspath(self) -> str:
        """Return path to .c and .i files"""

        return os.path.join(self.sempath, "s")

    def save_semantics(self) -> None:
        """Save the semantics directory as a tar.gz file."""

        chklogger.logger.info("change directory to %s", self.tgtpath)
        os.chdir(self.tgtpath)
        tarfilename = self.sempathname + ".tar"
        if os.path.isfile(tarfilename):
            chklogger.logger.info("Remove tar file %s", tarfilename)
            os.remove(tarfilename)
        if os.path.isfile(tarfilename + ".gz"):
            chklogger.logger.info("Remove tar.gz file %s", tarfilename + ".gz")
            os.remove(tarfilename + ".gz")
        tarcmd = ["tar", "-cf", tarfilename, self.sempathname]
        chklogger.logger.debug("tar command: %s", " ".join(tarcmd))
        if self.verbose:
            subprocess.call(tarcmd, cwd=self.cpath, stderr=subprocess.STDOUT)
        else:
            subprocess.call(
                tarcmd,
                cwd=self.cpath,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        gzipcmd = ["gzip", tarfilename]
        if self.verbose:
            subprocess.call(gzipcmd, cwd=self.cpath, stderr=subprocess.STDOUT)
        else:
            subprocess.call(
                gzipcmd,
                cwd=self.cpath,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )

    def preprocess_file_with_gcc(
            self,
            cfilename: str,
            copyfiles: bool = True,
            moreoptions: List[str] = []) -> str:
        """Invoke gcc preprocessor on c source file.

        Args:
            cfilename: c source code filename relative to cpath
            moreoptions: list of additional options to be given to the preprocessor

        Effects:
            invokes the gcc preprocessor on the c source file and optionally copies
            the original source file and the generated .i file to the
            tgtpath/sourcefiles directory
        """

        mac = self.config.platform == "mac"
        ifilename = cfilename[:-1] + "i"
        macoptions = ["-U___BLOCKS___", "-D_DARWIN_C_SOURCE", "-D_FORTIFY_SOURCE=0"]
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
        if self.verbose:
            chklogger.logger.info("Preprocess file: " + str(cmd))
            p = subprocess.call(cmd, cwd=self.cpath, stderr=subprocess.STDOUT)
            if p != 0:
                chklogger.logger.warning("Result of preprocessing: " + str(p))
        else:
            chklogger.logger.info("Preprocess file: " + str(cmd))
            subprocess.call(
                cmd,
                cwd=self.cpath,
                stdout=open(os.devnull, "w"),
                stderr=subprocess.STDOUT,
            )
        if copyfiles:
            tgtcfilename = os.path.join(self.tgtspath, cfilename)
            tgtifilename = os.path.join(self.tgtspath, ifilename)
            if not os.path.isdir(os.path.dirname(tgtcfilename)):
                os.makedirs(os.path.dirname(tgtcfilename))
            chklogger.logger.info("Change directory to %s", self.cpath)
            os.chdir(self.cpath)
            if cfilename != tgtcfilename:
                chklogger.logger.info("Copy %s to %s", cfilename, tgtcfilename)
                shutil.copy(cfilename, tgtcfilename)
                chklogger.logger.info("Copy %s to %s", ifilename, tgtifilename)
                shutil.copy(ifilename, tgtifilename)
        return ifilename

    def get_file_length(self, fname: str) -> int:
        """Return the number of lines in named file."""

        with open(fname) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def normalize_filename(self, filename: str) -> str:
        """Make filename relative to application directory (if in application directory)."""

        filename = os.path.normpath(filename)
        if filename.startswith(self.cpath):
            return filename[(len(self.cpath) + 1):]
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
                    ecommand, cwd=ccommand["directory"], stderr=subprocess.STDOUT
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
                    self.tgtspath, self.normalize_filename(cfilename)
                )
                tgtifilename = os.path.join(
                    self.tgtspath, self.normalize_filename(ifilename)
                )
                tgtcdir = os.path.dirname(tgtcfilename)
                if not os.path.isdir(tgtcdir):
                    os.makedirs(tgtcdir)
                os.chdir(self.cpath)
                if os.path.normpath(cfilename) != os.path.normpath(tgtcfilename):
                    shutil.copy(cfilename, tgtcfilename)
                    shutil.copy(ifilename, tgtifilename)
            return (cfilename, ifilename)
        else:
            print("\nCCWarning: Filename not recognized: " + cfilename)
            return (None, None)

    def parse_with_ccommands(
            self, compilecommands: List[Dict[str, Any]], copyfiles: bool = True) -> None:
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
                self.cpath,
                "-targetdirectory",
                self.tgtxpath,
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
        targetfiles.save_xml_file(self.tgtxpath)
        linecount = sum(cfiles[n] for n in cfiles)
        if self.verbose:
            print(
                "\nTotal " + str(len(cfiles)) + " files (" + str(linecount) + " lines)"
            )
        os.chdir(self.cpath)
        shutil.copy("compile_commands.json", self.tgtspath)

    def parse_ifiles(self, copyfiles: bool = True) -> None:
        """Run the CodeHawk C parser on all .i files in the directory."""

        chklogger.logger.info("Change directory to %s", self.cpath)
        os.chdir(self.cpath)
        targetfiles = TargetFiles()
        for d, dnames, fnames in os.walk(self.cpath):
            for fname in fnames:
                if fname.endswith(".i"):
                    self.parse_ifile(fname)
                    basename = fname[:-2]
                    cfile = basename + ".c"
                    targetfiles.add_file(self.normalize_filename(cfile))
        targetfiles.save_xml_file(self.tgtxpath)

    def parse_cfiles(self, copyfiles: bool = True) -> None:
        """Preprocess (with gcc) and run the CodeHawk C parser on all .c files in the directory."""

        os.chdir(self.cpath)
        targetfiles = TargetFiles()
        for d, dnames, fnames in os.walk(self.cpath):
            for fname in fnames:
                if fname.endswith(".c"):
                    fname = self.normalize_filename(os.path.join(d, fname))
                    if fname.startswith("semantics"):
                        continue
                    ifilename = self.preprocess_file_with_gcc(fname, copyfiles)
                    self.parse_ifile(ifilename)
                    targetfiles.add_file(self.normalize_filename(fname))
        targetfiles.save_xml_file(self.tgtxpath)

    def parse_ifile(self, ifilename: str) -> int:
        """Invoke the CodeHawk C parser frontend on preprocessed source file

        Args:
            ifilename: preprocessed source code filename relative to cpath

        Effects:
            invokes the parser frontend to produce an xml representation
            of the semantics of the file
        """

        ifilename = os.path.join(self.cpath, ifilename)
        cmd = [
            self.config.cparser,
            "-projectpath",
            self.cpath,
            "-targetdirectory",
            self.tgtxpath,
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
        if not os.path.isdir(self.tgtpath):
            os.mkdir(self.tgtpath)
        if not os.path.isdir(self.sempath):
            os.mkdir(self.sempath)
        if not os.path.isdir(self.tgtxpath):
            os.mkdir(self.tgtxpath)
        if not os.path.isdir(self.tgtspath):
            os.mkdir(self.tgtspath)


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
    pm = ParseManager(id115dir, id115dir)
    pm.initialize_paths()
    for f in ["id115.c", "id116.c", "id117.c", "id118.c"]:
        ifilename = pm.preprocess_file_with_gcc(f)
        pm.parse_ifile(ifilename)
