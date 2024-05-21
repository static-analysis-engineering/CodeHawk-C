# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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

from typing import Any, Dict, Iterable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from chc.cmdline.kendra.TestCFileRef import TestCFileRef
    from chc.cmdline.kendra.TestCFunctionRef import TestCFunctionRef
    from chc.cmdline.kendra.TestPPORef import TestPPORef
    from chc.cmdline.kendra.TestSPORef import TestSPORef
    from chc.cmdline.kendra.TestSetRef import TestSetRef


class TestResults(object):
    def __init__(self, testsetref: "TestSetRef") -> None:
        self._testsetref = testsetref  # TestSetRef
        self._parseresults: Dict[str, str] = {}
        self._xfileresults: Dict[str, Dict[str, Any]] = {}
        self._pporesults: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._pevresults: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._sporesults: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._sevresults: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._includes_parsing = False
        self._includes_ppos = False
        self._includes_pevs = False
        self._includes_spos = False
        self._includes_sevs = False
        self._initialize()

    @property
    def cfiles(self) -> Iterable["TestCFileRef"]:
        return self.testsetref.cfiles.values()

    @property
    def testsetref(self) -> "TestSetRef":
        return self._testsetref

    @property
    def parseresults(self) -> Dict[str, str]:
        return self._parseresults

    @property
    def xfileresults(self) -> Dict[str, Dict[str, Any]]:
        return self._xfileresults

    @property
    def pporesults(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self._pporesults

    @property
    def sporesults(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self._sporesults

    @property
    def pevresults(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self._pevresults

    @property
    def sevresults(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self._sevresults

    @property
    def includes_parsing(self) -> bool:
        return self._includes_parsing

    @property
    def includes_ppos(self) -> bool:
        return self._includes_ppos

    @property
    def includes_spos(self) -> bool:
        return self._includes_spos

    @property
    def includes_pevs(self) -> bool:
        return self._includes_pevs

    @property
    def includes_sevs(self) -> bool:
        return self._includes_sevs

    def set_parsing(self) -> None:
        self._includes_parsing = True

    def set_ppos(self) -> None:
        self._includes_ppos = True

    def set_pevs(self) -> None:
        self._includes_pevs = True

    def set_spos(self) -> None:
        self._includes_spos = True

    def set_sevs(self) -> None:
        self._includes_sevs = True

    def add_parse_error(self, cfilename: str, msg: str) -> None:
        self._parseresults[cfilename] = "error: " + msg

    def add_parse_success(self, cfilename: str) -> None:
        self._parseresults[cfilename] = "ok"

    def add_xcfile_error(self, cfilename: str) -> None:
        self._xfileresults[cfilename]["xcfile"] = "missing"

    def add_xcfile_success(self, cfilename: str) -> None:
        self._xfileresults[cfilename]["xcfile"] = "ok"

    def add_xffile_error(self, cfilename: str, cfun: str) -> None:
        self._xfileresults[cfilename]["xffiles"][cfun] = "missing"

    def add_xffile_success(self, cfilename: str, cfun: str) -> None:
        self._xfileresults[cfilename]["xffiles"][cfun] = "ok"

    def add_ppo_count_error(
            self, cfilename: str, cfun: str, lenppos: int, lenrefppos: int
    ) -> None:
        discrepancy: int = lenrefppos - lenppos
        if discrepancy > 0:
            msg: str = str(discrepancy) + " ppos are missing"
        else:
            msg = str(-discrepancy) + " additional ppos"

        self._pporesults[cfilename][cfun]["count"] = "error: " + msg

    def add_spo_count_error(
            self, cfilename: str, cfun: str, lenspos: int, lenrefspos: int
    ) -> None:
        discrepancy: int = lenrefspos - lenspos
        if discrepancy > 0:
            msg: str = str(discrepancy) + " spos are missing"
        else:
            msg = str(-discrepancy) + " additional spos"

        self._sporesults[cfilename][cfun]["count"] = "error: " + msg

    def add_ppo_count_success(self, cfilename: str, cfun: str) -> None:
        self._pporesults[cfilename][cfun]["count"] = "ok"

    def add_spo_count_success(self, cfilename: str, cfun: str) -> None:
        self._sporesults[cfilename][cfun]["count"] = "ok"

    def add_missing_ppo(
            self, cfilename: str, cfun: str, context: str, predicate: str
    ) -> None:
        self._pporesults[cfilename][cfun]["missingpredicates"].append(
            (context, predicate)
        )

    def add_missing_spo(
            self, cfilename: str, cfun: str, context: str, hashstr: str
    ) -> None:
        self._sporesults[cfilename][cfun]["missing"].append((context, hashstr))

    def add_pev_discrepancy(
            self,
            cfilename: str,
            cfun: "TestCFunctionRef",
            ppo: "TestPPORef",
            status: str) -> None:
        hasmultiple: bool = cfun.has_multiple(ppo.line, ppo.predicate)
        self._pevresults[cfilename][cfun.name]["discrepancies"].append(
            (ppo, status, hasmultiple)
        )

    def add_sev_discrepancy(
            self,
            cfilename: str,
            cfun: "TestCFunctionRef",
            spo: "TestSPORef",
            status: str) -> None:
        self._sevresults[cfilename][cfun.name]["discrepancies"].append(
            (spo, status, False)
        )

    def get_line_summary(self) -> str:
        name = os.path.basename(self.testsetref.specfilename)[:-5]
        parsing: str = ""
        ppogen: str = ""
        spogen: str = ""
        pporesult: str = ""
        sporesult: str = ""
        for cfile in self.cfiles:
            cfilename = cfile.name
            cfunctions = cfile.functions.values()
            parsingok: bool = True
            ppogenok: bool = True
            spogenok: bool = True
            pporesultok: bool = True
            sporesultok: bool = True
            if len(cfunctions) > 0:
                for cfun in cfunctions:
                    fname = cfun.name
                    if self.includes_parsing:
                        if self.xfileresults[cfilename]["xffiles"][fname] != "ok":
                            parsingok = False
                    if self.includes_ppos:
                        funresults = self.pporesults[cfilename][fname]
                        count: str = funresults["count"]
                        missing: List[str] = funresults["missingpredicates"]
                        if count != "ok" or len(missing) > 0:
                            ppogenok = False
                    if self.includes_spos:
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults["count"]
                        missing = funresults["missing"]
                        if count != "ok" or len(missing) > 0:
                            spogenok = False
                    if self.includes_pevs:
                        pevs = self.pevresults[cfilename][fname]["discrepancies"]
                        if len(pevs) > 0:
                            pporesultok = False
                    if self.includes_sevs:
                        sevs = self.sevresults[cfilename][fname]["discrepancies"]
                        if len(sevs) > 0:
                            sporesultok = False

                def pr(result: bool) -> str:
                    return "=" if result else "X"

                parsing += pr(parsingok)
                ppogen += pr(ppogenok)
                spogen += pr(spogenok)
                pporesult += pr(pporesultok)
                sporesult += pr(sporesultok)
        return (
            name.ljust(10)
            + "[  "
            + parsing.ljust(6)
            + ppogen.ljust(6)
            + spogen.ljust(6)
            + pporesult.ljust(6)
            + sporesult.ljust(6)
            + "]"
        )

    def get_summary(self) -> str:
        lines: List[str] = []
        header = (
            "File".ljust(10)
            + "Parsing".center(15)
            + "PPO Gen".center(15)
            + "SPO Gen".center(15)
            + "PPO Results".center(15)
            + "SPO Results".center(15)
        )
        lines.append(header)
        lines.append("-" * 85)
        for cfile in self.cfiles:
            cfilename = cfile.name
            cfunctions = cfile.functions.values()
            parsingok: str = ""
            pposok: str = "ok"
            sposok: str = ""
            pevsok: str = "ok"
            sevsok: str = ""
            if len(cfunctions) > 0:
                for cfun in cfunctions:
                    fname = cfun.name
                    if self.includes_parsing:
                        if self.xfileresults[cfilename]["xffiles"][fname] != "ok":
                            parsingok = "bad"
                    if self.includes_ppos:
                        funresults = self.pporesults[cfilename][fname]
                        count: str = funresults["count"]
                        missing: List[str] = funresults["missingpredicates"]
                        if count != "ok" or len(missing) > 0:
                            pposok = "bad"
                    if self.includes_spos:
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults["count"]
                        missing = funresults["missing"]
                        if count != "ok" or len(missing) > 0 or sposok == "bad":
                            sposok = "bad"
                        else:
                            sposok = "ok"
                    if self.includes_pevs:
                        pevs = self.pevresults[cfilename][fname]["discrepancies"]
                        if len(pevs) != 0 or pevsok == "bad":
                            pevsok = "bad"
                    if self.includes_sevs:
                        sevs = self.sevresults[cfilename][fname]["discrepancies"]
                        if len(sevs) != 0 or sevsok == "bad":
                            sevsok = "bad"
                        else:
                            sevsok = "ok"

            if self.includes_parsing:
                if self.parseresults[cfilename] != "ok":
                    parsingok = "bad"
                if self.xfileresults[cfilename]["xcfile"] != "ok":
                    parsingok = "bad"
                if parsingok != "bad":
                    parsingok = "ok"

            lines.append(
                cfilename.ljust(10)
                + parsingok.center(15)
                + pposok.center(15)
                + sposok.center(15)
                + pevsok.center(15)
                + sevsok.center(15)
            )
        return "\n".join(lines)

    def __str__(self) -> str:
        lines = []
        if self.includes_parsing:
            lines.append("\nCheck parsing results:\n" + ("-" * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append(" ")
                lines.append(cfilename)
                lines.append("  parse : " + self.parseresults[cfilename])
                lines.append("  xcfile: " + self.xfileresults[cfilename]["xcfile"])
                cfunctions = cfile.functions.values()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        lines.append(
                            "    "
                            + fname
                            + ": "
                            + self.xfileresults[cfilename]["xffiles"][fname]
                        )
        if self.includes_ppos:
            lines.append("\nCheck primary proof obligations:\n" + ("-" * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append("")
                lines.append(cfilename)
                cfunctions = cfile.functions.values()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        funresults = self.pporesults[cfilename][fname]
                        count: str = funresults["count"]
                        missing: List[str] = funresults["missingpredicates"]
                        if count == "ok" and len(missing) == 0:
                            lines.append("    " + fname + ": ok")
                        else:
                            lines.append("    " + fname)
                            if count != "ok":
                                lines.append("      count: " + count)
                        for (ctxt, p) in missing:
                            lines.append("        (" + str(ctxt) + ")" + ": " + p)

        if self.includes_spos:
            lines.append("\nCheck secondary proof obligations:\n" + ("-" * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append("")
                lines.append(cfilename)
                cfunctions = cfile.functions.values()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults["count"]
                        missing = funresults["missing"]
                        if count == "ok" and len(missing) == 0:
                            lines.append("    " + fname + ": ok")
                        else:
                            lines.append("    " + fname)
                            if count != "ok":
                                lines.append("     count: " + count)
                        for (ctxt, hashstr) in missing:
                            lines.append(
                                "      "
                                + str(ctxt)
                                + ": "
                                + str(hashstr))

        if self.includes_pevs:
            lines.append("\nCheck primary proof results:\n" + ("-" * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append("")
                lines.append(cfilename)
                cfunctions = cfile.functions.values()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        pevs = self.pevresults[cfilename][fname]["discrepancies"]
                        if len(pevs) == 0:
                            lines.append("    " + fname + ": ok")
                        else:
                            lines.append("    " + fname)
                            for (ppo, status, hasmultiple) in pevs:
                                ctxt = ppo.context_string if hasmultiple else ""
                                lines.append(
                                    "    "
                                    + str(ppo.line).rjust(4)
                                    + " "
                                    + ppo.predicate.ljust(20)
                                    + "  found:"
                                    + status.ljust(11)
                                    + "  expected:"
                                    + ppo.status.ljust(11)
                                    + "  "
                                    + ctxt
                                )

        if self.includes_sevs:
            lines.append("\nCheck secondary proof results:\n" + ("-" * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append("")
                lines.append(cfilename)
                cfunctions = cfile.functions.values()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        sevs = self.sevresults[cfilename][fname]["discrepancies"]
                        if len(sevs) == 0:
                            lines.append("    " + fname + ": ok")
                        else:
                            lines.append("    " + fname)
                            for (spo, status, hasmultiple) in sevs:
                                ctxt = (
                                    spo.cfg_context_string if hasmultiple else ""
                                )
                                lines.append(
                                    "    "
                                    + str(spo.line).rjust(4)
                                    + " "
                                    + spo.predicate.ljust(20)
                                    + "  found:"
                                    + status.ljust(11)
                                    + "  expected:"
                                    + spo.status.ljust(11)
                                    + "  "
                                    + ctxt
                                )
        return "\n".join(lines)

    def _initialize(self) -> None:
        for cfile in self.cfiles:
            f = cfile.name
            self._parseresults[f] = "none"
            self._xfileresults[f] = {}
            self._xfileresults[f]["xcfile"] = "none"
            self._xfileresults[f]["xffiles"] = {}
            self._pporesults[f] = {}
            self._pevresults[f] = {}
            self._sporesults[f] = {}
            self._sevresults[f] = {}
            for cfun in cfile.functions.values():
                ff = cfun.name
                self._pporesults[f][ff] = {}
                self._pporesults[f][ff]["count"] = "none"
                self._pporesults[f][ff]["missingpredicates"] = []
                self._pevresults[f][ff] = {}
                self._pevresults[f][ff]["discrepancies"] = []

                self._sporesults[f][ff] = {}
                self._sporesults[f][ff]["count"] = "none"
                self._sporesults[f][ff]["missing"] = []
                self._sevresults[f][ff] = {}
                self._sevresults[f][ff]["discrepancies"] = []
