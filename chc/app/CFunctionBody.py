# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
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

from typing import cast, Any, Callable, Dict, Iterable, List, Union, TYPE_CHECKING
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExpBase
    from chc.app.CLval import CLval
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation


stmt_constructors: Dict[str, Callable[["CBlock", ET.Element], "CStmt"]] = {
    "instr": lambda x, y: CInstrsStmt(x, y),
    "if": lambda x, y: CIfStmt(x, y),
    "loop": lambda x, y: CLoopStmt(x, y),
    "break": lambda x, y: CBreakStmt(x, y),
    "return": lambda x, y: CReturnStmt(x, y),
    "goto": lambda x, y: CGotoStmt(x, y),
    "switch": lambda x, y: CSwitchStmt(x, y),
    "continue": lambda x, y: CContinueStmt(x, y),
}


def get_statement(parent: "CBlock", xnode: ET.Element) -> "CStmt":
    """Return the appropriate kind of CStmt dependent on the stmt kind."""

    knode = xnode.find("skind")
    if knode is None:
        raise Exception("missing element `skind`")
    tag = knode.get("stag")
    if tag is None:
        raise Exception("missing attribute `stag`")
    if tag in stmt_constructors:
        return stmt_constructors[tag](parent, xnode)
    raise Exception("Unknown statement tag found: " + tag)


class CBlock(object):
    def __init__(self, parent: Union["CStmt", "CFunctionBody"], xnode: ET.Element) -> None:
        self.xnode = xnode  # CFunctionBody or CStmt
        self.cfun: "CFunction" = parent.cfun
        self.stmts: Dict[int, "CStmt"] = {}  # sid -> CStmt

    def iter_stmts(self, f: Callable[["CStmt"], None]) -> None:
        self._initialize_statements()
        for s in self.stmts.values():
            f(s)

    def get_statements(self) -> Iterable["CStmt"]:
        self._initialize_statements()
        return self.stmts.values()

    def get_block_count(self) -> int:
        return sum([stmt.get_block_count() for stmt in self.get_statements()])

    def get_stmt_count(self) -> int:
        return sum([stmt.get_stmt_count() for stmt in self.get_statements()])

    def get_instr_count(self) -> int:
        return sum([stmt.get_instr_count() for stmt in self.get_statements()])

    def get_call_instrs(self) -> List["CInstr"]:
        return sum([stmt.get_call_instrs() for stmt in self.get_statements()], [])

    def get_strings(self) -> List[str]:
        return sum([stmt.get_strings() for stmt in self.get_statements()], [])

    def get_variable_uses(self, vid: int) -> int:
        return sum([stmt.get_variable_uses(vid) for stmt in self.get_statements()])

    def _initialize_statements(self) -> None:
        if len(self.stmts) > 0:
            return
        bstmts = self.xnode.find("bstmts")
        if bstmts is None:
            raise Exception("Missing element `bstmts`")
        for s in bstmts.findall("stmt"):
            stmtid_xml = s.get("sid")
            if stmtid_xml is None:
                raise Exception("missing attribute `sid`")
            stmtid = int(stmtid_xml)
            self.stmts[stmtid] = get_statement(self, s)


class CFunctionBody(object):
    """Function implementation."""

    def __init__(self, cfun: "CFunction", xnode: ET.Element) -> None:
        self.cfun = cfun
        self.xnode = xnode
        self.block = CBlock(self, xnode)

    def iter_stmts(self, f: Callable[["CStmt"], None]) -> None:
        self.block.iter_stmts(f)

    def get_block_count(self) -> int:
        return self.block.get_block_count()

    def get_stmt_count(self) -> int:
        return self.block.get_stmt_count()

    def get_instr_count(self) -> int:
        return self.block.get_instr_count()

    def get_call_instrs(self) -> List["CInstr"]:
        return self.block.get_call_instrs()

    def get_strings(self) -> List[str]:
        return self.block.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.block.get_variable_uses(vid)

    def __str__(self) -> str:
        lines: List[str] = []

        def f(s: "CStmt") -> None:
            lines.append(str(s))

        self.iter_stmts(f)
        return "\n".join(lines)


class CStmt(object):
    """Function body statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        self.parentblock = parentblock  # containing block CBlock
        self.cfun = self.parentblock.cfun
        self.cdictionary: "CDictionary" = cast(Any, self.cfun).fdecls.dictionary
        self.xnode = xnode  # stmt element
        sid = self.xnode.get("sid")
        if sid is None:
            raise Exception("missing element `sid`")
        self.sid = int(sid)
        skind = self.xnode.find("skind")
        if skind is None:
            raise Exception("missing element `skind`")
        stag = skind.get("stag")
        if stag is None:
            raise Exception("missing attribute `stag`")
        self.kind = str(stag)
        self.succs: List[int] = []
        self.preds: List[int] = []
        self._initialize_stmt()

    def is_instrs_stmt(self) -> bool:
        return False

    def is_if_stmt(self) -> bool:
        return False

    def iter_stmts(self, f: Callable[["CStmt"], None]) -> None:
        pass

    def get_block_count(self) -> int:
        return 1

    def get_stmt_count(self) -> int:
        return 1

    def get_instr_count(self) -> int:
        return 0

    def get_call_instrs(self) -> List["CInstr"]:
        return []

    def get_strings(self) -> List[str]:
        return []

    def get_variable_uses(self, vid: int) -> int:
        return 0

    def _initialize_stmt(self) -> None:
        xpreds = self.xnode.find("preds")
        if xpreds is not None:
            xpreds_r = xpreds.get("r")
            if xpreds_r is not None:
                self.preds = [int(x) for x in str(xpreds_r).split(",")]
        xsuccs = self.xnode.find("succs")
        if xsuccs is not None:
            xsuccs_r = xsuccs.get("r")
            if xsuccs_r is not None:
                self.succs = [int(x) for x in str(xsuccs_r).split(",")]

    def __str__(self) -> str:
        lines: List[str] = []

        def f(s: "CStmt") -> None:
            lines.append("  " + str(s))

        predecessors = ",".join([str(p) for p in self.preds])
        successors = ",".join([str(p) for p in self.succs])
        lines.append(
            str(self.sid).rjust(4)
            + ": ["
            + predecessors
            + "] "
            + self.kind
            + " ["
            + successors
            + "]"
        )
        self.iter_stmts(f)
        return "\n".join(lines)


class CIfStmt(CStmt):
    """If statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)
        skind = self.xnode.find("skind")
        if skind is None:
            raise Exception("missing node `skind`")
        thenblock = skind.find("thenblock")
        if thenblock is None:
            raise Exception("missing node `thenblock`")
        self.thenblock = CBlock(self, thenblock)
        elseblock = skind.find("elseblock")
        if elseblock is None:
            raise Exception("missing node `elseblock`")
        self.elseblock = CBlock(self, elseblock)
        iexp = skind.get("iexp")
        if iexp is None:
            raise Exception("missing attribute `iexp`")
        self.condition = self.cdictionary.get_exp(int(iexp))
        iloc = skind.get("iloc")
        if iloc is None:
            raise Exception("missing attribute `iloc`")
        self.location: "CLocation" = cast(Any, self.cfun).fdecls.get_location(int(iloc))

    def iter_stmts(self, f: Callable[[CStmt], None]) -> None:
        self.thenblock.iter_stmts(f)
        self.elseblock.iter_stmts(f)

    def get_block_count(self) -> int:
        return self.thenblock.get_block_count() + self.elseblock.get_block_count()

    def get_stmt_count(self) -> int:
        return self.thenblock.get_stmt_count() + self.elseblock.get_stmt_count()

    def get_instr_count(self) -> int:
        return self.thenblock.get_instr_count() + self.elseblock.get_instr_count()

    def get_call_instrs(self) -> List["CInstr"]:
        return self.thenblock.get_call_instrs() + self.elseblock.get_call_instrs()

    def get_strings(self) -> List[str]:
        thenresult = self.thenblock.get_strings()
        elseresult = self.elseblock.get_strings()
        condresult = self.condition.get_strings()
        return thenresult + elseresult + condresult

    def get_variable_uses(self, vid: int) -> int:
        thenresult = self.thenblock.get_variable_uses(vid)
        elseresult = self.elseblock.get_variable_uses(vid)
        condresult = self.condition.get_variable_uses(vid)
        return thenresult + elseresult + condresult

    def is_if_stmt(self) -> bool:
        return True

    def __str__(self) -> str:
        return CStmt.__str__(self) + ": " + str(self.condition)


class CLoopStmt(CStmt):
    """Loop statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)
        skind = self.xnode.find("skind")
        if skind is None:
            raise Exception("missing element `skind`")
        block = skind.find("block")
        if block is None:
            raise Exception("missing element `block`")
        self.loopblock = CBlock(self, block)

    def iter_stmts(self, f: Callable[[CStmt], None]) -> None:
        self.loopblock.iter_stmts(f)

    def get_block_count(self) -> int:
        return self.loopblock.get_block_count()

    def get_instr_count(self) -> int:
        return self.loopblock.get_instr_count()

    def get_stmt_count(self) -> int:
        return self.loopblock.get_stmt_count()

    def get_call_instrs(self) -> List["CInstr"]:
        return self.loopblock.get_call_instrs()

    def get_strings(self) -> List[str]:
        return self.loopblock.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.loopblock.get_variable_uses(vid)


class CSwitchStmt(CStmt):
    """Switch statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)
        skind = self.xnode.find("skind")
        if skind is None:
            raise Exception("missing element `skind`")
        block = skind.find("block")
        if block is None:
            raise Exception("missing element `block`")
        self.switchblock = CBlock(self, block)

    def iter_stmts(self, f: Callable[[CStmt], None]) -> None:
        self.switchblock.iter_stmts(f)

    def get_block_count(self) -> int:
        return self.switchblock.get_block_count()

    def get_stmt_count(self) -> int:
        return self.switchblock.get_stmt_count()

    def get_instr_count(self) -> int:
        return self.switchblock.get_instr_count()

    def get_call_instrs(self) -> List["CInstr"]:
        return self.switchblock.get_call_instrs()

    def get_strings(self) -> List[str]:
        return self.switchblock.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.switchblock.get_variable_uses(vid)


class CBreakStmt(CStmt):
    """Break statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)


class CContinueStmt(CStmt):
    """Continue statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)


class CGotoStmt(CStmt):
    """Goto statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)


class CReturnStmt(CStmt):
    """Return statement."""

    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)


class CInstrsStmt(CStmt):
    def __init__(self, parentblock: CBlock, xnode: ET.Element) -> None:
        CStmt.__init__(self, parentblock, xnode)
        self.instrs: List[CInstr] = []
        self._initialize()

    def is_instrs_stmt(self) -> bool:
        return True

    def iter_instrs(self, f: Callable[["CInstr"], None]) -> None:
        for i in self.instrs:
            f(i)

    def get_instr_count(self) -> int:
        return len(self.instrs)

    def get_call_instrs(self) -> List["CInstr"]:
        return [i for i in self.instrs if i.is_call()]

    def get_strings(self) -> List[str]:
        return sum([i.get_strings() for i in self.instrs], [])

    def get_variable_uses(self, vid: int) -> int:
        return sum([i.get_variable_uses(vid) for i in self.instrs])

    def _initialize(self) -> None:
        skind = self.xnode.find("skind")
        if skind is None:
            raise Exception("missing element `skind`")
        instrs = self.xnode.find("instrs")
        if instrs is None:
            raise Exception("missing element `instrs`")
        for inode in instrs.findall("instr"):
            itag = inode.get("itag")
            if itag is None:
                raise Exception("missing attribute `itag`")
            elif itag == "call":
                self.instrs.append(CCallInstr(self, inode))
            elif itag == "set":
                self.instrs.append(CAssignInstr(self, inode))
            elif itag == "asm":
                self.instrs.append(CAsmInstr(self, inode))
            else:
                raise Exception("unknown itag \"" + str(itag) + "\"")

    def __str__(self) -> str:
        lines = []
        lines.append(CStmt.__str__(self))
        for (n, instr) in enumerate(self.instrs):
            lines.append("  " + str(n).rjust(4) + ": " + str(instr))
        return "\n".join(lines)


class CInstr(object):
    def __init__(self, parentstmt: CStmt, xnode: ET.Element) -> None:
        self.parentstmt = parentstmt
        self.xnode = xnode
        self.cfun = self.parentstmt.cfun

    def is_assign(self) -> bool:
        return False

    def is_call(self) -> bool:
        return False

    def is_asm(self) -> bool:
        return False

    def get_strings(self) -> List[str]:
        return []

    def get_variable_uses(self, vid: int) -> int:
        return 0


class CCallInstr(CInstr):
    def __init__(self, parentstmt: CStmt, xnode: ET.Element) -> None:
        CInstr.__init__(self, parentstmt, xnode)
        args = self.xnode.find("args")
        if args is None:
            raise Exception("missing element `args`")
        self.args = args.findall("exp")

    def is_call(self) -> bool:
        return True

    def get_lhs(self) -> "CLval":
        ilval = self.xnode.get("ilval")
        if ilval is None:
            raise Exception("missing attribute `ilval`")
        return self.parentstmt.cdictionary.get_lval(int(ilval))

    def get_callee(self) -> "CExpBase":
        iexp_xml = self.xnode.get("iexp")
        if iexp_xml is None:
            raise Exception("missing attribute `iexp`")
        return self.parentstmt.cdictionary.get_exp(int(iexp_xml))

    def get_arg_exprs(self) -> List["CExpBase"]:
        arg_exprs: List["CExpBase"] = []
        for a in self.args:
            iexp_xml = a.get("iexp")
            if iexp_xml is None:
                raise Exception("Missing attribute `iexp`")
            arg_exprs.append(self.parentstmt.cdictionary.get_exp(int(iexp_xml)))
        return arg_exprs

    def has_lhs(self) -> bool:
        return "ilval" in self.xnode.attrib

    def get_strings(self) -> List[str]:
        return sum([a.get_strings() for a in self.get_arg_exprs()], [])

    def get_variable_uses(self, vid: int) -> int:
        lhsuse = self.get_lhs().get_variable_uses(vid) if self.has_lhs() else 0
        arguse = sum([a.get_variable_uses(vid) for a in self.get_arg_exprs()])
        calleeuse = self.get_callee().get_variable_uses(vid)
        return lhsuse + arguse + calleeuse

    def to_dict(self) -> Dict[str, object]:
        result = {
            "base": "call",
            "callee": self.get_callee().to_idict(),
            "args": [e.to_idict() for e in self.get_arg_exprs()],
        }
        if self.has_lhs():
            result["lhs"] = self.get_lhs().to_idict()
        return result

    def __str__(self) -> str:
        return "      call " + str(self.get_callee())


class CAssignInstr(CInstr):
    def __init__(self, parentstmt: CStmt, xnode: ET.Element) -> None:
        CInstr.__init__(self, parentstmt, xnode)

    def is_assign(self) -> bool:
        return True

    def get_lhs(self) -> "CLval":
        ilval_xml = self.xnode.get("ilval")
        if ilval_xml is None:
            raise Exception("missing attribute `ilval`")
        return self.parentstmt.cdictionary.get_lval(int(ilval_xml))

    def get_rhs(self) -> "CExpBase":
        iexp_xml = self.xnode.get("iexp")
        if iexp_xml is None:
            raise Exception("missing attribute `iexp`")
        return self.parentstmt.cdictionary.get_exp(int(iexp_xml))

    def get_strings(self) -> List[str]:
        return self.get_rhs().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        lhsuse = self.get_lhs().get_variable_uses(vid)
        rhsuse = self.get_rhs().get_variable_uses(vid)
        return lhsuse + rhsuse

    def __str__(self) -> str:
        return "      assign: " + str(self.get_lhs()) + " := " + str(self.get_rhs())


class CAsmInstr(CInstr):
    def __init__(self, parentstmt: CStmt, xnode: ET.Element) -> None:
        CInstr.__init__(self, parentstmt, xnode)
        self.asminputs: List["CAsmInput"] = []
        self.asmoutputs: List["CAsmOutput"] = []
        self.templates: List[str] = []
        self._initialize()

    def is_asm(self) -> bool:
        return True

    def __str__(self) -> str:
        lines = []
        for s in self.templates:
            lines.append(str(s))
        for i in self.asminputs:
            lines.append("  " + str(i))
        for o in self.asmoutputs:
            lines.append("  " + str(o))
        return "\n".join(lines)

    def _initialize(self) -> None:
        xinputs = self.xnode.find("asminputs")
        if xinputs is not None:
            for inode in xinputs.findall("asminput"):
                self.asminputs.append(CAsmInput(self, inode))
        xoutputs = self.xnode.find("asmoutputs")
        if xoutputs is not None:
            for onode in xoutputs.findall("asmoutput"):
                self.asmoutputs.append(CAsmOutput(self, onode))
        xtemplates = self.xnode.find("templates")
        if xtemplates is not None:
            xml_indices = xtemplates.get("str-indices")
            if xml_indices is None:
                raise Exception("missing attribute `str-indices`")
            for s in str(xml_indices).split(","):
                self.templates.append(
                    self.cfun.cfile.declarations.dictionary.get_string(int(s))
                )


class CAsmOutput(object):
    def __init__(self, parentinstr: CAsmInstr, xnode: ET.Element) -> None:
        self.parentinstr = parentinstr
        self.xnode = xnode
        self.constraint = xnode.get("constraint", "none")
        ilval_xml = self.xnode.get("ilval")
        if ilval_xml is None:
            raise Exception("Missing attribute `ilval`")
        self.lval = self.parentinstr.cfun.cfile.declarations.dictionary.get_lval(int(ilval_xml))

    def __str__(self) -> str:
        return str(self.constraint) + ";  lval: " + str(self.lval)


class CAsmInput(object):
    def __init__(self, parentinstr: CAsmInstr, xnode: ET.Element) -> None:
        self.parentinstr = parentinstr
        self.xnode = xnode
        self.constraint = xnode.get("constraint", "none")
        iexp_xml = self.xnode.get("iexp")
        if iexp_xml is None:
            raise Exception("Missing attribute `iexp`")

        self.exp = self.parentinstr.cfun.cfile.declarations.dictionary.get_exp(int(iexp_xml))

    def __str__(self) -> str:
        return str(self.constraint) + "; exp: " + str(self.exp)
