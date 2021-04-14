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

from typing import cast, Callable, Dict, List, Optional, Tuple

import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
import chc.util.StringIndexedTable as SI

import chc.app.CAttributes as CA
import chc.app.CConstExp as CC
import chc.app.CExp as CE
import chc.app.CLHost as CH
import chc.app.CLval as CV
import chc.app.COffsetExp as CO
import chc.app.CTyp as CT
import chc.app.CTypsig as CS


attrparam_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CA.CAttrBase]
] = {
    "aint": lambda x: CA.CAttrInt(*x),
    "astr": lambda x: CA.CAttrStr(*x),
    "acons": lambda x: CA.CAttrCons(*x),
    "asizeof": lambda x: CA.CAttrSizeOf(*x),
    "asizeofe": lambda x: CA.CAttrSizeOfE(*x),
    "asizeofs": lambda x: CA.CAttrSizeOfS(*x),
    "aalignof": lambda x: CA.CAttrAlignOf(*x),
    "aalignofe": lambda x: CA.CAttrAlignOfE(*x),
    "aalignofs": lambda x: CA.CAttrAlignOfS(*x),
    "aunop": lambda x: CA.CAttrUnOp(*x),
    "abinop": lambda x: CA.CAttrBinOp(*x),
    "adot": lambda x: CA.CAttrDot(*x),
    "astar": lambda x: CA.CAttrStar(*x),
    "aaddrof": lambda x: CA.CAttrAddrOf(*x),
    "aindex": lambda x: CA.CAttrIndex(*x),
    "aquestion": lambda x: CA.CAttrQuestion(*x),
}

constant_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CC.CConstBase]
] = {
    "int": lambda x: CC.CConstInt(*x),
    "str": lambda x: CC.CConstStr(*x),
    "wstr": lambda x: CC.CConstWStr(*x),
    "chr": lambda x: CC.CConstChr(*x),
    "real": lambda x: CC.CConstReal(*x),
    "enum": lambda x: CC.CConstEnum(*x),
}

exp_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CE.CExpBase]
] = {
    "const": lambda x: CE.CExpConst(*x),
    "lval": lambda x: CE.CExpLval(*x),
    "sizeof": lambda x: CE.CExpSizeOf(*x),
    "sizeofe": lambda x: CE.CExpSizeOfE(*x),
    "sizeofstr": lambda x: CE.CExpSizeOfStr(*x),
    "alignof": lambda x: CE.CExpAlignOf(*x),
    "alignofe": lambda x: CE.CExpAlignOfE(*x),
    "unop": lambda x: CE.CExpUnOp(*x),
    "binop": lambda x: CE.CExpBinOp(*x),
    "question": lambda x: CE.CExpQuestion(*x),
    "caste": lambda x: CE.CExpCastE(*x),
    "addrof": lambda x: CE.CExpAddrOf(*x),
    "addroflabel": lambda x: CE.CExpAddrOfLabel(*x),
    "startof": lambda x: CE.CExpStartOf(*x),
    "fnapp": lambda x: CE.CExpFnApp(*x),
    "cnapp": lambda x: CE.CExpCnApp(*x),
}

lhost_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CH.CLHostBase]
] = {"var": lambda x: CH.CLHostVar(*x), "mem": lambda x: CH.CLHostMem(*x)}

offset_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CO.COffsetBase]
] = {
    "n": lambda x: CO.CNoOffset(*x),
    "f": lambda x: CO.CFieldOffset(*x),
    "i": lambda x: CO.CIndexOffset(*x),
}

typ_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CT.CTypBase]
] = {
    "tvoid": lambda x: CT.CTypVoid(*x),
    "tint": lambda x: CT.CTypInt(*x),
    "tfloat": lambda x: CT.CTypFloat(*x),
    "tnamed": lambda x: CT.CTypNamed(*x),
    "tcomp": lambda x: CT.CTypComp(*x),
    "tenum": lambda x: CT.CTypEnum(*x),
    "tbuiltin-va-list": lambda x: CT.CTypBuiltinVaargs(*x),
    "tbuiltinvaargs": lambda x: CT.CTypBuiltinVaargs(*x),
    "tptr": lambda x: CT.CTypPtr(*x),
    "tarray": lambda x: CT.CTypArray(*x),
    "tfun": lambda x: CT.CTypFun(*x),
}

typsig_constructors: Dict[
    str, Callable[[Tuple["CDictionary", int, List[str], List[int]]], CS.CTypsigTSBase]
] = {
    "tsarray": lambda x: CS.CTypsigArray(*x),
    "tsptr": lambda x: CS.CTypsigPtr(*x),
    "tscomp": lambda x: CS.CTypsigComp(*x),
    "tsfun": lambda x: CS.CTypsigFun(*x),
    "tsenum": lambda x: CS.CTypsigEnum(*x),
    "tsbase": lambda x: CS.CTypsigBase(*x),
}


class CDictionary(object):
    """Indexed types."""

    def __init__(self) -> None:
        self.attrparam_table: IT.IndexedTable[CA.CAttrBase] = IT.IndexedTable(
            "attrparam-table"
        )
        self.attribute_table: IT.IndexedTable[CA.CAttribute] = IT.IndexedTable(
            "attribute-table"
        )
        self.attributes_table: IT.IndexedTable[CA.CAttributes] = IT.IndexedTable(
            "attributes-table"
        )
        self.constant_table: IT.IndexedTable[CC.CConstBase] = IT.IndexedTable(
            "constant-table"
        )
        self.exp_table: IT.IndexedTable[CE.CExpBase] = IT.IndexedTable("exp-table")
        self.funarg_table: IT.IndexedTable[CT.CFunArg] = IT.IndexedTable("funarg-table")
        self.funargs_table: IT.IndexedTable[CT.CFunArgs] = IT.IndexedTable(
            "funargs-table"
        )
        self.lhost_table: IT.IndexedTable[CH.CLHostBase] = IT.IndexedTable(
            "lhost-table"
        )
        self.lval_table: IT.IndexedTable[CV.CLval] = IT.IndexedTable("lval-table")
        self.offset_table: IT.IndexedTable[CO.COffsetBase] = IT.IndexedTable(
            "offset-table"
        )
        self.typ_table: IT.IndexedTable[CT.CTypBase] = IT.IndexedTable("typ-table")
        self.typsig_table: IT.IndexedTable[CS.CTypsigTSBase] = IT.IndexedTable(
            "typsig-table"
        )
        self.typsiglist_table: IT.IndexedTable[CS.CTypsigList] = IT.IndexedTable(
            "typsiglist-table"
        )
        self.string_table = SI.StringIndexedTable("string-table")
        self.tables: List[Tuple[IT.IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
            (self.attrparam_table, self._read_xml_attrparam_table),
            (self.attribute_table, self._read_xml_attribute_table),
            (self.attributes_table, self._read_xml_attributes_table),
            (self.constant_table, self._read_xml_constant_table),
            (self.exp_table, self._read_xml_exp_table),
            (self.funarg_table, self._read_xml_funarg_table),
            (self.funargs_table, self._read_xml_funargs_table),
            (self.lhost_table, self._read_xml_lhost_table),
            (self.lval_table, self._read_xml_lval_table),
            (self.offset_table, self._read_xml_offset_table),
            (self.typ_table, self._read_xml_typ_table),
            (self.typsig_table, self._read_xml_typsig_table),
            (self.typsiglist_table, self._read_xml_typsiglist_table),
        ]
        self.string_tables: List[Tuple[IT.IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
            (self.string_table, self._read_xml_string_table)
        ]

    # --------------- Statistics ---------------------------------------------

    def get_stats(self) -> str:
        lines = []
        for (t, _) in self.tables + self.string_tables:
            if t.size() > 0:
                lines.append(t.name.ljust(25) + str(t.size()).rjust(4))
        return "\n".join(lines)

    def get_table(self, n: str) -> IT.IndexedTableSuperclass:
        return next(
            x[0]
            for x in (self.tables + self.string_tables)
            if x[0].name == (n + "-table")
        )

    # create a count distribution for the objects in the table with name tname
    # that satisfy the respective case predicates
    def get_distribution(self, tname, cases):
        table = self.get_table(tname)
        if table is None:
            print("No table found for " + tname)
            return {}
        result = {}
        for c in cases:
            result[c] = len([v for v in table.values() if cases[c](v)])
        return result

    # -------------- Retrieve items from dictionary tables -------------------

    def get_attrparam(self, ix: int) -> CA.CAttrBase:
        return self.attrparam_table.retrieve(ix)

    def get_attribute(self, ix: int) -> CA.CAttribute:
        return self.attribute_table.retrieve(ix)

    def get_attributes(self, ix: int) -> CA.CAttributes:
        return self.attributes_table.retrieve(ix)

    def get_constant(self, ix: int) -> CC.CConstBase:
        return self.constant_table.retrieve(ix)

    def get_funarg(self, ix: int) -> CT.CFunArg:
        return self.funarg_table.retrieve(ix)

    def get_funargs(self, ix: int) -> CT.CFunArgs:
        return self.funargs_table.retrieve(ix)

    def get_funargs_opt(self, ix: int) -> Optional[CT.CFunArgs]:
        return self.get_funargs(ix) if ix >= 0 else None

    def get_lhost(self, ix: int) -> CH.CLHostBase:
        return self.lhost_table.retrieve(ix)

    def get_lval(self, ix: int) -> CV.CLval:
        return self.lval_table.retrieve(ix)

    def get_offset(self, ix: int) -> CO.COffsetBase:
        return self.offset_table.retrieve(ix)

    def get_typ(self, ix: int) -> CT.CTypBase:
        return self.typ_table.retrieve(ix)

    def get_exp(self, ix: int) -> CE.CExpBase:
        return self.exp_table.retrieve(ix)

    def get_exp_opt(self, ix: int) -> Optional[CE.CExpBase]:
        return self.get_exp(ix) if ix >= 0 else None

    def get_typsig(self, ix: int) -> CS.CTypsigTSBase:
        return self.typsig_table.retrieve(ix)

    def get_typesig_list(self, ix: int) -> CS.CTypsigList:
        return self.typsiglist_table.retrieve(ix)

    def get_string(self, ix: int) -> str:
        return self.string_table.retrieve(ix)

    # --------Provide read_xml/write_xml service for semantics files ----------

    def read_xml_funargs(self, node: ET.Element, tag: str = "iargs") -> CT.CFunArgs:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_funargs(int(xml_value))
        else:
            raise Exception("xml node was missing the tag \"" + tag + "\"")

    def write_xml_exp(self, node, exp, tag="iexp"):
        node.set(tag, str(self.index_exp(exp)))

    def read_xml_exp(self, node: ET.Element, tag: str = "iexp") -> CE.CExpBase:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_exp(int(xml_value))
        else:
            raise Exception("xml node was missing the tag \"" + tag + "\"")

    def write_xml_exp_opt(self, node, exp, tag="iexp"):
        if exp is None:
            return
        self.write_xml_exp(node, exp)

    def read_xml_exp_opt(self, node, tag="iexp"):
        if tag in node.attrib:
            return self.get_exp_opt(int(node.get(tag)))
        else:
            return None

    # ----------------------- Initialize dictionary from file ----------------

    def initialize(self, xnode, force=False):
        if xnode is None:
            return
        for (t, f) in self.tables + self.string_tables:
            t.reset()
            f(xnode.find(t.name))

    # --------------- stubs, overridden in file/global dictionary -------------

    def index_compinfo_key(self, compinfo, _):
        return compinfo.get_ckey()

    def index_varinfo_vid(self, vid, _):
        return vid

    def convert_ckey(self, ckey, fid=-1):
        return ckey

    # -------------------- Index items by category ---------------------------

    def index_attrparam(self, a: CA.CAttrBase) -> int:
        if a.is_int():

            def f_int(index: int, key: Tuple[str, str]) -> CA.CAttrInt:
                return CA.CAttrInt(self, index, a.tags, a.args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_int)
        if a.is_str():

            def f_str(index: int, key: Tuple[str, str]) -> CA.CAttrStr:
                return CA.CAttrStr(self, index, a.tags, a.args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_str)
        if a.is_cons():
            args = [self.index_attrparam(p) for p in cast(CA.CAttrCons, a).get_params()]

            def f_cons(index: int, key: Tuple[str, str]) -> CA.CAttrCons:
                return CA.CAttrCons(self, index, a.tags, args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_cons)
        raise Exception("No case yet for attrparam \"" + str(a) + "\"")

    def index_attribute(self, a: CA.CAttribute) -> int:
        args = [self.index_attrparam(p) for p in a.get_params()]

        def f(index: int, key: Tuple[str, str]) -> CA.CAttribute:
            return CA.CAttribute(self, index, a.tags, args)

        return self.attribute_table.add(IT.get_key(a.tags, a.args), f)

    def index_attributes(self, aa: CA.CAttributes) -> int:
        args = [self.index_attribute(a) for a in aa.get_attributes()]

        def f(index: int, key: Tuple[str, str]) -> CA.CAttributes:
            return CA.CAttributes(self, index, aa.tags, args)

        return self.attributes_table.add(IT.get_key(aa.tags, aa.args), f)

    def index_constant(self, c: CC.CConstBase) -> int:  # TBF
        if c.is_int():

            def f_int(index: int, key: Tuple[str, str]) -> CC.CConstInt:
                return CC.CConstInt(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_int)
        if c.is_str():
            args = [self.index_string(cast(CC.CConstStr, c).get_string())]

            def f_str(index: int, key: Tuple[str, str]) -> CC.CConstStr:
                return CC.CConstStr(self, index, c.tags, args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_str)
        if c.is_chr():

            def f_chr(index: int, key: Tuple[str, str]) -> CC.CConstChr:
                return CC.CConstChr(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_chr)
        if c.is_real():

            def f_real(index: int, key: Tuple[str, str]) -> CC.CConstReal:
                return CC.CConstReal(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_real)
        raise Exception("No case yet for const \"" + str(c) + "\"")

    def mk_exp_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CE.CExpBase:
            return exp_constructors[tags[0]]((self, index, tags, args))

        return self.exp_table.add(IT.get_key(tags, args), f)

    def mk_constant_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CC.CConstBase:
            return constant_constructors[tags[0]]((self, index, tags, args))

        return self.constant_table.add(IT.get_key(tags, args), f)

    def mk_typ_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CT.CTypBase:
            return typ_constructors[tags[0]]((self, index, tags, args))

        return self.typ_table.add(IT.get_key(tags, args), f)

    def mk_lhost_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CH.CLHostBase:
            return lhost_constructors[tags[0]]((self, index, tags, args))

        return self.lhost_table.add(IT.get_key(tags, args), f)

    def mk_lval_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CV.CLval:
            return CV.CLval(self, index, tags, args)

        return self.lval_table.add(IT.get_key(tags, args), f)

    def varinfo_to_exp_index(self, vinfo):
        lhostix = self.mk_lhost_index(["var", vinfo.vname], [vinfo.get_real_vid()])
        offsetix = self.mk_offset_index(["n"], [])
        lvalix = self.mk_lval_index([], [lhostix, offsetix])
        return self.mk_exp_index(["lval"], [lvalix])

    def s_term_to_exp_index(self, t, subst={}, fid=-1):
        """Create exp index from interface s_term"""
        if t.is_return_value():
            if "return" in subst:
                return self.index_exp(subst["return"])
            else:
                raise Exception("Error in index_s_term: no return found")
        if t.is_num_constant():
            c = t.get_constant()
            ctags = ["int", str(c), "iint"]
            tags = ["const"]
            args = [self.mk_constant_index(ctags, [])]
            return self.mk_exp_index(tags, args)
        if t.is_arg_value():
            par = t.get_parameter()
            if par.is_global():
                gname = par.get_name()
                if gname in subst:
                    return self.index_exp(subst[gname])
                else:
                    raise Exception(
                        "Error in index_s_term: global variable " + gname + " not found"
                    )
        print("cdict missing:index_s_term: " + t.tags[0])
        exit(1)

    def s_term_bool_expr_to_exp_index(self, op, t1, t2, subst={}):
        """Create exp index from interface s_term expression"""
        typtags = ["tint", "ibool"]
        typix = self.mk_typ_index(typtags, [])
        tags = ["binop", op]
        args = [
            self.s_term_to_exp_index(t1, subst),
            self.s_term_to_exp_index(t2, subst),
            typix,
        ]
        return self.mk_exp_index(tags, args)

    def index_exp(self, e, subst={}, fid=-1):  # TBF
        if e.is_constant():
            args = [self.index_constant(e.get_constant())]

            def f(index, key):
                return CE.CExpConst(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_sizeof():
            args = [self.index_typ(e.get_type())]

            def f(index, key):
                return CE.CExpSizeOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_sizeofe():
            args = [self.index_exp(e.get_exp(), subst=subst, fid=fid)]

            def f(index, key):
                return CE.CExpSizeOfE(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_sizeofstr():
            args = [self.index_string(e.get_string())]

            def f(index, key):
                return CE.CExpSizeOfStr(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_unop():
            args = [
                self.index_exp(e.get_exp(), subst=subst, fid=fid),
                self.index_typ(e.get_type()),
            ]

            def f(index, key):
                return CE.CExpUnOp(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_binop():
            args = [
                self.index_exp(e.get_exp1(), subst=subst, fid=fid),
                self.index_exp(e.get_exp2(), subst=subst, fid=fid),
                self.index_typ(e.get_type()),
            ]

            def f(index, key):
                return CE.CExpBinOp(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_caste():
            args = [
                self.index_typ(e.get_type()),
                self.index_exp(e.get_exp(), subst=subst, fid=fid),
            ]

            def f(index, key):
                return CE.CExpCastE(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_addrof():
            args = [self.index_lval(e.get_lval(), subst=subst, fid=fid)]

            def f(index, key):
                return CE.CExpAddrOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_startof():
            args = [self.index_lval(e.get_lval(), subst=subst, fid=fid)]

            def f(index, key):
                return CE.CExpStartOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_lval():
            args = [self.index_lval(e.get_lval(), subst=subst, fid=fid)]

            def f(index, key):
                return CE.CExpLval(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        print("cdict:no case yet for exp " + str(e))
        exit(1)

    def index_funarg(self, funarg):
        tags = [funarg.get_name()]
        args = [self.index_typ(funarg.get_type())]

        def f(index, key):
            return CT.CFunArg(self, index, tags, args)

        return self.funarg_table.add(IT.get_key(tags, args), f)

    def index_funargs_opt(self, opt_funargs):
        if opt_funargs is None:
            return None
        tags = []
        args = [self.index_funarg(f) for f in opt_funargs.get_args()]

        def f(index, key):
            return CT.CFunArgs(self, index, tags, args)

        return self.funargs_table.add(IT.get_key(tags, args), f)

    def index_lhost(self, h, subst={}, fid=-1):
        if h.is_var():
            args = [self.index_varinfo_vid(h.get_vid(), fid)]

            def f(index, key):
                return CH.CLHostVar(self, index, h.tags, args)

            return self.lhost_table.add(IT.get_key(h.tags, args), f)
        if h.is_mem():
            args = [self.index_exp(h.get_exp(), subst=subst, fid=fid)]

            def f(index, key):
                return CH.CLHostMem(self, index, h.tags, args)

            return self.lhost_table.add(IT.get_key(h.tags, args), f)

    def index_lval(self, lval, subst={}, fid=-1):
        args = [
            self.index_lhost(lval.get_lhost(), subst=subst, fid=fid),
            self.index_offset(lval.get_offset()),
        ]

        def f(index, key):
            return CV.CLval(self, index, [], args)

        return self.lval_table.add(IT.get_key([], args), f)

    def mk_offset_index(self, tags, args):
        def f(index, key):
            return offset_constructors[tags[0]]((self, index, tags, args))

        return self.offset_table.add(IT.get_key(tags, args), f)

    def index_offset(self, o, fid=-1):
        if not o.has_offset():

            def f(index, key):
                return CO.CNoOffset(self, index, o.tags, o.args)

            return self.offset_table.add(IT.get_key(o.tags, o.args), f)
        if o.is_field():
            ckey = self.convert_ckey(o.get_ckey(), o.cd.cfile.index)
            args = [ckey, self.index_offset(o.get_offset(), fid)]

            def f(index, key):
                return CO.CFieldOffset(self, index, o.tags, args)

            return self.offset_table.add(IT.get_key(o.tags, args), f)
        if o.is_index():
            args = [
                self.index_exp(o.get_index_exp()),
                self.index_offset(o.get_offset(), fid),
            ]

            def f(index, key):
                return CO.CIndexOffset(self, index, o.tags, args)

            return self.offset_table.add(IT.get_key(o.tags, args), f)

    def mk_typ(self, tags, args):
        def f(index, key):
            return typ_constructors[tags[0]]((self, index, tags, args))

        return self.typ_table.add(IT.get_key(tags, args), f)

    def index_typ(self, t):  # TBF
        # omit attributes argument if there are no attributes
        def ia(attrs):
            return (
                []
                if len(attrs.get_attributes()) == 0
                else [self.index_attributes(attrs)]
            )

        if t.is_void():
            tags = ["tvoid"]
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypVoid(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_int():
            tags = ["tint", t.get_kind()]
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypInt(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_float():
            tags = ["tfloat", t.get_kind()]
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypFloat(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_pointer():
            tags = ["tptr"]
            args = [self.index_typ(t.get_pointedto_type())] + ia(t.get_attributes())

            def f(index, key):
                return CT.CTypPtr(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_named_type():
            tags = ["tnamed", t.get_name()]
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypNamed(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_comp():
            tags = ["tcomp"]
            ckey = self.index_compinfo_key(t.get_struct(), t.cd.cfile.index)
            args = [ckey] + ia(t.get_attributes())

            def f(index, key):
                return CT.CTypComp(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_enum():
            tags = t.tags
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypEnum(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_array():
            tags = ["tarray"]
            arraysize = (
                self.index_exp(t.get_array_size_expr())
                if t.has_array_size_expr()
                else (-1)
            )
            args = [self.index_typ(t.get_array_basetype()), arraysize] + ia(
                t.get_attributes()
            )

            def f(index, key):
                return CT.CTypArray(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_function():
            index_funargs_opt = self.index_funargs_opt(t.get_args())
            ixfunargs = -1 if index_funargs_opt is None else index_funargs_opt
            tags = ["tfun"]
            args = [
                self.index_typ(t.get_return_type()),
                ixfunargs,
                (1 if t.is_vararg() else 0),
            ] + ia(t.get_attributes())

            def f(index, key):
                return CT.CTypFun(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        elif t.is_builtin_vaargs():
            tags = ["tbuiltinvaargs"]
            args = ia(t.get_attributes())

            def f(index, key):
                return CT.CTypBuiltinVaargs(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f)
        else:
            print("cdict: no case yet for " + str(t))
            exit(1)

    def index_typsig(self, t):
        return None  # TBD

    def index_typsiglist(self, t):
        return None  # TBD

    def index_string(self, s: str) -> int:
        return self.string_table.add(s)

    def write_xml(self, node):
        def f(n, r):
            r.write_xml(n)

        for (t, _) in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
        for (t, _) in self.string_tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode)
            node.append(tnode)

    def __str__(self):
        lines = []
        for (t, _) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)

    def _read_xml_attrparam_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CA.CAttrBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return attrparam_constructors[tag](args)

        self.attrparam_table.read_xml(txnode, "n", get_value)

    def _read_xml_attribute_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CA.CAttribute:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CA.CAttribute(*args)

        self.attribute_table.read_xml(txnode, "n", get_value)

    def _read_xml_attributes_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CA.CAttributes:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CA.CAttributes(*args)

        self.attributes_table.read_xml(txnode, "n", get_value)

    def _read_xml_constant_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CC.CConstBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return constant_constructors[tag](args)

        self.constant_table.read_xml(txnode, "n", get_value)

    def _read_xml_exp_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CE.CExpBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return exp_constructors[tag](args)

        self.exp_table.read_xml(txnode, "n", get_value)

    def _read_xml_funarg_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CT.CFunArg:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CT.CFunArg(*args)

        self.funarg_table.read_xml(txnode, "n", get_value)

    def _read_xml_funargs_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CT.CFunArgs:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CT.CFunArgs(*args)

        self.funargs_table.read_xml(txnode, "n", get_value)

    def _read_xml_lhost_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CH.CLHostBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return lhost_constructors[tag](args)

        self.lhost_table.read_xml(txnode, "n", get_value)

    def _read_xml_lval_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CV.CLval:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CV.CLval(*args)

        self.lval_table.read_xml(txnode, "n", get_value)

    def _read_xml_offset_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CO.COffsetBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return offset_constructors[tag](args)

        self.offset_table.read_xml(txnode, "n", get_value)

    def _read_xml_typ_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CT.CTypBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return typ_constructors[tag](args)

        self.typ_table.read_xml(txnode, "n", get_value)

    def _read_xml_typsig_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CS.CTypsigTSBase:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return typsig_constructors[tag](args)

        self.typsig_table.read_xml(txnode, "n", get_value)

    def _read_xml_typsiglist_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CS.CTypsigList:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CS.CTypsigList(*args)

        self.typsiglist_table.read_xml(txnode, "n", get_value)

    def _read_xml_string_table(self, txnode: ET.Element) -> None:
        self.string_table.read_xml(txnode)
