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

from typing import cast, List, Optional, TYPE_CHECKING

import chc.app.CAttributes as CA
import chc.app.CExp as CE
import chc.app.CInstr as CI
import chc.app.CLHost as CH
import chc.app.CLval as CL
import chc.app.COffset as CO
import chc.app.CStmt as CS
import chc.app.CTyp as CT
from chc.app.CVarInfo import CVarInfo

from chc.app.CVisitor import CVisitor

if TYPE_CHECKING:
    from chc.app.CFileGlobals import CGCompTag, CGType, CGVarDef
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CFieldInfo import CFieldInfo
    from chc.app.CFunction import CFunction
    from chc.app.CInitInfo import CSingleInitInfo, CCompoundInitInfo
    from chc.app.CLocation import CLocation
    from chc.app.CInitInfo import (
        CSingleInitInfo, CCompoundInitInfo, COffsetInitInfo)
    from chc.app.CTypeInfo import CTypeInfo


integernames = {
    "ichar": "char",
    "ischar": "signed char",
    "iuchar": "unsigned char",
    "ibool": "bool",
    "iint": "int",
    "iuint": "unsigned int",
    "ishort": "short",
    "iushort": "unsigned short",
    "ilong": "long",
    "iulong": "unsigned long",
    "ilonglong": "long long",
    "iulonglong": "unsigned long long",
}


operators = {
    "band": " & ",
    "bor": " | ",
    "bxor": " ^ ",
    "div": " / ",
    "eq": " == ",
    "ge": " >= ",
    "gt": " > ",
    "indexpi": " + ",
    "land": " && ",
    "le": " <= ",
    "lor": " || ",
    "lt": " < ",
    "minusa": " - ",
    "minuspi": " - ",
    "minuspp": " - ",
    "mod": " % ",
    "mult": " * ",
    "ne": " != ",
    "plusa": " + ",
    "pluspi": " + ",
    "shiftlt": " << ",
    "shiftrt": " >> "
}


floatnames = {"float": "float", "fdouble": "double", "flongdouble": "long double"}


class CPrettyCode:

    def __init__(self) -> None:
        self._outputlines: List[str] = []
        self._pos: int = 0

    @property
    def outputlines(self) -> List[str]:
        return self._outputlines

    @property
    def pos(self) -> int:
        return self._pos

    def newline(self, indent: int = 0) -> None:
        self._outputlines.append(" " * indent)
        self._pos = indent

    def write(self, s: str) -> None:
        self._outputlines[-1] += s
        self._pos += len(s)

    def __str__(self) -> str:
        return "\n".join(self.outputlines)


class CPrettyPrinter(CVisitor):

    def __init__(self, indentation: int = 2) -> None:
        self._indentation = indentation
        self._indent = 0
        self._ccode = CPrettyCode()

    def cgtypedef_str(self, gty: "CGType") -> str:
        gty.accept(self)
        return str(self.ccode)

    def cgcomptag_str(self, gcomp: "CGCompTag") -> str:
        gcomp.accept(self)
        return str(self.ccode)

    def cgvardef_str(self, gvardef: "CGVarDef") -> str:
        gvardef.accept(self)
        return str(self.ccode)

    def function_definition_to_string(self, cfun: "CFunction") -> str:
        self.write_function_signature(cfun.svar)
        self.ccode.write(" {")
        self.ccode.newline(indent=self.indent)
        self.increase_indent()
        if len(cfun.locals) > 0:
            self.write_function_locals(list(cfun.locals.values()))
            self.ccode.newline(indent=self.indent)
        cfun.sbody.accept(self)
        self.decrease_indent()
        self.ccode.newline(indent=self.indent)
        self.ccode.write("}")
        return str(self.ccode)

    @property
    def indentation(self) -> int:
        return self._indentation

    @property
    def indent(self) -> int:
        return self._indent

    @property
    def ccode(self) -> CPrettyCode:
        return self._ccode

    def increase_indent(self) -> None:
        self._indent += self.indentation

    def decrease_indent(self) -> None:
        self._indent -= self.indentation

    def visit_location(self, loc: "CLocation") -> None:
        self.ccode.newline(indent=0)
        self.ccode.write(f"// {loc.file}:{loc.line}:{loc.byte}")

    def visit_cgtype(self, cgtype: "CGType") -> None:
        cgtype.location.accept(self)
        cgtype.typeinfo.accept(self)

    def visit_cgcomptag(self, cgcomptag: "CGCompTag") -> None:
        cgcomptag.location.accept(self)
        self.ccode.newline(indent=0)
        if cgcomptag.is_struct:
            self.ccode.write(f"struct {cgcomptag.name}")
        else:
            self.ccode.write(f"union {cgcomptag.name}")
        self.ccode.write(" {")
        self.increase_indent()
        cgcomptag.compinfo.accept(self)
        self.decrease_indent()
        self.ccode.newline()
        self.ccode.write("}")

    def visit_cgvardef(self, cgvardef: "CGVarDef") -> None:
        cgvardef.location.accept(self)
        self.ccode.newline(indent=0)
        cgvardef.varinfo.vtype.accept(self)
        self.ccode.write(" ")
        self.ccode.write(cgvardef.vname)
        if cgvardef.initializer is not None:
            self.ccode.write(" = ")
            cgvardef.initializer.accept(self)

    def visit_typeinfo(self, typeinfo: "CTypeInfo") -> None:
        self.ccode.newline(indent=0)
        self.ccode.write("typedef ")
        typeinfo.type.accept(self)
        self.ccode.write(" ")
        self.ccode.write(typeinfo.name)
        self.ccode.write(";")

    def visit_compinfo(self, compinfo: "CCompInfo") -> None:
        for field in compinfo.fields:
            field.accept(self)

    def visit_fieldinfo(self, fieldinfo: "CFieldInfo") -> None:
        self.ccode.newline(indent=self.indent)
        fieldinfo.ftype.accept(self)
        self.ccode.write(f" {fieldinfo.fname};")

    def visit_single_initinfo(self, initinfo: "CSingleInitInfo") -> None:
        initinfo.exp.accept(self)

    def visit_compound_initinfo(self, initinfo: "CCompoundInitInfo") -> None:
        if initinfo.typ.is_struct or initinfo.typ.is_union:
            self.ccode.write("{")
        else:
            self.ccode.write("]")
        if len(initinfo.offset_initializers) > 0:
            for oi in initinfo.offset_initializers[:-1]:
                oi.accept(self)
                self.ccode.write(", ")
            initinfo.offset_initializers[-1].accept(self)
        if initinfo.typ.is_struct or initinfo.is_union:
            self.ccode.write("}")
        else:
            self.ccode.write("]")

    def visit_offset_initinfo(self, initinfo: "COffsetInitInfo") -> None:
        initinfo.offset.accept(self)
        self.ccode.write(" = ")
        initinfo.initializer.accept(self)

    def visit_voidtyp(self, t: CT.CTypVoid) -> None:
        t.attributes.accept(self)
        self.ccode.write("void")

    def visit_inttyp(self, t: CT.CTypInt) -> None:
        t.attributes.accept(self)
        self.ccode.write(integernames[t.ikind])

    def visit_floattyp(self, t: CT.CTypFloat) -> None:
        t.attributes.accept(self)
        self.ccode.write(str(t))

    def visit_namedtyp(self, t: CT.CTypNamed) -> None:
        t.attributes.accept(self)
        t.expand().accept(self)

    def visit_comptyp(self, t: CT.CTypComp) -> None:
        t.attributes.accept(self)
        if t.is_comp:
            self.ccode.write("struct " + self.de_anon_name(t.name))
        else:
            self.ccode.write("union " + self.de_anon_name(t.name))

    def de_anon_name(self, name: str) -> str:
        if name.startswith("__anonstruct_") and len(name) > 24:
            return name[13:-10] + "st"
        else:
            return name

    def visit_enumtyp(self, t: CT.CTypEnum) -> None:
        t.attributes.accept(self)
        self.ccode.write("enum " + t.name)

    def visit_builtinvaargs(self, t: CT.CTypBuiltinVaargs) -> None:
        pass

    def visit_ptrtyp(self, t: CT.CTypPtr) -> None:
        t.attributes.accept(self)
        t.pointedto_type.accept(self)
        self.ccode.write(" *")

    def visit_arraytyp(self, t: CT.CTypArray) -> None:
        t.array_basetype.accept(self)
        self.ccode.write("[")
        if t.array_size_expr is not None:
            # self.ccode.write("?")
            t.array_size_expr.accept(self)
        self.ccode.write("]")

    def visit_funtyp(self, t: CT.CTypFun) -> None:
        """Emits a function type without name."""

        t.return_type.accept(self)
        self.ccode.write(" (")
        if t.funargs is not None:
            t.funargs.accept(self)
        self.ccode.write(")")

    def write_chkx_srcloc_attribute(
            self, srcfile: str, line: int, binloc: Optional[str]) -> None:
        self.ccode.newline(indent=3)
        self.ccode.write("__attribute__ (( chkc_srcloc(")
        self.ccode.write('"')
        self.ccode.write(srcfile)
        self.ccode.write('"')
        self.ccode.write(",")
        self.ccode.write(str(line))
        self.ccode.write(")")
        if binloc is not None:
            self.ccode.write(", chkx_binloc(")
            self.ccode.write('"')
            self.ccode.write(binloc)
            self.ccode.write('"')
            self.ccode.write(")")
        self.ccode.write(" ))")

    def gvar_definition_str(
            self,
            vinfo: CVarInfo,
            srcloc: Optional[str] = None,
            binloc: Optional[str] = None) -> str:
        if vinfo.vtype.is_function:
            return "error"

        if vinfo.vtype.is_array:
            sizexps: List[Optional[CE.CExp]] = []
            self.ccode.newline()
            atype = cast(CT.CTypArray, vinfo.vtype)
            sizexps.append(atype.array_size_expr)
            basetype = atype.array_basetype
            while basetype.is_array:
                atype = cast(CT.CTypArray, basetype)
                sizexps.append(atype.array_size_expr)
                basetype = atype.array_basetype
            basetype.accept(self)
            self.ccode.write(" ")
            self.ccode.write(vinfo.vname)
            for s in sizexps:
                self.ccode.write("[")
                if s:
                    s.accept(self)
                self.ccode.write("]")
            self.ccode.write(";")
            self.ccode.newline()
            return str(self.ccode)

        self.ccode.newline()
        vinfo.vtype.accept(self)
        self.ccode.write(" ")
        self.ccode.write(vinfo.vname)
        if srcloc is not None:
            self.write_chkx_srcloc_attribute(srcloc, vinfo.line, binloc)
        self.ccode.write(";")
        self.ccode.newline()
        return str(self.ccode)

    def function_declaration_str(
            self,
            vinfo: CVarInfo,
            srcloc: Optional[str] = None,
            binloc: Optional[str] = None) -> str:
        if not vinfo.vtype.is_function:
            return "error"

        self.write_function_signature(vinfo, srcloc=srcloc, binloc=binloc)
        self.ccode.write(";")
        return str(self.ccode)

    def write_function_signature(
            self,
            vinfo: CVarInfo,
            srcloc: Optional[str] = None,
            binloc: Optional[str] = None) -> None:
        self.ccode.newline()
        ftype = cast(CT.CTypFun, vinfo.vtype)
        if ftype.return_type.is_function_pointer:
            returntyp = cast(CT.CTypPtr, ftype.return_type)
            retfntyp = cast(CT.CTypFun, returntyp.pointedto_type)
            retfntyp.return_type.accept(self)
            self.ccode.write(" (*")
            self.ccode.write(vinfo.vname)
            self.ccode.write("(")
            if ftype.funargs is not None:
                ftype.funargs.accept(self)
            self.ccode.write("))(")
            if retfntyp.funargs is not None:
                retfntyp.funargs.accept(self)
            self.ccode.write(")")
            if srcloc is not None:
                self.write_chkx_srcloc_attribute(srcloc, vinfo.line, binloc)
        else:
            ftype.return_type.accept(self)
            self.ccode.write(" ")
            self.ccode.write(vinfo.vname)
        self.ccode.write("(")
        if ftype.funargs is not None:
            ftype.funargs.accept(self)
        if ftype.is_vararg:
            self.ccode.write(", ...")
        self.ccode.write(")")
        if srcloc is not None:
            self.write_chkx_srcloc_attribute(srcloc, vinfo.line, binloc)

    def write_function_locals(self, vinfos: List["CVarInfo"]) -> None:
        for vinfo in vinfos:
            self.ccode.newline(indent=self.indent)
            vinfo.vtype.accept(self)
            self.ccode.write(" ")
            self.ccode.write(vinfo.vname)
            self.ccode.write(";")

    def funtypptr_with_name(self, t: CT.CTypFun, name: str) -> None:
        if t.return_type.is_function_pointer:
            returntyp = cast(CT.CTypPtr, t.return_type)
            retty = cast(CT.CTypFun, returntyp.pointedto_type)
            self.funtypptr_with_name(retty, name)
            self.ccode.write("(")
            if t.funargs is not None:
                t.funargs.accept(self)
            self.ccode.write(")")
        else:
            t.return_type.accept(self)
            self.ccode.write(" (*")
            self.ccode.write(name)
            self.ccode.write(")(")
            if t.funargs is not None:
                t.funargs.accept(self)
            self.ccode.write(")")

    def visit_funargs(self, funargs: CT.CFunArgs) -> None:
        args = funargs.arguments
        if len(args) == 0:
            self.ccode.write("void")
        else:
            for arg in args[:-1]:
                arg.accept(self)
                self.ccode.write(", ")
            args[-1].accept(self)

    def visit_funarg(self, funarg: CT.CFunArg) -> None:
        if funarg.typ.is_function_pointer:
            argtyp = cast(CT.CTypPtr, funarg.typ)
            fnptr = cast(CT.CTypFun, argtyp.pointedto_type)
            self.funtypptr_with_name(fnptr, funarg.name)
            return

        if funarg.typ.is_pointer:
            argtyp = cast(CT.CTypPtr, funarg.typ)
            ptargtyp = argtyp.pointedto_type
            if ptargtyp.is_named_type:
                ptx = cast(CT.CTypNamed, ptargtyp).expand()
                if ptx.is_function:
                    ptx = cast(CT.CTypFun, ptx)
                    self.funtypptr_with_name(ptx, funarg.name)
                    return

            # if (
            #        argtyp.attributes.length > 0
            #         and argtyp.attributes.attributes[0].name == "arraylen"):
            #    self.ptrarg_with_attribute_length(
            #        ptargtyp, argtyp.attributes.attributes[0], funarg.name)
            #    return

        funarg.typ.accept(self)
        self.ccode.write(" ")
        self.ccode.write(funarg.name)

    def ptrarg_with_attribute_length(
            self, t: CT.CTyp, a: CA.CAttribute, name: str) -> None:
        """retrieve arraylength from arraylen attribute.

        In C arrays passed as arguments to functions become pointers,
        that is, the function call:

        f(int a[20]);

        is compiled into

        f(int *a);

        It appears that CIL in this case records the length in an
        attribute with the name arraylen.
        """
        if not a.name == "arraylen":
            raise Exception("Not an arraylen attribute")
        if not (len(a.params) == 1):
            raise Exception("Expected one argument for arraylen")
        aparam = a.params[0]
        if not aparam.is_int:
            raise Exception("Expected an integer argument for arraylen")
        aparam = cast(CA.CAttrInt, aparam)

        t.accept(self)
        self.ccode.write(" ")
        self.ccode.write(name)
        self.ccode.write("[")
        self.ccode.write(str(aparam.intvalue))
        self.ccode.write("]")

    '''
    def visit_attributes(self, a: CA.CAttributes) -> None:
        if a.length == 0:
            return
        if a.attributes[0].name in ["const", "pconst"]:
            self.ccode.write("const ")
        elif a.attributes[0].name == "volatile":
            self.ccode.write("volatile ")
        else:
            self.ccode.write("[[" + a.attributes[0].name + " not yet supported]]")
    '''

    def visit_constexp(self, e: CE.CExpConst) -> None:
        self.ccode.write(str(e))

    def function_body_str(self, cbody: CS.CFunctionBody) -> str:
        self.ccode.newline()
        cbody.accept(self)
        return str(self.ccode)

    def visit_block(self, cblock: CS.CBlock) -> None:
        for stmt in cblock.stmts.values():
            stmt.accept(self)

    def visit_function_body(self, cbody: CS.CFunctionBody) -> None:
        for stmt in cbody.stmts.values():
            stmt.accept(self)

    def visit_if_stmt(self, ifstmt: CS.CIfStmt) -> None:
        self.ccode.newline(indent=self.indent)
        self.ccode.write("if (")
        ifstmt.condition.accept(self)
        self.ccode.write(") {")
        if ifstmt.ifstmt is not None:
            self.increase_indent()
            ifstmt.ifstmt.accept(self)
            self.decrease_indent()
            self.ccode.newline(indent=self.indent)
        if ifstmt.elsestmt is not None:
            self.ccode.write("} else {")
            self.increase_indent()
            ifstmt.elsestmt.accept(self)
            self.decrease_indent()
            self.ccode.newline(indent=self.indent)
        self.ccode.write("}")

    def visit_loop_stmt(self, loopstmt: CS.CLoopStmt) -> None:
        pass

    def visit_switch_stmt(self, switchstmt: CS.CSwitchStmt) -> None:
        pass

    def visit_break_stmt(self, breakstmt: CS.CBreakStmt) -> None:
        pass

    def visit_continue_stmt(self, continuestmt: CS.CContinueStmt) -> None:
        pass

    def visit_goto_stmt(self, gotostmt: CS.CGotoStmt) -> None:
        pass

    def visit_return_stmt(self, returnstmt: CS.CReturnStmt) -> None:
        returnstmt.location.accept(self)
        self.ccode.newline(indent=self.indent)
        if returnstmt.exp is not None:
            self.ccode.write("return ")
            returnstmt.exp.accept(self)
            self.ccode.write(";")
        else:
            self.ccode.write("return;")

    def visit_instrs_stmt(self, instrsstmt: CS.CInstrsStmt) -> None:
        for instr in instrsstmt.instrs:
            instr.accept(self)

    def visit_assign_instr(self, assigninstr: CI.CAssignInstr) -> None:
        self.ccode.newline(indent=self.indent)
        assigninstr.lhs.accept(self)
        self.ccode.write(" = ")
        assigninstr.rhs.accept(self)
        self.ccode.write(";")

    def visit_call_instr(self, callinstr: CI.CCallInstr) -> None:
        self.ccode.newline(indent=self.indent)
        if callinstr.lhs is not None:
            callinstr.lhs.accept(self)
            self.ccode.write(" = ")
        callinstr.callee.accept(self)
        self.ccode.write("(")
        if len(callinstr.callargs) > 0:
            for a in callinstr.callargs[:-1]:
                a.accept(self)
                self.ccode.write(", ")
            callinstr.callargs[-1].accept(self)
        self.ccode.write(");")

    def visit_asm_instr(self, asminstr: CI.CAsmInstr) -> None:
        pass

    def visit_asm_output(self, asmoutput: CI.CAsmOutput) -> None:
        pass

    def visit_asm_input(self, asminput: CI.CAsmInput) -> None:
        pass

    def visit_lval(self, lval: CL.CLval) -> None:
        lval.lhost.accept(self)
        lval.offset.accept(self)

    def visit_lhostvar(self, lhostvar: CH.CLHostVar) -> None:
        self.ccode.write(lhostvar.name)

    def visit_lhostmem(self, lhostmem: CH.CLHostMem) -> None:
        self.ccode.write("*(")
        lhostmem.exp.accept(self)
        self.ccode.write(")")

    def visit_nooffset(self, nooffset: CO.CNoOffset) -> None:
        pass

    def visit_fieldoffset(self, fieldoffset: CO.CFieldOffset) -> None:
        self.ccode.write(".")
        self.ccode.write(fieldoffset.fieldname)
        fieldoffset.offset.accept(self)

    def visit_indexoffset(self, indexoffset: CO.CIndexOffset) -> None:
        pass

    def visit_explval(self, explval: CE.CExpLval) -> None:
        explval.lval.accept(self)

    def visit_sizeof(self, sizeof: CE.CExpSizeOf) -> None:
        pass

    def visit_sizeofe(self, sizeofe: CE.CExpSizeOfE) -> None:
        pass

    def visit_size_of_str(self, sizeofstr: CE.CExpSizeOfStr) -> None:
        pass

    def visit_alignof(self, alignof: CE.CExpAlignOf) -> None:
        pass

    def visit_alignofe(self, alignofe: CE.CExpAlignOfE) -> None:
        pass

    def visit_unop(self, unop: CE.CExpUnOp) -> None:
        pass

    def visit_binop(self, binop: CE.CExpBinOp) -> None:
        self.ccode.write("(")
        binop.exp1.accept(self)
        self.ccode.write(operators[binop.op])
        binop.exp2.accept(self)
        self.ccode.write(")")

    def visit_question(self, question: CE.CExpQuestion) -> None:
        pass

    def visit_cast(self, ecast: CE.CExpCastE) -> None:
        self.ccode.write("(")
        ecast.typ.accept(self)
        self.ccode.write(")")
        ecast.exp.accept(self)

    def visit_addrof(self, addrof: CE.CExpAddrOf) -> None:
        if addrof.lval.is_var:
            self.ccode.write("&")
            addrof.lval.accept(self)
        else:
            self.ccode.write("&(")
            addrof.lval.accept(self)
            self.ccode.write(")")

    def visit_addr_of_label(self, addroflabel: CE.CExpAddrOfLabel) -> None:
        pass

    def visit_startof(self, startof: CE.CExpStartOf) -> None:
        pass

    def visit_fn_app(self, fnapp: CE.CExpFnApp) -> None:
        pass

    def visit_cn_app(self, cnapp: CE.CExpCnApp) -> None:
        pass

    def visit_attributes(self, a: CA.CAttributes) -> None:
        for attr in a.attributes:
            attr.accept(self)

    def visit_attribute(self, a: CA.CAttribute) -> None:
        if len(a.params) == 0:
            self.ccode.write(a.name)
            self.ccode.write(" ")
        else:
            self.ccode.write("attribute not yet supported " + str(a))

    def visit_attr_int(self, a: CA.CAttrInt) -> None:
        pass

    def visit_attr_str(self, a: CA.CAttrStr) -> None:
        pass

    def visit_attr_cons(self, a: CA.CAttrCons) -> None:
        pass

    def visit_attr_sizeof(self, a: CA.CAttrSizeOf) -> None:
        pass

    def visit_attr_sizeofe(self, a: CA.CAttrSizeOfE) -> None:
        pass

    def visit_attr_sizeofs(self, a: CA.CAttrSizeOfS) -> None:
        pass

    def visit_attr_alignof(self, a: CA.CAttrAlignOf) -> None:
        pass

    def visit_attr_alignofe(self, a: CA.CAttrAlignOfE) -> None:
        pass

    def visit_attr_alignofs(self, a: CA.CAttrAlignOfS) -> None:
        pass

    def visit_attr_unop(self, a: CA.CAttrUnOp) -> None:
        pass

    def visit_attr_binop(self, a: CA.CAttrBinOp) -> None:
        pass

    def visit_attr_dot(self, a: CA.CAttrDot) -> None:
        pass

    def visit_attr_star(self, a: CA.CAttrStar) -> None:
        pass

    def visit_attr_addrof(self, a: CA.CAttrAddrOf) -> None:
        pass

    def visit_attr_index(self, a: CA.CAttrIndex) -> None:
        pass

    def visit_attr_question(self, a: CA.CAttrQuestion) -> None:
        pass
