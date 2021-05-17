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

from typing import cast, Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import xml.etree.ElementTree as ET
import chc.app.CDictionaryRecord as CD
import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

from chc.app.CAttributes import CAttrBase, CAttribute, CAttributes, CAttrInt, CAttrStr, CAttrCons
from chc.app.CConstExp import CConstBase, CConstInt, CConstStr, CConstChr, CConstReal
from chc.app.CExp import (
    CExpBase,
    CExpConst,
    CExpSizeOf,
    CExpSizeOfE,
    CExpSizeOfStr,
    CExpUnOp,
    CExpBinOp,
    CExpCastE,
    CExpAddrOf,
    CExpStartOf,
    CExpLval,
)
from chc.app.CLHost import CLHostBase, CLHostVar, CLHostMem
from chc.app.CLval import CLval
from chc.app.COffsetExp import COffsetBase, CNoOffset, CFieldOffset, CIndexOffset
from chc.app.CTyp import (
    CTypBase,
    CFunArg,
    CFunArgs,
    CTypVoid,
    CTypInt,
    CTypFloat,
    CTypComp,
    CTypEnum,
    CTypNamed,
    CTypArray,
    CTypPtr,
    CTypFun,
    CTypBuiltinVaargs,
)
from chc.app.CTypsig import CTypsigTSBase, CTypsigList
from chc.util.IndexedTable import IndexedTable, IndexedTableSuperclass, IndexedTableValue
from chc.util.StringIndexedTable import StringIndexedTable

if TYPE_CHECKING:
    from chc.api.STerm import STerm, STNumConstant, STArgValue
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CVarInfo import CVarInfo


class CDictionary(object):
    """Indexed types."""

    def __init__(self) -> None:
        self.attrparam_table: IndexedTable[CAttrBase] = IndexedTable("attrparam-table")
        self.attribute_table: IndexedTable[CAttribute] = IndexedTable("attribute-table")
        self.attributes_table: IndexedTable[CAttributes] = IndexedTable("attributes-table")
        self.constant_table: IndexedTable[CConstBase] = IndexedTable("constant-table")
        self.exp_table: IndexedTable[CExpBase] = IndexedTable("exp-table")
        self.funarg_table: IndexedTable[CFunArg] = IndexedTable("funarg-table")
        self.funargs_table: IndexedTable[CFunArgs] = IndexedTable("funargs-table")
        self.lhost_table: IndexedTable[CLHostBase] = IndexedTable("lhost-table")
        self.lval_table: IndexedTable[CLval] = IndexedTable("lval-table")
        self.offset_table: IndexedTable[COffsetBase] = IndexedTable("offset-table")
        self.typ_table: IndexedTable[CTypBase] = IndexedTable("typ-table")
        self.typsig_table: IndexedTable[CTypsigTSBase] = IndexedTable("typsig-table")
        self.typsiglist_table: IndexedTable[CTypsigList] = IndexedTable("typsiglist-table")
        self.string_table = StringIndexedTable("string-table")
        self.tables: List[Tuple[IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
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
        self.string_tables: List[Tuple[IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
            (self.string_table, self._read_xml_string_table)
        ]

    # --------------- Statistics ---------------------------------------------

    def get_stats(self) -> str:
        lines = []
        for (t, _) in self.tables + self.string_tables:
            if t.size() > 0:
                lines.append(t.name.ljust(25) + str(t.size()).rjust(4))
        return "\n".join(lines)

    def get_table(self, n: str) -> Optional[IndexedTableSuperclass]:
        return next(x[0] for x in (self.tables + self.string_tables) if x[0].name == (n + "-table"))

    # create a count distribution for the objects in the table with name tname
    # that satisfy the respective case predicates
    def get_distribution(
        self,
        tname: str,
        cases: Dict[str, Callable[[object], bool]],
    ) -> Dict[str, int]:
        table = cast(Optional[IndexedTable[IndexedTableValue]], self.get_table(tname))
        if table is None:
            raise Exception("No table found for " + tname)
        result = {}
        for c in cases:
            result[c] = len([v for v in table.values() if cases[c](v)])
        return result

    # -------------- Retrieve items from dictionary tables -------------------

    def get_attrparam(self, ix: int) -> CAttrBase:
        return self.attrparam_table.retrieve(ix)

    def get_attribute(self, ix: int) -> CAttribute:
        return self.attribute_table.retrieve(ix)

    def get_attributes(self, ix: int) -> CAttributes:
        return self.attributes_table.retrieve(ix)

    def get_constant(self, ix: int) -> CConstBase:
        return self.constant_table.retrieve(ix)

    def get_funarg(self, ix: int) -> CFunArg:
        return self.funarg_table.retrieve(ix)

    def get_funargs(self, ix: int) -> CFunArgs:
        return self.funargs_table.retrieve(ix)

    def get_funargs_opt(self, ix: int) -> Optional[CFunArgs]:
        return self.get_funargs(ix) if ix >= 0 else None

    def get_lhost(self, ix: int) -> CLHostBase:
        return self.lhost_table.retrieve(ix)

    def get_lval(self, ix: int) -> CLval:
        return self.lval_table.retrieve(ix)

    def get_offset(self, ix: int) -> COffsetBase:
        return self.offset_table.retrieve(ix)

    def get_typ(self, ix: int) -> CTypBase:
        return self.typ_table.retrieve(ix)

    def get_exp(self, ix: int) -> CExpBase:
        return self.exp_table.retrieve(ix)

    def get_exp_opt(self, ix: int) -> Optional[CExpBase]:
        return self.get_exp(ix) if ix >= 0 else None

    def get_typsig(self, ix: int) -> CTypsigTSBase:
        return self.typsig_table.retrieve(ix)

    def get_typesig_list(self, ix: int) -> CTypsigList:
        return self.typsiglist_table.retrieve(ix)

    def get_string(self, ix: int) -> str:
        return self.string_table.retrieve(ix)

    # --------Provide read_xml/write_xml service for semantics files ----------

    def read_xml_funargs(self, node: ET.Element, tag: str = "iargs") -> CFunArgs:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_funargs(int(xml_value))
        else:
            raise Exception('xml node was missing the tag "' + tag + '"')

    def write_xml_exp(self, node: ET.Element, exp: CExpBase, tag: str = "iexp") -> None:
        node.set(tag, str(self.index_exp(exp)))

    def read_xml_exp(self, node: ET.Element, tag: str = "iexp") -> CExpBase:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_exp(int(xml_value))
        else:
            raise Exception('xml node was missing the tag "' + tag + '"')

    def write_xml_exp_opt(
        self,
        node: ET.Element,
        exp: Optional[CExpBase],
        tag: str = "iexp",
    ) -> None:
        if exp is None:
            return
        self.write_xml_exp(node, exp)

    def read_xml_exp_opt(self, node: ET.Element, tag: str = "iexp") -> Optional[CExpBase]:
        xml_tag = node.get(tag)
        if xml_tag is None:
            return None
        else:
            return self.get_exp_opt(int(xml_tag))

    # ----------------------- Initialize dictionary from file ----------------

    def initialize(self, xnode, force=False):
        if xnode is None:
            return
        for (t, f) in self.tables + self.string_tables:
            t.reset()
            node = xnode.find(t.name)
            if node is None:
                raise Exception("Missing node `" + t.name + "`")
            f(node)

    # --------------- stubs, overridden in file/global dictionary -------------

    def index_compinfo_key(self, compinfo: "CCompInfo", _: object) -> int:
        return compinfo.get_ckey()

    def index_varinfo_vid(self, vid: int, _: object) -> int:
        return vid

    def convert_ckey(self, ckey: int, fid: int = -1) -> int:
        return ckey

    # -------------------- Index items by category ---------------------------

    def index_attrparam(self, a: CAttrBase) -> int:
        if a.is_int():

            def f_int(index: int, key: Tuple[str, str]) -> CAttrInt:
                return CAttrInt(self, index, a.tags, a.args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_int)
        if a.is_str():

            def f_str(index: int, key: Tuple[str, str]) -> CAttrStr:
                return CAttrStr(self, index, a.tags, a.args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_str)
        if a.is_cons():
            args = [self.index_attrparam(p) for p in cast(CAttrCons, a).get_params()]

            def f_cons(index: int, key: Tuple[str, str]) -> CAttrCons:
                return CAttrCons(self, index, a.tags, args)

            return self.attrparam_table.add(IT.get_key(a.tags, a.args), f_cons)
        raise Exception('No case yet for attrparam "' + str(a) + '"')

    def index_attribute(self, a: CAttribute) -> int:
        args = [self.index_attrparam(p) for p in a.get_params()]

        def f(index: int, key: Tuple[str, str]) -> CAttribute:
            return CAttribute(self, index, a.tags, args)

        return self.attribute_table.add(IT.get_key(a.tags, a.args), f)

    def index_attributes(self, aa: CAttributes) -> int:
        args = [self.index_attribute(a) for a in aa.get_attributes()]

        def f(index: int, key: Tuple[str, str]) -> CAttributes:
            return CAttributes(self, index, aa.tags, args)

        return self.attributes_table.add(IT.get_key(aa.tags, aa.args), f)

    def index_constant(self, c: CConstBase) -> int:  # TBF
        if c.is_int():

            def f_int(index: int, key: Tuple[str, str]) -> CConstInt:
                return CConstInt(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_int)
        if c.is_str():
            args = [self.index_string(cast(CConstStr, c).get_string())]

            def f_str(index: int, key: Tuple[str, str]) -> CConstStr:
                return CConstStr(self, index, c.tags, args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_str)
        if c.is_chr():

            def f_chr(index: int, key: Tuple[str, str]) -> CConstChr:
                return CConstChr(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_chr)
        if c.is_real():

            def f_real(index: int, key: Tuple[str, str]) -> CConstReal:
                return CConstReal(self, index, c.tags, c.args)

            return self.constant_table.add(IT.get_key(c.tags, c.args), f_real)
        raise Exception('No case yet for const "' + str(c) + '"')

    def mk_exp_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CExpBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, CExpBase)

        return self.exp_table.add(IT.get_key(tags, args), f)

    def mk_constant_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CConstBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, CConstBase)

        return self.constant_table.add(IT.get_key(tags, args), f)

    def mk_typ_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CTypBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, CTypBase)

        return self.typ_table.add(IT.get_key(tags, args), f)

    def mk_lhost_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CLHostBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, CLHostBase)

        return self.lhost_table.add(IT.get_key(tags, args), f)

    def mk_lval_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CLval:
            return CLval(self, index, tags, args)

        return self.lval_table.add(IT.get_key(tags, args), f)

    def varinfo_to_exp_index(self, vinfo: "CVarInfo") -> int:
        lhostix = self.mk_lhost_index(["var", vinfo.vname], [vinfo.get_real_vid()])
        offsetix = self.mk_offset_index(["n"], [])
        lvalix = self.mk_lval_index([], [lhostix, offsetix])
        return self.mk_exp_index(["lval"], [lvalix])

    def s_term_to_exp_index(self, t: "STerm", subst: Dict[Any, Any] = {}, fid: int = -1) -> int:
        """Create exp index from interface s_term"""
        if t.is_return_value():
            if "return" in subst:
                return self.index_exp(subst["return"])
            else:
                raise Exception("Error in index_s_term: no return found")
        if t.is_num_constant():
            c = cast("STNumConstant", t).get_constant()
            ctags = ["int", str(c), "iint"]
            tags = ["const"]
            args = [self.mk_constant_index(ctags, [])]
            return self.mk_exp_index(tags, args)
        if t.is_arg_value():
            par = cast("STArgValue", t).get_parameter()
            if par.is_global():
                gname = par.get_name()
                if gname in subst:
                    return self.index_exp(subst[gname])
                else:
                    raise Exception(
                        "Error in index_s_term: global variable " + gname + " not found"
                    )
        raise Exception("cdict missing:index_s_term: " + t.tags[0])

    def s_term_bool_expr_to_exp_index(
        self,
        op: str,
        t1: "STerm",
        t2: "STerm",
        subst: Dict[Any, Any] = {},
    ) -> int:
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

    def index_exp(self, e: CExpBase, subst: Dict[Any, Any] = {}, fid: int = -1) -> int:  # TBF
        if e.is_constant():
            args = [self.index_constant(cast(CExpConst, e).get_constant())]

            def f_cexpconst(index: int, key: object) -> CExpConst:
                return CExpConst(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpconst)
        if e.is_sizeof():
            args = [self.index_typ(cast(CExpSizeOf, e).get_type())]

            def f_cexpsizeof(index: int, key: object) -> CExpSizeOf:
                return CExpSizeOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpsizeof)
        if e.is_sizeofe():
            args = [self.index_exp(cast(CExpSizeOfE, e).get_exp(), subst=subst, fid=fid)]

            def f_cexpsizeofe(index: int, key: object) -> CExpSizeOfE:
                return CExpSizeOfE(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_sizeofstr():
            args = [self.index_string(cast(CExpSizeOfStr, e).get_string())]

            def f_cexpsizeofstr(index: int, key: object) -> CExpSizeOfStr:
                return CExpSizeOfStr(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpsizeofstr)
        if e.is_unop():
            args = [
                self.index_exp(cast(CExpUnOp, e).get_exp(), subst=subst, fid=fid),
                self.index_typ(cast(CExpUnOp, e).get_type()),
            ]

            def f_cexpunop(index: int, key: object) -> CExpUnOp:
                return CExpUnOp(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpunop)
        if e.is_binop():
            args = [
                self.index_exp(cast(CExpBinOp, e).get_exp1(), subst=subst, fid=fid),
                self.index_exp(cast(CExpBinOp, e).get_exp2(), subst=subst, fid=fid),
                self.index_typ(cast(CExpBinOp, e).get_type()),
            ]

            def f_cexpbinop(index: int, key: object) -> CExpBinOp:
                return CExpBinOp(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpbinop)
        if e.is_caste():
            args = [
                self.index_typ(cast(CExpCastE, e).get_type()),
                self.index_exp(cast(CExpCastE, e).get_exp(), subst=subst, fid=fid),
            ]

            def f(index: int, key: object) -> CExpCastE:
                return CExpCastE(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f)
        if e.is_addrof():
            args = [self.index_lval(cast(CExpAddrOf, e).get_lval(), subst=subst, fid=fid)]

            def f_cexpaddrof(index: int, key: object) -> CExpAddrOf:
                return CExpAddrOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpaddrof)
        if e.is_startof():
            args = [self.index_lval(cast(CExpStartOf, e).get_lval(), subst=subst, fid=fid)]

            def f_cexpstartof(index: int, key: object) -> CExpStartOf:
                return CExpStartOf(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexpstartof)
        if e.is_lval():
            args = [self.index_lval(cast(CExpLval, e).get_lval(), subst=subst, fid=fid)]

            def f_cexplval(index: int, key: object) -> CExpLval:
                return CExpLval(self, index, e.tags, args)

            return self.exp_table.add(IT.get_key(e.tags, args), f_cexplval)
        raise Exception("cdict:no case yet for exp " + str(e))

    def index_funarg(self, funarg: CFunArg) -> int:
        tags: List[str] = [funarg.get_name()]
        args: List[int] = [self.index_typ(funarg.get_type())]

        def f(index: int, key: Tuple[str, str]) -> CFunArg:
            return CFunArg(self, index, tags, args)

        return self.funarg_table.add(IT.get_key(tags, args), f)

    def index_funargs_opt(self, opt_funargs: Optional[CFunArgs]) -> Optional[int]:
        if opt_funargs is None:
            return None
        tags: List[str] = []
        args = [self.index_funarg(f) for f in opt_funargs.get_args()]

        def f(index: int, key: Tuple[str, str]) -> CFunArgs:
            return CFunArgs(self, index, tags, args)

        return self.funargs_table.add(IT.get_key(tags, args), f)

    def index_lhost(self, h: CLHostBase, subst: Dict[Any, Any] = {}, fid: int = -1) -> int:
        if h.is_var():
            args = [self.index_varinfo_vid(cast(CLHostVar, h).get_vid(), fid)]

            def f_clhostvar(index: int, key: object) -> CLHostVar:
                return CLHostVar(self, index, h.tags, args)

            return self.lhost_table.add(IT.get_key(h.tags, args), f_clhostvar)
        if h.is_mem():
            args = [self.index_exp(cast(CLHostMem, h).get_exp(), subst=subst, fid=fid)]

            def f(index: int, key: object) -> CLHostMem:
                return CLHostMem(self, index, h.tags, args)

            return self.lhost_table.add(IT.get_key(h.tags, args), f)
        raise Exception("Unknown type of lhost: \"" + str(h) + "\"")

    def index_lval(self, lval: CLval, subst: Dict[Any, Any] = {}, fid: int = -1) -> int:
        args = [
            self.index_lhost(lval.get_lhost(), subst=subst, fid=fid),
            self.index_offset(lval.get_offset()),
        ]

        def f(index: int, key: object) -> CLval:
            return CLval(self, index, [], args)

        return self.lval_table.add(IT.get_key([], args), f)

    def mk_offset_index(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> COffsetBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, COffsetBase)

        return self.offset_table.add(IT.get_key(tags, args), f)

    def index_offset(self, o: COffsetBase, fid: int = -1) -> int:
        if not o.has_offset():

            def f_no_offset(index: int, key: Tuple[str, str]) -> CNoOffset:
                return CNoOffset(self, index, o.tags, o.args)

            return self.offset_table.add(IT.get_key(o.tags, o.args), f_no_offset)
        if o.is_field():
            ckey = self.convert_ckey(cast(CFieldOffset, o).get_ckey(), cast(Any, o.cd).cfile.index)
            args = [ckey, self.index_offset(cast(CFieldOffset, o).get_offset(), fid)]

            def f_field(index: int, key: Tuple[str, str]) -> CFieldOffset:
                return CFieldOffset(self, index, o.tags, args)

            return self.offset_table.add(IT.get_key(o.tags, args), f_field)
        if o.is_index():
            args = [
                self.index_exp(cast(CIndexOffset, o).get_index_exp()),
                self.index_offset(cast(CIndexOffset, o).get_offset(), fid),
            ]

            def f_index(index: int, key: Tuple[str, str]) -> CIndexOffset:
                return CIndexOffset(self, index, o.tags, args)

            return self.offset_table.add(IT.get_key(o.tags, args), f_index)
        raise UF.CHError("cdict: no case yet for " + str(o))

    def mk_typ(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: Tuple[str, str]) -> CTypBase:
            return CD.construct_c_dictionary_record(self, index, tags, args, CTypBase)

        return self.typ_table.add(IT.get_key(tags, args), f)

    def index_typ(self, t: CTypBase) -> int:  # TBF
        # omit attributes argument if there are no attributes
        def ia(attrs: CAttributes) -> List[int]:
            return [] if len(attrs.get_attributes()) == 0 else [self.index_attributes(attrs)]

        if t.is_void():
            tags = ["tvoid"]
            args = ia(t.get_attributes())

            def f_void(index: int, key: Tuple[str, str]) -> CTypVoid:
                return CTypVoid(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_void)
        elif t.is_int():
            tags = ["tint", cast(CTypInt, t).get_kind()]
            args = ia(t.get_attributes())

            def f_int(index: int, key: Tuple[str, str]) -> CTypInt:
                return CTypInt(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_int)
        elif t.is_float():
            tags = ["tfloat", cast(CTypFloat, t).get_kind()]
            args = ia(t.get_attributes())

            def f_float(index: int, key: Tuple[str, str]) -> CTypFloat:
                return CTypFloat(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_float)
        elif t.is_pointer():
            tags = ["tptr"]
            args = [self.index_typ(cast(CTypPtr, t).get_pointedto_type())] + ia(t.get_attributes())

            def f_ptr(index: int, key: Tuple[str, str]) -> CTypPtr:
                return CTypPtr(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_ptr)
        elif t.is_named_type():
            tags = ["tnamed", cast(CTypNamed, t).get_name()]
            args = ia(t.get_attributes())

            def f_named(index: int, key: Tuple[str, str]) -> CTypNamed:
                return CTypNamed(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_named)
        elif t.is_comp():
            tags = ["tcomp"]
            ckey = self.index_compinfo_key(
                cast(CTypComp, t).get_struct(), cast(Any, t.cd).cfile.index
            )
            args = [ckey] + ia(t.get_attributes())

            def f_comp(index: int, key: Tuple[str, str]) -> CTypComp:
                return CTypComp(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_comp)
        elif t.is_enum():
            tags = t.tags
            args = ia(t.get_attributes())

            def f_enum(index: int, key: Tuple[str, str]) -> CTypEnum:
                return CTypEnum(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_enum)
        elif t.is_array():
            tags = ["tarray"]
            arraysize = (
                self.index_exp(cast(CTypArray, t).get_array_size_expr())
                if cast(CTypArray, t).has_array_size_expr()
                else (-1)
            )
            args = [self.index_typ(cast(CTypArray, t).get_array_basetype()), arraysize] + ia(
                t.get_attributes()
            )

            def f_array(index: int, key: Tuple[str, str]) -> CTypArray:
                return CTypArray(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_array)
        elif t.is_function():
            index_funargs_opt = self.index_funargs_opt(cast(CTypFun, t).get_args())
            ixfunargs = -1 if index_funargs_opt is None else index_funargs_opt
            tags = ["tfun"]
            args = [
                self.index_typ(cast(CTypFun, t).get_return_type()),
                ixfunargs,
                (1 if cast(CTypFun, t).is_vararg() else 0),
            ] + ia(t.get_attributes())

            def f_fun(index: int, key: Tuple[str, str]) -> CTypFun:
                return CTypFun(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_fun)
        elif t.is_builtin_vaargs():
            tags = ["tbuiltinvaargs"]
            args = ia(t.get_attributes())

            def f_builtin_varargs(index: int, key: Tuple[str, str]) -> CTypBuiltinVaargs:
                return CTypBuiltinVaargs(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_builtin_varargs)
        else:
            print("cdict: no case yet for " + str(t))
            exit(1)

    def index_typsig(self, t: object) -> None:
        return None  # TBD

    def index_typsiglist(self, t: object) -> None:
        return None  # TBD

    def index_string(self, s: str) -> int:
        return self.string_table.add(s)

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for (t, _) in self.tables:
            tnode = ET.Element(t.name)
            cast(IndexedTable[IndexedTableValue], t).write_xml(tnode, f)
            node.append(tnode)
        for (t, _) in self.string_tables:
            tnode = ET.Element(t.name)
            cast(StringIndexedTable, t).write_xml(tnode)
            node.append(tnode)

    def __str__(self) -> str:
        lines = []
        for (t, _) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)

    def _read_xml_attrparam_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CAttrBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CAttrBase)

        self.attrparam_table.read_xml(txnode, "n", get_value)

    def _read_xml_attribute_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CAttribute:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CAttribute(*args)

        self.attribute_table.read_xml(txnode, "n", get_value)

    def _read_xml_attributes_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CAttributes:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CAttributes(*args)

        self.attributes_table.read_xml(txnode, "n", get_value)

    def _read_xml_constant_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CConstBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CConstBase)

        self.constant_table.read_xml(txnode, "n", get_value)

    def _read_xml_exp_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CExpBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CExpBase)

        self.exp_table.read_xml(txnode, "n", get_value)

    def _read_xml_funarg_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CFunArg:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CFunArg(*args)

        self.funarg_table.read_xml(txnode, "n", get_value)

    def _read_xml_funargs_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CFunArgs:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CFunArgs(*args)

        self.funargs_table.read_xml(txnode, "n", get_value)

    def _read_xml_lhost_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CLHostBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CLHostBase)

        self.lhost_table.read_xml(txnode, "n", get_value)

    def _read_xml_lval_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CLval:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CLval(*args)

        self.lval_table.read_xml(txnode, "n", get_value)

    def _read_xml_offset_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> COffsetBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), COffsetBase)

        self.offset_table.read_xml(txnode, "n", get_value)

    def _read_xml_typ_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CTypBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CTypBase)

        self.typ_table.read_xml(txnode, "n", get_value)

    def _read_xml_typsig_table(self, txnode: ET.Element) -> None:
        def get_value(n: ET.Element) -> CTypsigTSBase:
            return CD.construct_c_dictionary_record(*((self,) + IT.get_rep(n)), CTypsigTSBase)

        self.typsig_table.read_xml(txnode, "n", get_value)

    def _read_xml_typsiglist_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> CTypsigList:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CTypsigList(*args)

        self.typsiglist_table.read_xml(txnode, "n", get_value)

    def _read_xml_string_table(self, txnode: ET.Element) -> None:
        self.string_table.read_xml(txnode)
