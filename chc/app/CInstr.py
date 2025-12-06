# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2025 Aarno Labs LLC
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
"""C instruction (assignment, call, or inserted assembly code)."""

import xml.etree.ElementTree as ET

from typing import Callable, Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation
    from chc.app.CLval import CLval
    from chc.app.CStmt import CStmt
    from chc.app.CVisitor import CVisitor


class CInstr:
    """Base class for instructions."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        self._parent = parent
        self.xnode = xnode

    @property
    def parent(self) -> "CStmt":
        return self._parent

    @property
    def cfun(self) -> "CFunction":
        return self.parent.cfun

    @property
    def cdictionary(self) -> "CFileDictionary":
        return self.parent.cdictionary

    @property
    def location(self) -> "CLocation":
        return self.cfun.cfiledecls.read_xml_location(self.xnode)

    @property
    def is_assign(self) -> bool:
        return False

    @property
    def is_call(self) -> bool:
        return False

    @property
    def is_asm(self) -> bool:
        return False

    @property
    def strings(self) -> List[str]:
        return []

    def get_variable_uses(self, vid: int) -> int:
        return 0

    def accept(self, visitor: "CVisitor") -> None:
        raise UF.CHCError("visitor not yet accepted on: " + str(self))


class CCallInstr(CInstr):
    """Call instruction."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CInstr.__init__(self, parent, xnode)
        self._callee: Optional["CExp"] = None
        self._callargs: Optional[List["CExp"]] = None

    @property
    def is_call(self) -> bool:
        return True

    @property
    def lhs(self) -> Optional["CLval"]:
        xlval = self.xnode.get("ilval")
        if xlval is not None:
            return self.cdictionary.get_lval(int(xlval))
        else:
            return None

    @property
    def callee(self) -> "CExp":
        if self._callee is None:
            xexp = self.xnode.get("iexp")
            if xexp is not None:
                self._callee = self.cdictionary.get_exp(int(xexp))
            else:
                raise UF.CHCError("call instruction does not hava a callee")
        return self._callee

    @property
    def callargs(self) -> List["CExp"]:
        if self._callargs is None:
            self._callargs = []
            xargs = self.xnode.find("args")
            if xargs is None:
                raise UF.CHCError(
                    "Argument element missing from call instruction")
            for a in xargs.findall("exp"):
                xiexp = a.get("iexp")
                if xiexp is not None:
                    exp = self.cdictionary.get_exp(int(xiexp))
                    self._callargs.append(exp)
                else:
                    raise UF.CHCError(
                        "iexp attribute not found in call argument")
        return self._callargs

    @property
    def strings(self) -> List[str]:
        return sum([a.get_strings() for a in self.callargs], [])

    def has_lhs(self) -> bool:
        return "ilval" in self.xnode.attrib

    def get_variable_uses(self, vid: int) -> int:
        if self.lhs is not None:
            lhsuse = self.lhs.get_variable_uses(vid) if self.has_lhs() else 0
            arguse = sum([a.get_variable_uses(vid) for a in self.callargs])
            calleeuse = self.callee.get_variable_uses(vid)
            return lhsuse + arguse + calleeuse
        else:
            return 0

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_call_instr(self)

    def __str__(self) -> str:
        return "      call " + str(self.callee)


class CAssignInstr(CInstr):
    """Assignment instruction."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CInstr.__init__(self, parent, xnode)
        self._lhs: Optional["CLval"] = None
        self._rhs: Optional["CExp"] = None

    @property
    def is_assign(self) -> bool:
        return True

    @property
    def lhs(self) -> "CLval":
        if self._lhs is None:
            xlval = self.xnode.get("ilval")
            if xlval is not None:
                self._lhs = self.cdictionary.get_lval(int(xlval))
            else:
                raise UF.CHCError(
                    "Lhs attribute missing from assign instruction")
        return self._lhs

    @property
    def rhs(self) -> "CExp":
        if self._rhs is None:
            xexp = self.xnode.get("iexp")
            if xexp is not None:
                self._rhs = self.cdictionary.get_exp(int(xexp))
            else:
                raise UF.CHCError(
                    "Rhs attribute missing from assign instruction")
        return self._rhs

    @property
    def strings(self) -> List[str]:
        return self.rhs.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        lhsuse = self.lhs.get_variable_uses(vid)
        rhsuse = self.rhs.get_variable_uses(vid)
        return lhsuse + rhsuse

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_assign_instr(self)

    def __str__(self) -> str:
        return "     assign: " + str(self.lhs) + " := " + str(self.rhs)


class CAsmInstr(CInstr):
    """Instruction representing inserted assembly code."""

    def __init__(self, parent: "CStmt", xnode: ET.Element) -> None:
        CInstr.__init__(self, parent, xnode)
        self._asminputs: Optional[List["CAsmInput"]] = None
        self._asmoutputs: Optional[List["CAsmOutput"]] = None
        self._templates: Optional[List[str]] = None

    @property
    def is_asm(self) -> bool:
        return True

    @property
    def asminputs(self) -> List["CAsmInput"]:
        if self._asminputs is None:
            self._asminputs = []
            xinputs = self.xnode.find("asminputs")
            if xinputs is not None:
                for inode in xinputs.findall("asminput"):
                    self._asminputs.append(CAsmInput(self, inode))
        return self._asminputs

    @property
    def asmoutputs(self) -> List["CAsmOutput"]:
        if self._asmoutputs is None:
            self._asmoutputs = []
            xoutputs = self.xnode.find("asmoutputs")
            if xoutputs is not None:
                for inode in xoutputs.findall("asmoutput"):
                    self._asmoutputs.append(CAsmOutput(self, inode))
        return self._asmoutputs

    @property
    def templates(self) -> List[str]:
        if self._templates is None:
            self._templates = []
            xtemplate = self.xnode.find("templates")
            if xtemplate is not None:
                xindices = xtemplate.get("str-indices")
                if xindices is not None:
                    for s in xindices.split(","):
                        ts = self.cdictionary.get_string(int(s))
                        self._templates.append(ts)
        return self._templates

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_asm_instr(self)

    def __str__(self) -> str:
        lines: List[str] = []
        for s in self.templates:
            lines.append(s)
        for i in self.asminputs:
            lines.append("  " + str(i))
        for o in self.asmoutputs:
            lines.append("  " + str(o))
        return "\n".join(lines)


class CAsmOutput:

    def __init__(self, parent: CAsmInstr, xnode: ET.Element) -> None:
        self._parent = parent
        self.xnode = xnode
        self._lhs: Optional["CLval"] = None

    @property
    def parent(self) -> CAsmInstr:
        return self._parent

    @property
    def lhs(self) -> "CLval":
        if self._lhs is None:
            xlval = self.xnode.get("ilval")
            if xlval is not None:
                self._lhs = self.parent.cdictionary.get_lval(int(xlval))
            else:
                raise UF.CHCError("ilval attribute missing from asm output")
        return self._lhs

    @property
    def constraint(self) -> str:
        return self.xnode.get("constraint", "none")

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_asm_output(self)

    def __str__(self) -> str:
        return self.constraint + "; lval: " + str(self.lhs)


class CAsmInput:

    def __init__(self, parent: CAsmInstr, xnode: ET.Element) -> None:
        self._parent = parent
        self.xnode = xnode
        self._exp: Optional["CExp"] = None

    @property
    def parent(self) -> CAsmInstr:
        return self._parent

    @property
    def exp(self) -> "CExp":
        if self._exp is None:
            xexp = self.xnode.get("iexp")
            if xexp is not None:
                self._exp = self.parent.cdictionary.get_exp(int(xexp))
            else:
                raise UF.CHCError("iexp attribute missing from asm input")
        return self._exp

    @property
    def constraint(self) -> str:
        return self.xnode.get("constraint", "none")

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_asm_input(self)

    def __str__(self) -> str:
        return self.constraint + "; exp: " + str(self.exp)
