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
"""Diagnostic messages related to an open proof obligation."""

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, TYPE_CHECKING


class CProofDiagnostic:

    def __init__(self, xnode: Optional[ET.Element]) -> None:
        self._xnode = xnode
        self._invsmap: Optional[Dict[int, List[int]]] = None
        self._amsgs: Optional[Dict[int, List[str]]] = None
        self._kmsgs: Optional[Dict[str, List[str]]] = None
        self._msgs: Optional[List[str]] = None

    @property
    def invsmap(self) -> Dict[int, List[int]]:
        """Returns a map from argument index to invariant indices.

        Note: argument index starts at 1.
        """

        if self._invsmap is None:
            self._invsmap = {}
            if self._xnode is not None:
                inode = self._xnode.find("invs")
                if inode is not None:
                    for n in inode.findall("arg"):
                        xargindex = n.get("a")
                        xarginvs = n.get("i")
                        if xargindex is not None and xarginvs is not None:
                            self._invsmap[int(xargindex)] = [
                                int(x) for x in xarginvs.split(",")]
        return self._invsmap

    @property
    def msgs(self) -> List[str]:
        """Returns general diagnostics pertaining to the proof obligation."""

        if self._msgs is None:
            self._msgs = []
            if self._xnode is not None:
                mnode = self._xnode.find("msgs")
                if mnode is not None:
                    self._msgs = [x.get("t", "") for x in mnode.findall("msg")]
        return self._msgs

    @property
    def argument_msgs(self) -> Dict[int, List[str]]:
        """Returns argument-specific diagnostic messages.

        Note: argument index starts at 1.
        """

        if self._amsgs is None:
            self._amsgs = {}
            if self._xnode is not None:
                anode = self._xnode.find("amsgs")
                if anode is not None:
                    for n in anode.findall("arg"):
                        xargindex = n.get("a")
                        if xargindex is not None:
                            msgs = [x.get("t", "") for x in n.findall("msg")]
                            self._amsgs[int(xargindex)] = msgs
        return self._amsgs

    @property
    def keyword_msgs(self) -> Dict[str, List[str]]:
        """Returns diagnostics with a known keyword (e.g., a domain name)."""

        if self._kmsgs is None:
            self._kmsgs = {}
            if self._xnode is not None:
                knode = self._xnode.find("kmsgs")
                if knode is not None:
                    for n in knode.findall("key"):
                        xkey = n.get("k")
                        if xkey is not None:
                            msgs = [x.get("t", "") for x in n.findall("msg")]
                            self._kmsgs[xkey] = msgs
        return self._kmsgs

    @property
    def argument_indices(self) -> List[int]:
        return list(self.invsmap.keys())

    def get_invariant_ids(self, index: int) -> List[int]:
        if index in self.invsmap:
            return self.invsmap[index]
        else:
            return []

    def write_xml(self, dnode: ET.Element) -> None:
        inode = ET.Element("invs")  # invariants
        mmnode = ET.Element("msgs")  # general messages
        aanode = ET.Element("amsgs")  # messages about individual arguments
        kknode = ET.Element("kmsgs")  # keyword messages
        for arg in self.invsmap:
            anode = ET.Element("arg")
            anode.set("a", str(arg))
            anode.set("i", ",".join([str(i) for i in self.invsmap[arg]]))
            inode.append(anode)
        for arg in self.argument_msgs:
            anode = ET.Element("arg")
            anode.set("a", str(arg))
            for t in self.argument_msgs[arg]:
                tnode = ET.Element("msg")
                tnode.set("t", t)
                anode.append(tnode)
            aanode.append(anode)
        for key in self.keyword_msgs:
            knode = ET.Element("key")
            knode.set("k", str(key))
            for t in self.keyword_msgs[key]:
                tnode = ET.Element("msg")
                tnode.set("t", t)
                knode.append(tnode)
            kknode.append(knode)
        for t in self.msgs:
            mnode = ET.Element("msg")
            mnode.set("t", t)
            mmnode.append(mnode)
        dnode.extend([inode, mmnode, aanode, kknode])

    def __str__(self) -> str:
        if len(self.msgs) == 0:
            return "no diagnostic messages"
        return "\n".join(self.msgs)
