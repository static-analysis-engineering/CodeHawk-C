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

import xml.etree.ElementTree as ET

from typing import Any, Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication


class CGlobalContract(object):
    """Holds assumptions that transcend the file level.

    The global contract is held by two files at the top directory of
    the contractpath:
    - globaldefs.json:
      - directions to the linker about hidden data structures and hidden fields

    - globaldefs.xml:
      - assumptions relevant to the CodeHawk analyzer
      - library function summaries that override the standard library function
        summaries

    Examples:
      - abstraction of interfile data structures by hiding fields
      - abstraction of interfile data structures by complete hiding
    """

    def __init__(self, capp: "CApplication") -> None:
        self._capp = capp
        self._globalassumptions: Optional[List[str]] = None
        self._hiddenstructs: Optional[Dict[str, Any]] = None
        self._hiddenfields: Optional[Dict[str, Any]] = None

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def contractpath(self) -> str:
        return self.capp.contractpath

    @property
    def globalassumptions(self) -> List[str]:
        if self._globalassumptions is None:
            self._globalassumptions = []
            if UF.has_global_xml_contract(self.contractpath):
                chklogger.logger.info("Load globaldefs.xml contract file")
                globalxmlcontract = UF.get_global_xml_contract(
                    self.contractpath)
                if globalxmlcontract is not None:
                    xas = globalxmlcontract.find("global-assumptions")
                    if xas is not None:
                        for a in xas.findall("ga"):
                            xname = a.get("name")
                            if xname is not None:
                                self._globalassumptions.append(xname)
                            else:
                                raise UF.CHCError(
                                    "Global assumption without name")
        return self._globalassumptions

    @property
    def hiddenstructs(self) -> Dict[str, Any]:
        if self._hiddenstructs is None:
            if UF.has_global_contract(self.contractpath):
                chklogger.logger.info("Load globaldefs.json contract file")
                globalcontract = UF.get_global_contract(self.contractpath)
                if "hidden-structs" in globalcontract:
                    self._hiddenstructs = globalcontract["hidden-structs"]
                    if self._hiddenstructs is not None:
                        return self._hiddenstructs

        self._hiddenstructs = {}
        return self._hiddenstructs

    @property
    def hiddenfields(self) -> Dict[str, Any]:
        if self._hiddenfields is None:
            if UF.has_global_contract(self.contractpath):
                chklogger.logger.info("Load globaldefs.json contract file")
                globalcontract = UF.get_global_contract(self.contractpath)
                if "hidden-fields" in globalcontract:
                    self._hiddenfields = globalcontract["hidden-fields"]
                    if self._hiddenfields is not None:
                        return self._hiddenfields

        self._hiddenfields = {}
        return self._hiddenfields

    def is_hidden_struct(self, filename: str, compname: str) -> bool:
        return (
            filename in self.hiddenstructs
            and compname in self.hiddenstructs[filename]
        )

    def is_hidden_field(self, compname: str, fieldname: str) -> bool:
        return (
            compname in self.hiddenfields
            and fieldname in self.hiddenfields[compname]
        )

    def add_no_free(self) -> None:
        if "no-free" in self.globalassumptions:
            return
        self.globalassumptions.append("no-free")
        self.save_global_xml_contract()

    def save_global_xml_contract(self) -> None:
        cnode = ET.Element("global-definitions")
        anode = ET.Element("global-assumptions")
        for a in self.globalassumptions:
            gnode = ET.Element("ga")
            gnode.set("name", a)
            anode.append(gnode)
        cnode.append(anode)
        UF.save_global_xml_contract(self.contractpath, cnode)

    '''
    def _initialize(self) -> None:
        globalcontract: Optional[Dict[str, Any]] = None
        if UF.has_global_contract(self.contractpath):
            logging.info("Load globaldefs.json contract file")
            globalcontract = UF.get_global_contract(self.contractpath)
        if globalcontract is not None:
            if "hidden-structs" in globalcontract:
                self.hiddenstructs = globalcontract["hidden-structs"]
            if "hidden-fields" in globalcontract:
                self.hiddenfields = globalcontract["hidden-fields"]
        if UF.has_global_xml_contract(self.contractpath):
            logging.info("Load globaldefs.xml contract file")
            globalxmlcontract = UF.get_global_xml_contract(self.contractpath)
            if "global-assumptions" in globalxmlcontract:
                xas = globalxmlcontract.find("global-assumptions")
                if xas is not None:
                    for a in xas.findall("ga"):
                        self.globalassumptions.append(a.get("name"))
    '''
