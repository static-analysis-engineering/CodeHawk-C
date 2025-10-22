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
import chc.app.CTyp as CT
from chc.app.CVarInfo import CVarInfo

from chc.app.CVisitor import CVisitor


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
            self.ccode.write(";")
            self.ccode.newline()
            return str(self.ccode)

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
        self.ccode.write(";")
        self.ccode.newline()
        return str(self.ccode)

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

    def visit_attributes(self, a: CA.CAttributes) -> None:
        if a.length == 0:
            return
        if a.attributes[0].name in ["const", "pconst"]:
            self.ccode.write("const ")
        elif a.attributes[0].name == "volatile":
            self.ccode.write("volatile ")
        else:
            self.ccode.write("[[" + a.attributes[0].name + " not yet supported]]")

    def visit_constexp(self, e: CE.CExpConst) -> None:
        self.ccode.write(str(e))
