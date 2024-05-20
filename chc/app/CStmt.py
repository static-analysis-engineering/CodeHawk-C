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
"""Control flow element in a function."""

import xml.etree.ElementTree as ET

from typing import Callable, cast, Dict, List, Optional, TYPE_CHECKING

from chc.app.CInstr import (CInstr, CCallInstr, CAssignInstr, CAsmInstr)

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFunction import CFunction


stmt_constructors: Dict[str, Callable[["CStmt", ET.Element], "CStmt"]] = {
    "instr": lambda x, y: CInstrsStmt(x, y),
    "if": lambda x, y: CIfStmt(x, y),
    "loop": lambda x, y: CLoopStmt(x, y),
    "break": lambda x, y: CBreakStmt(x, y),
    "return": lambda x, y: CReturnStmt(x, y),
    "goto": lambda x, y: CGotoStmt(x, y),
    "switch": lambda x, y: CSwitchStmt(x, y),
    "continue": lambda x, y: CContinueStmt(x, y),
}


def get_statement(parent: "CStmt", xnode: ET.Element) -> "CStmt":
    """Return the appropriate kind of CStmt dependent on the stmt kind."""

    knode = xnode.find("skind")
    if knode is None:
        raise UF.CHCError("missing element `skind`")
    tag = knode.get("stag")
    if tag is None:
        raise UF.CHCError("missing attribute `stag`")
    if tag in stmt_constructors:
        return stmt_constructors[tag](parent, xnode)
    raise UF.CHCError("Unknown statement tag found: " + tag)


class CStmt:
    """Superclass of all control flow components in a function."""

    def __init__(self, parent: Optional["CStmt"], xnode: ET.Element) -> None:
        self._parent = parent
        self.xnode = xnode
        self._succs: Optional[List[int]] = None
        self._preds: Optional[List[int]] = None

    @property
    def parent(self) -> Optional["CStmt"]:
        return self._parent

    @property
    def cfun(self) -> "CFunction":
        if self.parent is not None:
            return self.parent.cfun
        else:
            raise UF.CHCError("Unable to chain back to function body")

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def cdictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def sid(self) -> int:
        xsid = self.xnode.get("sid")
        if xsid is not None:
            return int(xsid)
        else:
            raise UF.CHCError("sid missing from stmt")

    @property
    def xskind(self) -> ET.Element:
        xskind = self.xnode.find("skind")
        if xskind is not None:
            return xskind
        else:
            raise UF.CHCError("skind missing from stmt")

    @property
    def kind(self) -> str:
        xkind = self.xskind.get("stag")
        if xkind is not None:
            return xkind
        else:
            raise UF.CHCError("stag missing from stmt")

    @property
    def preds(self) -> List[int]:
        if self._preds is None:
            self._preds = []
            xpreds = self.xnode.find("preds")
            if xpreds is not None:
                xpreds_r = xpreds.get("r")
                if xpreds_r is not None:
                    self._preds = [int(x) for x in str(xpreds_r).split(",")]
        return self._preds

    @property
    def succs(self) -> List[int]:
        if self._succs is None:
            self._succs = []
            xsuccs = self.xnode.find("succs")
            if xsuccs is not None:
                xsuccs_r = xsuccs.get("r")
                if xsuccs_r is not None:
                    self._succs = [int(x) for x in str(xsuccs_r).split(",")]
        return self._succs

    @property
    def stmts(self) -> Dict[int, "CStmt"]:
        return {}

    def iter_stmts(self, f: Callable[["CStmt"], None]) -> None:
        for s in self.stmts.values():
            f(s)

    @property
    def is_instrs_stmt(self) -> bool:
        return False

    @property
    def is_if_stmt(self) -> bool:
        return False

    @property
    def is_block_stmt(self) -> bool:
        return False

    @property
    def is_function_body(self) -> bool:
        return False

    @property
    def block_count(self) -> int:
        return sum(s.block_count for s in self.stmts.values())

    @property
    def stmt_count(self) -> int:
        return sum(s.stmt_count for s in self.stmts.values()) + 1

    @property
    def instr_count(self) -> int:
        return sum(s.instr_count for s in self.stmts.values())

    @property
    def call_instrs(self) -> List["CCallInstr"]:
        return sum([s.call_instrs for s in self.stmts.values()], [])

    @property
    def strings(self) -> List[str]:
        return sum([s.strings for s in self.stmts.values()], [])

    def get_variable_uses(self, vid: int) -> int:
        return sum(s.get_variable_uses(vid) for s in self.stmts.values())

    def __str__(self) -> str:
        lines: List[str] = []
        predecessors = ",".join(str(p) for p in self.preds)
        successors = ",".join(str(s) for s in self.succs)
        lines.append(
            str(self.sid).rjust(4)
            + ": ["
            + predecessors
            + "] "
            + self.kind
            + " ["
            + successors
            + "]")
        for s in self.stmts.values():
            lines.append("  " + str(s))
        return "\n".join(lines)


class CBlock(CStmt):

    def __init__(self, parent: Optional["CStmt"], xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)
        self._stmts: Optional[Dict[int, "CStmt"]] = None

    @property
    def stmts(self) -> Dict[int, "CStmt"]:
        if self._stmts is None:
            self._stmts = {}
            bstmts = self.xnode.find("bstmts")
            if bstmts is not None:
                for s in bstmts.findall("stmt"):
                    stmt = get_statement(self, s)
                    self._stmts[stmt.sid] = stmt
            else:
                raise UF.CHCError("stmts element is missing from block element")
        return self._stmts

    @property
    def is_block_stmt(self) -> bool:
        return True

    @property
    def block_count(self) -> int:
        return sum(s.block_count for s in self.stmts.values()) + 1


class CFunctionBody(CBlock):

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        CBlock.__init__(self, None, xnode)
        self._cfun = cfun

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def is_function_body(self) -> bool:
        return self.parent is None



class CIfStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)
        self._stmts: Optional[Dict[int, "CStmt"]] = None

    @property
    def stmts(self) -> Dict[int, "CStmt"]:
        if self._stmts is None:
            self._stmts = {}
            xthen = self.xskind.find("thenblock")
            if xthen is not None:
                thenblock = CBlock(self, xthen)
                for s in thenblock.stmts.values():
                    self._stmts[s.sid] = s
            xelse = self.xskind.find("elseblock")
            if xelse is not None:
                elseblock = CBlock(self, xelse)
                for s in elseblock.stmts.values():
                    self._stmts[s.sid] = s
        return self._stmts

    @property
    def condition(self) -> "CExp":
        xiexp = self.xskind.get("iexp")
        if xiexp is not None:
            return self.cdictionary.get_exp(int(xiexp))
        else:
            raise UF.CHCError("iexp attribute is missing from if stmt")

    @property
    def strings(self) -> List[str]:
        result: List[str] = sum([s.strings for s in self.stmts.values()], [])
        return result + self.condition.get_strings()

    @property
    def is_if_stmt(self) -> bool:
        return True

    def get_variable_uses(self, vid: int) -> int:
        result: int = sum(s.get_variable_uses(vid) for s in self.stmts.values())
        return result + self.condition.get_variable_uses(vid)

    def __str__(self) -> str:
        return CStmt.__str__(self) + ": " + str(self.condition)


class CLoopStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)
        self._stmts: Optional[Dict[int, "CStmt"]] = None

    @property
    def stmts(self) -> Dict[int, "CStmt"]:
        if self._stmts is None:
            self._stmts = {}
            xblock = self.xskind.find("block")
            if xblock is not None:
                loopblock = CBlock(self, xblock)
                for s in loopblock.stmts.values():
                    self._stmts[s.sid] = s
            else:
                raise UF.CHCError("Loop stmt without nested block")
        return self._stmts


class CSwitchStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)
        self._stmts: Optional[Dict[int, "CStmt"]] = None

    @property
    def stmts(self) -> Dict[int, "CStmt"]:
        if self._stmts is None:
            self._stmts = {}
            sblock = self.xskind.find("block")
            if sblock is not None:
                switchblock = CBlock(self, sblock)
                for s in switchblock.stmts.values():
                    self._stmts[s.sid] = s
            else:
                raise UF.CHCError("Switch stmt without nested block")
        return self._stmts

                
class CBreakStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)


class CContinueStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)


class CGotoStmt(CStmt):

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)


class CReturnStmt(CStmt):
    """Function return."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)


class CInstrsStmt(CStmt):
    """Sequence of instructions without control flow."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CStmt.__init__(self, parent, xnode)
        self._instrs: Optional[List[CInstr]] = None

    @property
    def is_instrs_stmt(self) -> bool:
        return True

    @property
    def instrs(self) -> List[CInstr]:
        if self._instrs is None:
            self._instrs = []
            xinstrs = self.xskind.find("instrs")
            if xinstrs is None:
                raise UF.CHCError("Instr stmt is missing instrs element")
            for xinode in xinstrs.findall("instr"):
                xitag = xinode.get("itag")
                if xitag is None:
                    raise UF.CHCError("Instr stmt is missing itag attribute")
                if xitag == "call":
                    self._instrs.append(CCallInstr(self, xinode))
                elif xitag == "set":
                    self._instrs.append(CAssignInstr(self, xinode))
                elif xitag == "asm":
                    self._instrs.append(CAsmInstr(self, xinode))
                else:
                    raise UF.CHCError("unknown instruction tag: " + xitag)
        return self._instrs

    @property
    def call_instrs(self) -> List["CCallInstr"]:
        result: List["CCallInstr"] = []
        for i in self.instrs:
            if i.is_call:
                result.append(cast("CCallInstr", i))
        return result

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append(CStmt.__str__(self))
        for (n, instr) in enumerate(self.instrs):
            lines.append("  " + str(n).rjust(4) + ": " + str(instr))
        return "\n".join(lines)
