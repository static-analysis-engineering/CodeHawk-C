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

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionProofs import CFunctionProofs


class SituatedMsg:

    def __init__(self, cd: "CDictionary", xnode: ET.Element) -> None:
        self._cd = cd
        self._xnode = xnode

    @property
    def cd(self) -> "CDictionary":
        return self._cd

    @property
    def msg(self) -> str:
        result = self._xnode.get("t")
        if result is None:
            return self._xnode.get("txt", "?")
        else:
            return result

    @property
    def file(self) -> Optional[str]:
        xfile = self._xnode.get("file")
        if xfile is not None:
            return self.cd.get_string(int(xfile))
        return None

    @property
    def line(self) -> Optional[int]:
        xline = self._xnode.get("line")
        if xline is not None:
            return int(xline)
        return None

    @property
    def detail(self) -> Optional[str]:
        xdetail = self._xnode.get("detail")
        if xdetail is not None:
            return self.cd.get_string(int(xdetail))
        return None

    @property
    def is_situated(self) -> bool:
        return (
            self.file is not None
            and self.line is not None
            and self.detail is not None)

    def __str__(self) -> str:
        if self.is_situated:
            return self.msg + " (" + str(self.line) + ": " + str(self.detail) + ")"
        else:
            return self.msg


class CProofDiagnostic:

    def __init__(
            self, cproofs: "CFunctionProofs", xnode: Optional[ET.Element]
    ) -> None:
        self._cproofs = cproofs
        self._xnode = xnode
        self._invsmap: Optional[Dict[int, List[int]]] = None
        self._amsgs: Optional[Dict[int, List[SituatedMsg]]] = None
        self._kmsgs: Optional[Dict[str, List[str]]] = None
        self._msgs: Optional[List[SituatedMsg]] = None

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def cfun(self) -> "CFunction":
        return self.cproofs.cfun

    @property
    def cd(self) -> "CDictionary":
        return self.cfun.cdictionary

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
    def msgs(self) -> List[SituatedMsg]:
        """Returns general diagnostics pertaining to the proof obligation."""

        if self._msgs is None:
            self._msgs = []
            if self._xnode is not None:
                mnode = self._xnode.find("msgs")
                if mnode is not None:
                    self._msgs = [
                        SituatedMsg(self.cd, x) for x in mnode.findall("msg")]
        return self._msgs

    @property
    def argument_msgs(self) -> Dict[int, List[SituatedMsg]]:
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
                            msgs = [
                                SituatedMsg(self.cd, x) for x in n.findall("msg")]
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
            for msg in self.argument_msgs[arg]:
                tnode = ET.Element("msg")
                tnode.set("t", msg.msg)
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
        for msg in self.msgs:
            mnode = ET.Element("msg")
            mnode.set("t", msg.msg)
            mmnode.append(mnode)
        dnode.extend([inode, mmnode, aanode, kknode])

    def __str__(self) -> str:
        if len(self.msgs) == 0:
            return "no diagnostic messages"
        return "\n".join(str(m) for m in self.msgs)
