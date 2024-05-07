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

import json
import os
import shutil

from typing import Dict, List, Optional, TYPE_CHECKING

from chc.app.CApplication import CApplication

from chc.cmdline.AnalysisManager import AnalysisManager

from chc.cmdline.kendra.TestCFileRef import TestCFileRef
from chc.cmdline.kendra.TestCFunctionRef import TestCFunctionRef
from chc.cmdline.kendra.TestPPORef import TestPPORef
from chc.cmdline.kendra.TestResults import TestResults
from chc.cmdline.kendra.TestSetRef import TestSetRef
from chc.cmdline.kendra.TestSPORef import TestSPORef
from chc.cmdline.ParseManager import ParseManager

from chc.util.Config import Config
import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger


if TYPE_CHECKING:
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionPO import CFunctionPO
    from chc.proof.CFunctionPPO import CFunctionPPO


class FileParseError(UF.CHCError):
    def __init__(self, msg: str) -> None:
        UF.CHCError.__init__(self, msg)


class XmlFileNotFoundError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class FunctionPPOError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class FunctionSPOError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class FunctionPEVError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class FunctionSEVError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class AnalyzerMissingError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class TestManager:
    """Provide utility functions to support regression and platform tests.

    Args:
        projectpath: directory that holds the source code
        targetpath: directory that holds the chc artifacts directory
        testname: name of the test directory
        saveref: adds missing ppos to functions in the json spec file and
                 overwrites the json file with the result
    """

    def __init__(
            self,
            projectpath: str,
            targetpath: str,
            testname: str,
            saveref: bool = False,
            verbose: bool = True) -> None:
        self._projectpath = projectpath
        self._targetpath = targetpath
        self._testname = testname
        self._saveref = saveref
        self._config = Config()
        self._verbose = verbose
        testfilename = os.path.join(self.projectpath, testname + ".json")
        self._testsetref = TestSetRef(testfilename)
        self._testresults = TestResults(self.testsetref)
        self._parsemanager: Optional[ParseManager] = None

    @property
    def projectpath(self) -> str:
        return self._projectpath

    @property
    def targetpath(self) -> str:
        return self._targetpath

    @property
    def testname(self) -> str:
        return self._testname

    @property
    def parsemanager(self) -> ParseManager:
        if self._parsemanager is None:
            self._parsemanager = ParseManager(
                self.projectpath,
                self.testname,
                self.targetpath,
                verbose=self.verbose)
        return self._parsemanager

    @property
    def cchpath(self) -> str:
        return self.parsemanager.cchpath

    @property
    def analysisresultspath(self) -> str:
        return self.parsemanager.analysisresultspath

    @property
    def savedsourcepath(self) -> str:
        return self.parsemanager.savedsourcepath

    @property
    def testsetref(self) -> TestSetRef:
        return self._testsetref

    @property
    def testresults(self) -> TestResults:
        return self._testresults

    @property
    def contractpath(self) -> str:
        return os.path.join(self.targetpath, "chccontracts")

    @property
    def saveref(self) -> bool:
        return self._saveref

    @property
    def config(self) -> Config:
        return self._config

    @property
    def ismac(self) -> bool:
        return self.config.platform == "macOS"

    @property
    def is_linux_only(self) -> bool:
        return self.testsetref.is_linux_only

    @property
    def verbose(self) -> bool:
        return self._verbose

    def print_test_results(self) -> None:
        print(str(self.testresults))

    def print_test_results_summary(self) -> None:
        print(str(self.testresults.get_summary()))

    def print_test_results_line_summary(self) -> None:
        print(str(self.testresults.get_line_summary()))

    def test_parser(self, savesemantics: bool = False) -> bool:
        self.testresults.set_parsing()
        self.clean()
        self.parsemanager.initialize_paths()
        for cfile in self.cref_files:
            cfilename_c = cfile.name
            ifilename = self.parsemanager.preprocess_file_with_gcc(
                cfilename_c, copyfiles=True
            )
            parseresult = self.parsemanager.parse_ifile(ifilename)
            if parseresult != 0:
                chklogger.logger.warning("File parse error for %s", ifilename)
                self.testresults.add_parse_error(cfilename_c, str(parseresult))
                raise FileParseError(cfilename_c)
            self.testresults.add_parse_success(cfilename_c)
            if self.xcfile_exists(cfilename_c):
                self.testresults.add_xcfile_success(cfilename_c)
            else:
                chklogger.logger.warning(
                    "Test results not found for %s", cfilename_c)
                self.testresults.add_xcfile_error(cfilename_c)
                raise FileParseError(cfilename_c)
            for fname in cfile.functionnames:
                if self.xffile_exists(cfilename_c, fname):
                    self.testresults.add_xffile_success(cfilename_c, fname)
                else:
                    self.testresults.add_xffile_error(cfilename_c, fname)
                    raise FileParseError(cfilename_c)
        if savesemantics:
            self.parsemanager.save_semantics()
        return True

    def check_ppos(
            self,
            cfilename: str,
            cfun: str,
            ppos: List["CFunctionPO"],
            refppos: List[TestPPORef]) -> None:
        """Check if all required primary proof obligations are created."""

        d: Dict[str, List[str]] = {}
        # collect ppos produced
        for ppo in ppos:
            context = ppo.context_strings
            if context not in d:
                d[context] = []
            d[context].append(ppo.predicate_name)

        # compare with reference ppos
        for refppo in refppos:
            p = refppo.predicate
            context = refppo.context_string
            if context not in d:
                self.testresults.add_missing_ppo(cfilename, cfun, context, p)
                for c in d:
                    if self.verbose:
                        print(str(c))
                        print("Did not find " + str(context))
                raise FunctionPPOError(
                    cfilename
                    + ":"
                    + cfun
                    + ":"
                    + " Missing ppo: "
                    + str(context)
                )
            else:
                if p not in d[context]:
                    self.testresults.add_missing_ppo(cfilename, cfun, context, p)
                    raise FunctionPPOError(
                        cfilename + ":" + cfun + ":" + str(context) + ":" + p
                    )

    def create_reference_ppos(
            self,
            cfilename: str,
            fname: str,
            ppos: List["CFunctionPPO"]) -> None:
        """Create reference ppos from actual analysis results."""

        result: List[Dict[str, str]] = []
        for ppo in ppos:
            ctxt = ppo.context
            d: Dict[str, str] = {}
            d["line"] = str(ppo.line)
            d["cfgctxt"] = str(ctxt.cfg_context)
            d["expctxt"] = str(ctxt.exp_context)
            d["predicate"] = ppo.predicate_name
            d["tgtstatus"] = "open"
            d["status"] = "open"
            result.append(d)
        self.testsetref.set_ppos(cfilename, fname, result)

    def create_reference_spos(
            self,
            cfilename: str,
            fname: str,
            spos: List["CFunctionPO"]) -> None:
        """Create reference spos from actual analysis results."""

        result: List[Dict[str, str]] = []
        if len(spos) > 0:
            for spo in spos:
                d: Dict[str, str] = {}
                d["line"] = str(spo.line)
                d["cfgctxt"] = spo.context_strings
                d["tgtstatus"] = "unknown"
                d["status"] = "unknown"
                result.append(d)
            self.testsetref.set_spos(cfilename, fname, result)

    def test_ppos(self) -> None:
        """Create primary proof obligations and check if created as expected."""

        if not os.path.isfile(self.config.canalyzer):
            raise AnalyzerMissingError(self.config.canalyzer)
        self.testresults.set_ppos()
        saved = False
        try:
            for creffile in self.cref_files:
                creffilename_c = creffile.name
                if not self.xcfile_exists(creffilename_c):
                    raise XmlFileNotFoundError(creffilename_c)
                capp = CApplication(
                    self.projectpath,
                    self.testname,
                    self.targetpath,
                    contractpath=self.contractpath,
                    singlefile=True
                )
                cfilename = creffilename_c[:-2]
                capp.initialize_single_file(cfilename)
                am = AnalysisManager(capp, verbose=self.verbose)
                am.create_file_primary_proofobligations(cfilename)
                cfile = capp.get_cfile()
                capp.collect_post_assumes()
                ppos = cfile.get_ppos()
                for creffun in creffile.functions.values():
                    fname = creffun.name
                    cfun = cfile.get_function_by_name(fname)
                    if self.saveref:
                        if creffun.has_ppos():
                            chklogger.logger.warning(
                                "Ppos not created for %s (delete first)", fname)
                        else:
                            self.create_reference_ppos(
                                creffilename_c, fname, cfun.get_ppos()
                            )
                            saved = True
                    else:
                        refppos = creffun.ppos
                        funppos = [ppo for ppo in ppos if ppo.cfun.name == fname]
                        if len(refppos) == len(funppos):
                            self.testresults.add_ppo_count_success(
                                creffilename_c, fname)
                            self.check_ppos(
                                creffilename_c, fname, funppos, refppos)
                        else:
                            self.testresults.add_ppo_count_error(
                                creffilename_c,
                                fname,
                                len(funppos),
                                len(refppos)
                            )
                            raise FunctionPPOError(creffilename_c + ":" + fname)
        except FunctionPPOError as detail:
            self.print_test_results()
            chklogger.logger.error("Function PPO error: %s", str(detail))
            exit()
        if self.saveref and saved:
            self.testsetref.save()
            exit()

    def check_spos(
            self,
            cfilename: str,
            cfun: str,
            spos: List["CFunctionPO"],
            refspos: List[TestSPORef]) -> None:
        """Check if spos created match reference spos."""

        d: Dict[str, List[str]] = {}
        # collect spos produced
        for spo in spos:
            context = str(spo.cfg_context)
            if context not in d:
                d[context] = []
            d[context].append(spo.predicate_name)

        # compare with reference spos
        for refspo in refspos:
            context = refspo.context
            if context not in d:
                p = refspo.predicate
                self.testresults.add_missing_spo(cfilename, cfun, context, p)
                for c in d:
                    if self.verbose:
                        print(str(c))
                raise FunctionSPOError(
                    cfilename
                    + ":"
                    + cfun
                    + ":"
                    + " Missing spo: "
                    + str(context)
                    + " ("
                    + str(d)
                    + ")"
                )
            else:
                p = refspo.predicate
                if p not in d[context]:
                    self.testresults.add_missing_spo(cfilename, cfun, context, p)
                    raise FunctionSPOError(
                        cfilename
                        + ":"
                        + cfun
                        + ":"
                        + str(context)
                        + ":"
                        + p
                        + str(d[context])
                    )

    def test_spos(self, delaytest: bool = False) -> None:
        """Run analysis and check if all expected spos are created."""

        try:
            for creffile in self.cref_files:
                self.testresults.set_spos()
                cfilename_c = creffile.name
                cfilename = cfilename_c[:-2]
                cfilefilename = UF.get_cfile_cfile(
                    self.targetpath, self.testname, None, cfilename)
                if not os.path.isfile(cfilefilename):
                    raise XmlFileNotFoundError(cfilefilename)
                capp = CApplication(
                    self.projectpath,
                    self.testname,
                    self.targetpath,
                    self.contractpath,
                    singlefile=True)
                capp.initialize_single_file(cfilename)
                cappfile = capp.get_cfile()
                capp.update_spos()
                capp.collect_post_assumes()
                spos = cappfile.get_spos()
                if delaytest:
                    continue
                for creffun in creffile.functions.values():
                    fname = creffun.name
                    if self.saveref:
                        if creffun.has_spos():
                            chklogger.logger.warning(
                                "Spos not created for %s in %s (delete first)",
                                fname, cfilename)
                        else:
                            self.create_reference_spos(
                                cfilename_c, fname, cappfile.get_fn_spos(fname))
                    else:
                        refspos = creffun.spos
                        funspos = [spo for spo in spos if spo.cfun.name == fname]
                        if funspos is None and len(refspos) == 0:
                            self.testresults.add_spo_count_success(
                                cfilename_c, fname)

                        elif len(refspos) == len(funspos):
                            self.testresults.add_spo_count_success(
                                cfilename_c, fname)
                            self.check_spos(cfilename_c, fname, funspos, refspos)
                        else:
                            self.testresults.add_spo_count_error(
                                cfilename_c, fname, len(funspos), len(refspos)
                            )
                            raise FunctionSPOError(
                                cfilename_c
                                + ":"
                                + fname
                                + " ("
                                + str(len(funspos))
                                + " spos found; expected: "
                                + str(len(refspos))
                                + ")"
                            )
        except FunctionSPOError as detail:
            self.print_test_results()
            print("")
            print("*" * 80)
            print("Function SPO error: " + str(detail))
            print("*" * 80)
            exit()
        if self.saveref:
            self.testsetref.save()
            exit()

    def check_ppo_proofs(
            self,
            cfilename: str,
            cfun: TestCFunctionRef,
            funppos: List["CFunctionPO"],
            refppos: List[TestPPORef]) -> None:
        """Check if ppo analysis results match the expected results."""

        d: Dict[str, Dict[str, str]] = {}
        fname = cfun.name
        # collect actual analysis results
        for ppo in funppos:
            context = ppo.context_strings
            if context not in d:
                d[context] = {}
            p = ppo.predicate_name
            if p in d[context]:
                raise FunctionPEVError(
                    cfilename
                    + ":"
                    + fname
                    + ":"
                    + str(context)
                    + ": "
                    + "multiple instances of "
                    + p
                )
            else:
                status = ppo.status
                if ppo.is_delegated:
                    status += ":delegated"
                d[context][p] = status

        # compare with reference results
        for refppo in refppos:
            context = refppo.context_string
            p = refppo.predicate
            if context not in d:
                raise FunctionPEVError(
                    cfilename + ":" + fname + ":" + str(context) + ": missing"
                )
            else:
                cfilename_c = cfilename + ".c"
                if refppo.status != d[context][p]:
                    self.testresults.add_pev_discrepancy(
                        cfilename_c, cfun, refppo, d[context][p]
                    )

    def test_ppo_proofs(self, delaytest: bool = False) -> None:
        """Run analysis and check if analysis results match expected results.

        Skip checking results if delaytest is true.
        """

        if not os.path.isfile(self.config.canalyzer):
            raise AnalyzerMissingError(self.config.canalyzer)

        self.testresults.set_pevs()
        for creffile in self.cref_files:
            cfilename_c = creffile.name
            cfilename = cfilename_c[:-2]
            cfilefilename = UF.get_cfile_cfile(
                self.targetpath,
                self.testname,
                None,
                cfilename)
            if not os.path.isfile(cfilefilename):
                raise XmlFileNotFoundError(cfilefilename)
            capp = CApplication(
                self.projectpath,
                self.testname,
                self.targetpath,
                singlefile=True,
                contractpath=self.contractpath
            )
            capp.initialize_single_file(cfilename)
            cfile = capp.get_cfile()
            # only generate invariants if required
            if creffile.has_domains():
                for d in creffile.domains:
                    am = AnalysisManager(capp, verbose=self.verbose)
                    am.generate_and_check_file(cfilename, d)
            cfile.reinitialize_tables()
            ppos = cfile.get_ppos()
            if delaytest:
                continue
            for cfun in creffile.functions.values():
                fname = cfun.name
                funppos = [ppo for ppo in ppos if ppo.cfun.name == fname]
                refppos = cfun.ppos
                self.check_ppo_proofs(cfilename, cfun, funppos, refppos)

    def check_spo_proofs(
            self,
            cfilename: str,
            cfun: TestCFunctionRef,
            funspos: List["CFunctionPO"],
            refspos: List[TestSPORef]) -> None:
        """Check if spo analysis results match the expected results."""

        d: Dict[str, Dict[str, str]] = {}
        fname = cfun.name
        for spo in funspos:
            context = str(spo.cfg_context)
            if context not in d:
                d[context] = {}
            p = spo.predicate_name
            if p in d[context]:
                raise FunctionSEVError(
                    cfilename
                    + ":"
                    + fname
                    + ":"
                    + str(context)
                    + ": "
                    + "multiple instances of "
                    + p
                )
            else:
                status = spo.status
                if spo.is_delegated:
                    status = status + ":delegated"
                d[context][p] = status
        for refspo in refspos:
            context = refspo.context
            p = refspo.predicate
            if context not in d:
                raise FunctionSEVError(
                    cfilename + ":" + fname + ":" + str(context) + ": missing"
                )
            else:
                if refspo.status != d[context][p]:
                    self.testresults.add_sev_discrepancy(
                        cfilename, cfun, refspo, d[context][p]
                    )

    def test_spo_proofs(self, delaytest: bool = False) -> None:
        """Run analysis and check analysis results against the expected results.

        Skip the checking if delaytest is True.
        """

        self.testresults.set_sevs()
        for creffile in self.cref_files:
            creffilename_c = creffile.name
            cfilename = creffilename_c[:-2]
            cfilefilename = UF.get_cfile_cfile(
                self.targetpath, self.testname, None, cfilename)
            if not os.path.isfile(cfilefilename):
                raise XmlFileNotFoundError(cfilefilename)
            capp = CApplication(
                self.projectpath,
                self.testname,
                self.targetpath,
                self.contractpath,
                singlefile=True)
            capp.initialize_single_file(cfilename)
            cappfile = capp.get_cfile()
            if creffile.has_domains():
                for d in creffile.domains:
                    am = AnalysisManager(capp, verbose=self.verbose)
                    am.generate_and_check_file(cfilename, d)
            cappfile.reinitialize_tables()
            spos = cappfile.get_spos()
            if delaytest:
                continue
            for cfun in creffile.functions.values():
                fname = cfun.name
                funspos = [spo for spo in spos if spo.cfun.name == fname]
                refspos = cfun.spos
                self.check_spo_proofs(creffilename_c, cfun, funspos, refspos)

    @property
    def cref_filenames(self) -> List[str]:
        return self.testsetref.cfilenames

    @property
    def cref_files(self) -> List[TestCFileRef]:
        return list(self.testsetref.cfiles.values())

    def get_cref_file(self, cfilename: str) -> Optional[TestCFileRef]:
        return self.testsetref.cfile(cfilename)

    def clean(self) -> None:
        self.parsemanager.remove_semantics()

    def xcfile_exists(self, cfilename: str) -> bool:
        """Checks existence of xml file for cfilename."""

        cfilename = cfilename[:-2]
        xcfile_name = UF.get_cfile_cfile(
            self.targetpath, self.testname, None, cfilename)
        return os.path.isfile(xcfile_name)

    def xffile_exists(self, cfilename: str, funname: str) -> bool:
        """Checks existence of xml file for function funname in cfilename."""

        cfilename = cfilename[:-2]
        xfilename = UF.get_cfun_filename(
            self.targetpath, self.testname, None, cfilename, funname)
        return os.path.isfile(xfilename)
