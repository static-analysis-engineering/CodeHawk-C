# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2025  Aarno Labs LLC
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


from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

import chc.app.CAttributes as CA
import chc.app.CExp as CE
import chc.app.CInstr as CI
import chc.app.CLHost as CH
import chc.app.CLval as CL
import chc.app.COffset as CO
import chc.app.CStmt as CS
import chc.app.CTyp as CT
from chc.app.CVarInfo import CVarInfo

if TYPE_CHECKING:
    from chc.app.CFileGlobals import CGCompTag, CGType, CGVarDef
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CFieldInfo import CFieldInfo
    from chc.app.CInitInfo import (
        CSingleInitInfo, CCompoundInitInfo, COffsetInitInfo)
    from chc.app.CLocation import CLocation
    from chc.app.CTypeInfo import CTypeInfo


class CVisitor(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def visit_location(self, loc: "CLocation") -> None:
        ...

    @abstractmethod
    def visit_cgtype(self, cgtype: "CGType") -> None:
        ...

    @abstractmethod
    def visit_cgcomptag(self, cgcomptag: "CGCompTag") -> None:
        ...

    @abstractmethod
    def visit_cgvardef(self, cgvardef: "CGVarDef") -> None:
        ...

    @abstractmethod
    def visit_typeinfo(self, typeinfo: "CTypeInfo") -> None:
        ...

    @abstractmethod
    def visit_compinfo(self, compinfo: "CCompInfo") -> None:
        ...

    @abstractmethod
    def visit_fieldinfo(self, fieldinfo: "CFieldInfo") -> None:
        ...

    @abstractmethod
    def visit_single_initinfo(self, initinfo: "CSingleInitInfo") -> None:
        ...

    @abstractmethod
    def visit_compound_initinfo(self, initinfo: "CCompoundInitInfo") -> None:
        ...

    @abstractmethod
    def visit_offset_initinfo(self, initinfo: "COffsetInitInfo") -> None:
        ...

    @abstractmethod
    def visit_block(self, cblock: CS.CBlock) -> None:
        ...

    @abstractmethod
    def visit_function_body(self, cbody: CS.CFunctionBody) -> None:
        ...

    @abstractmethod
    def visit_if_stmt(self, ifstmt: CS.CIfStmt) -> None:
        ...

    @abstractmethod
    def visit_loop_stmt(self, loopstmt: CS.CLoopStmt) -> None:
        ...

    @abstractmethod
    def visit_switch_stmt(self, switchstmt: CS.CSwitchStmt) -> None:
        ...

    @abstractmethod
    def visit_break_stmt(self, breakstmt: CS.CBreakStmt) -> None:
        ...

    @abstractmethod
    def visit_continue_stmt(self, continuestmt: CS.CContinueStmt) -> None:
        ...

    @abstractmethod
    def visit_goto_stmt(self, gotostmt: CS.CGotoStmt) -> None:
        ...

    @abstractmethod
    def visit_return_stmt(self, returnstmt: CS.CReturnStmt) -> None:
        ...

    @abstractmethod
    def visit_instrs_stmt(self, instrsstmt: CS.CInstrsStmt) -> None:
        ...

    @abstractmethod
    def visit_assign_instr(self, assigninstr: CI.CAssignInstr) -> None:
        ...

    @abstractmethod
    def visit_call_instr(self, callinstr: CI.CCallInstr) -> None:
        ...

    @abstractmethod
    def visit_asm_instr(self, asminstr: CI.CAsmInstr) -> None:
        ...

    @abstractmethod
    def visit_asm_output(self, asmoutput: CI.CAsmOutput) -> None:
        ...

    @abstractmethod
    def visit_asm_input(self, asminput: CI.CAsmInput) -> None:
        ...

    @abstractmethod
    def visit_voidtyp(self, ctyp: CT.CTypVoid) -> None:
        ...

    @abstractmethod
    def visit_inttyp(self, ctyp: CT.CTypInt) -> None:
        ...

    @abstractmethod
    def visit_floattyp(self, ctyp: CT.CTypFloat) -> None:
        ...

    @abstractmethod
    def visit_namedtyp(self, ctyp: CT.CTypNamed) -> None:
        ...

    @abstractmethod
    def visit_comptyp(self, ctyp: CT.CTypComp) -> None:
        ...

    @abstractmethod
    def visit_enumtyp(self, ctyp: CT.CTypEnum) -> None:
        ...

    @abstractmethod
    def visit_builtinvaargs(self, ctyp: CT.CTypBuiltinVaargs) -> None:
        ...

    @abstractmethod
    def visit_ptrtyp(self, ctyp: CT.CTypPtr) -> None:
        ...

    @abstractmethod
    def visit_arraytyp(self, ctyp: CT.CTypArray) -> None:
        ...

    @abstractmethod
    def visit_funtyp(self, ctyp: CT.CTypFun) -> None:
        ...

    @abstractmethod
    def visit_funarg(self, ctyp: CT.CFunArg) -> None:
        ...

    @abstractmethod
    def visit_funargs(self, ctyp: CT.CFunArgs) -> None:
        ...

    @abstractmethod
    def visit_lval(self, lval: CL.CLval) -> None:
        ...

    @abstractmethod
    def visit_lhostvar(self, lhostvar: CH.CLHostVar) -> None:
        ...

    @abstractmethod
    def visit_lhostmem(self, lhostmem: CH.CLHostMem) -> None:
        ...

    @abstractmethod
    def visit_nooffset(self, nooffset: CO.CNoOffset) -> None:
        ...

    @abstractmethod
    def visit_fieldoffset(self, fieldoffset: CO.CFieldOffset) -> None:
        ...

    @abstractmethod
    def visit_indexoffset(self, indexoffset: CO.CIndexOffset) -> None:
        ...

    @abstractmethod
    def visit_constexp(self, c: CE.CExpConst) -> None:
        ...

    @abstractmethod
    def visit_explval(self, lval: CE.CExpLval) -> None:
        ...

    @abstractmethod
    def visit_sizeof(self, sizeof: CE.CExpSizeOf) -> None:
        ...

    @abstractmethod
    def visit_sizeofe(self, sizeofe: CE.CExpSizeOfE) -> None:
        ...

    @abstractmethod
    def visit_size_of_str(self, sizeofstr: CE.CExpSizeOfStr) -> None:
        ...

    @abstractmethod
    def visit_alignof(self, alignof: CE.CExpAlignOf) -> None:
        ...

    @abstractmethod
    def visit_alignofe(self, alignofe: CE.CExpAlignOfE) -> None:
        ...

    @abstractmethod
    def visit_unop(self, unop: CE.CExpUnOp) -> None:
        ...

    @abstractmethod
    def visit_binop(self, binop: CE.CExpBinOp) -> None:
        ...

    @abstractmethod
    def visit_question(self, question: CE.CExpQuestion) -> None:
        ...

    @abstractmethod
    def visit_cast(self, ecast: CE.CExpCastE) -> None:
        ...

    @abstractmethod
    def visit_addrof(self, addrof: CE.CExpAddrOf) -> None:
        ...

    @abstractmethod
    def visit_addr_of_label(self, addroflabel: CE.CExpAddrOfLabel) -> None:
        ...

    @abstractmethod
    def visit_startof(self, startof: CE.CExpStartOf) -> None:
        ...

    @abstractmethod
    def visit_fn_app(self, fnapp: CE.CExpFnApp) -> None:
        ...

    @abstractmethod
    def visit_cn_app(self, cnapp: CE.CExpCnApp) -> None:
        ...

    @abstractmethod
    def visit_attributes(self, a: CA.CAttributes) -> None:
        ...

    @abstractmethod
    def visit_attribute(self, a: CA.CAttribute) -> None:
        ...

    @abstractmethod
    def visit_attr_int(self, a: CA.CAttrInt) -> None:
        ...

    @abstractmethod
    def visit_attr_str(self, a: CA.CAttrStr) -> None:
        ...

    @abstractmethod
    def visit_attr_cons(self, a: CA.CAttrCons) -> None:
        ...

    @abstractmethod
    def visit_attr_sizeof(self, a: CA.CAttrSizeOf) -> None:
        ...

    @abstractmethod
    def visit_attr_sizeofe(self, a: CA.CAttrSizeOfE) -> None:
        ...

    @abstractmethod
    def visit_attr_sizeofs(self, a: CA.CAttrSizeOfS) -> None:
        ...

    @abstractmethod
    def visit_attr_alignof(self, a: CA.CAttrAlignOf) -> None:
        ...

    @abstractmethod
    def visit_attr_alignofe(self, a: CA.CAttrAlignOfE) -> None:
        ...

    @abstractmethod
    def visit_attr_alignofs(self, a: CA.CAttrAlignOfS) -> None:
        ...

    @abstractmethod
    def visit_attr_unop(self, a: CA.CAttrUnOp) -> None:
        ...

    @abstractmethod
    def visit_attr_binop(self, a: CA.CAttrBinOp) -> None:
        ...

    @abstractmethod
    def visit_attr_dot(self, a: CA.CAttrDot) -> None:
        ...

    @abstractmethod
    def visit_attr_star(self, a: CA.CAttrStar) -> None:
        ...

    @abstractmethod
    def visit_attr_addrof(self, a: CA.CAttrAddrOf) -> None:
        ...

    @abstractmethod
    def visit_attr_index(self, a: CA.CAttrIndex) -> None:
        ...

    @abstractmethod
    def visit_attr_question(self, a: CA.CAttrQuestion) -> None:
        ...
