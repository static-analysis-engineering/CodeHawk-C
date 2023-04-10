# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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
from typing import cast, Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import xml.etree.ElementTree as ET
from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry
import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
import chc.util.StringIndexedTable as SI

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
from chc.util.IndexedTable import IndexedTable, IndexedTableValue
from chc.util.StringIndexedTable import StringIndexedTable

if TYPE_CHECKING:
    from chc.api.ApiParameter import APGlobal
    from chc.api.STerm import STerm, STNumConstant, STArgValue
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CVarInfo import CVarInfo


class CDictionary(ABC):
    """Indexed types.

    subclassed by
    CFileDictionary: Corresponds with cchlib/cCHDictionary.
    CGlobalDictionary: constructed in the python api
    """

    def __init__(self) -> None:
        self.attrparam_table = IndexedTable("attrparam-table")
        self.attribute_table = IndexedTable("attribute-table")
        self.attributes_table = IndexedTable("attributes-table")
        self.constant_table = IndexedTable("constant-table")
        self.exp_table = IndexedTable("exp-table")
        self.funarg_table = IndexedTable("funarg-table")
        self.funargs_table = IndexedTable("funargs-table")
        self.lhost_table = IndexedTable("lhost-table")
        self.lval_table = IndexedTable("lval-table")
        self.offset_table = IndexedTable("offset-table")
        self.typ_table = IndexedTable("typ-table")
        self.typsig_table = IndexedTable("typsig-table")
        self.typsiglist_table = IndexedTable("typsiglist-table")
        self.string_table = StringIndexedTable("string-table")
        self.tables = [
            self.attrparam_table,
            self.attribute_table,
            self.attributes_table,
            self.constant_table,
            self.exp_table,
            self.funarg_table,
            self.funargs_table,
            self.lhost_table,
            self.lval_table,
            self.offset_table,
            self.typ_table,
            self.typsig_table,
            self.typsiglist_table
        ]
        self.string_table = SI.StringIndexedTable("string-table")

    @property
    @abstractmethod
    def cfile(self) -> "CFile":
        ...

    @property
    @abstractmethod
    def decls(self) -> "CDeclarations":
        ...

    # --------------- Statistics ---------------------------------------------
    '''
    def get_stats(self) -> str:
        lines = []
        for (t, _) in self.tables:
            if t.size() > 0:
                lines.append(t.name.ljust(25) + str(t.size()).rjust(4))
        return "\n".join(lines)

    def get_table(self, n: str) -> Optional[IndexedTableSuperclass]:
        return next(x[0] for x in self.tables if x[0].name == (n + "-table"))


    # create a count distribution for the objects in the table with name tname
    # that satisfy the respective case predicates
    def get_distribution(
        self,
        tname: str,
        cases: Dict[str, Callable[[object], bool]],
    ) -> Dict[str, int]:
        table = cast(Optional[IndexedTable], self.get_table(tname))
        if table is None:
            raise Exception("No table found for " + tname)
        result = {}
        for c in cases:
            result[c] = len([v for v in table.values() if cases[c](v)])
        return result
    '''

    # -------------- Retrieve items from dictionary tables -------------------

    def get_attrparam(self, ix: int) -> CAttrBase:
        return cdregistry.mk_instance(
            self, self.attrparam_table.retrieve(ix), CAttrBase)

    def get_attribute(self, ix: int) -> CAttribute:
        return cdregistry.mk_instance(
            self, self.attribute_table.retrieve(ix), CAttribute)

    def get_attributes(self, ix: int) -> CAttributes:
        return cdregistry.mk_instance(
            self, self.attributes_table.retrieve(ix), CAttributes)

    def get_constant(self, ix: int) -> CConstBase:
        return cdregistry.mk_instance(
            self, self.constant_table.retrieve(ix), CConstBase)

    def get_funarg(self, ix: int) -> CFunArg:
        return cdregistry.mk_instance(
            self, self.funarg_table.retrieve(ix), CFunArg)

    def get_funargs(self, ix: int) -> CFunArgs:
        return cdregistry.mk_instance(
            self, self.funargs_table.retrieve(ix), CFunArgs)

    def get_funargs_opt(self, ix: int) -> Optional[CFunArgs]:
        if ix >= 0:
            return self.get_funargs(ix)
        else:
            return None

    def get_lhost(self, ix: int) -> CLHostBase:
        return cdregistry.mk_instance(
            self, self.lhost_table.retrieve(ix), CLHostBase)

    def get_lval(self, ix: int) -> CLval:
        return cdregistry.mk_instance(
            self, self.lval_table.retrieve(ix), CLval)

    def get_offset(self, ix: int) -> COffsetBase:
        return cdregistry.mk_instance(
            self, self.offset_table.retrieve(ix), COffsetBase)

    def get_typ(self, ix: int) -> CTypBase:
        return cdregistry.mk_instance(
            self, self.typ_table.retrieve(ix), CTypBase)

    def get_exp(self, ix: int) -> CExpBase:
        return cdregistry.mk_instance(
            self, self.exp_table.retrieve(ix), CExpBase)

    def get_exp_opt(self, ix: int) -> Optional[CExpBase]:
        if ix >= 0:
            return self.get_exp(ix)
        else:
            return None

    def get_typsig(self, ix: int) -> CTypsigTSBase:
        return cdregistry.mk_instance(
            self, self.typsig_table.retrieve(ix), CTypsigTSBase)

    def get_typesig_list(self, ix: int) -> CTypsigList:
        itv = self.typsiglist_table.retrieve(ix)
        return CTypsigList(self, itv)

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

            def f_int(index: int, tags: List[str], args: List[int]) -> CAttrInt:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CAttrInt)

            return self.attrparam_table.add_tags_args(a.tags, a.args, f_int)
        if a.is_str():

            def f_str(index: int, tags: List[str], args: List[int]) -> CAttrStr:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CAttrStr)

            return self.attrparam_table.add_tags_args(a.tags, a.args, f_str)
        if a.is_cons():
            args = [self.index_attrparam(p) for p in cast(CAttrCons, a).get_params()]

            def f_cons(index: int, tags: List[str], args: List[int]) -> CAttrCons:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CAttrCons)

            return self.attrparam_table.add_tags_args(a.tags, args, f_cons)
        raise Exception('No case yet for attrparam "' + str(a) + '"')

    def index_attribute(self, a: CAttribute) -> int:
        args = [self.index_attrparam(p) for p in a.get_params()]

        def f(index: int, tags: List[str], args: List[int]) -> CAttribute:
            itv = IT.IndexedTableValue(index, tags, args)
            return CAttribute(self, itv)

        return self.attribute_table.add_tags_args(a.tags, args, f)

    def index_attributes(self, aa: CAttributes) -> int:
        args = [self.index_attribute(a) for a in aa.get_attributes()]

        def f(index: int, tags: List[str], args: List[int]) -> CAttributes:
            itv = IT.IndexedTableValue(index, tags, args)
            return CAttributes(self, itv)

        return self.attributes_table.add_tags_args(aa.tags, args, f)

    def index_constant(self, c: CConstBase) -> int:  # TBF
        if c.is_int():

            def f_int(index: int, tags: List[str], args: List[int]) -> CConstInt:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CConstInt)

            return self.constant_table.add_tags_args(c.tags, c.args, f_int)
        if c.is_str():
            args = [self.index_string(cast(CConstStr, c).get_string())]

            def f_str(index: int, tags: List[str], args: List[int]) -> CConstStr:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CConstStr)

            return self.constant_table.add_tags_args(c.tags, args, f_str)
        if c.is_chr():

            def f_chr(index: int, tags: List[str], args: List[int]) -> CConstChr:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CConstChr)

            return self.constant_table.add_tags_args(c.tags, c.args, f_chr)
        if c.is_real():

            def f_real(index: int, tags: List[str], args: List[int]) -> CConstReal:
                itv = IT.IndexedTableValue(index, tags, args)
                return cdregistry.mk_instance(self, itv, CConstReal)

            return self.constant_table.add_tags_args(c.tags, c.args, f_real)
        raise Exception('No case yet for const "' + str(c) + '"')

    def mk_exp_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CExpBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CExpBase)

        return self.exp_table.add_tags_args(tags, args, f)

    def mk_constant_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CConstBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CConstBase)

        return self.constant_table.add_tags_args(tags, args, f)

    def mk_typ_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CTypBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CTypBase)

        return self.typ_table.add_tags_args(tags, args, f)

    def mk_lhost_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CLHostBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CLHostBase)

        return self.lhost_table.add_tags_args(tags, args, f)

    def mk_lval_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CLval:
            itv = IT.IndexedTableValue(index, tags, args)
            return CLval(self, itv)

        return self.lval_table.add_tags_args(tags, args, f)

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
                gname = cast("APGlobal", par).get_name()
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

        def f(index: int, tags: List[str], args: List[int]) -> CExpBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CExpBase)

        if e.is_constant():
            args = [self.index_constant(cast(CExpConst, e).get_constant())]

        elif e.is_sizeof():
            args = [self.index_typ(cast(CExpSizeOf, e).get_type())]

        elif e.is_sizeofe():
            args = [self.index_exp(cast(CExpSizeOfE, e).get_exp(), subst=subst, fid=fid)]

        elif e.is_sizeofstr():
            args = [self.index_string(cast(CExpSizeOfStr, e).get_string())]

        elif e.is_unop():
            args = [
                self.index_exp(cast(CExpUnOp, e).get_exp(), subst=subst, fid=fid),
                self.index_typ(cast(CExpUnOp, e).get_type()),
            ]

        elif e.is_binop():
            args = [
                self.index_exp(cast(CExpBinOp, e).get_exp1(), subst=subst, fid=fid),
                self.index_exp(cast(CExpBinOp, e).get_exp2(), subst=subst, fid=fid),
                self.index_typ(cast(CExpBinOp, e).get_type()),
            ]

        elif e.is_caste():
            args = [
                self.index_typ(cast(CExpCastE, e).get_type()),
                self.index_exp(cast(CExpCastE, e).get_exp(), subst=subst, fid=fid),
            ]

        elif e.is_addrof():
            args = [self.index_lval(cast(CExpAddrOf, e).get_lval(), subst=subst, fid=fid)]

        elif e.is_startof():
            args = [self.index_lval(cast(CExpStartOf, e).get_lval(), subst=subst, fid=fid)]

        elif e.is_lval():
            args = [self.index_lval(cast(CExpLval, e).get_lval(), subst=subst, fid=fid)]

        else:
            raise Exception("cdict:no case yet for exp " + str(e))

        return self.exp_table.add_tags_args(e.tags, args, f)

    def index_funarg(self, funarg: CFunArg) -> int:
        tags: List[str] = [funarg.get_name()]
        args: List[int] = [self.index_typ(funarg.get_type())]

        def f(index: int, tags: List[str], args: List[int]) -> CFunArg:
            itv = IT.IndexedTableValue(index, tags, args)
            return CFunArg(self, itv)

        return self.funarg_table.add_tags_args(tags, args, f)

    def index_funargs_opt(self, opt_funargs: Optional[CFunArgs]) -> Optional[int]:
        if opt_funargs is None:
            return None
        tags: List[str] = []
        args = [self.index_funarg(f) for f in opt_funargs.get_args()]

        def f(index: int, tags: List[str], args: List[int]) -> CFunArgs:
            itv = IT.IndexedTableValue(index, tags, args)
            return CFunArgs(self, itv)

        return self.funargs_table.add_tags_args(tags, args, f)

    def index_lhost(self, h: CLHostBase, subst: Dict[Any, Any] = {}, fid: int = -1) -> int:

        def f_lhost(index: int, tags: List[str], args: List[int]) -> CLHostBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CLHostBase)

        if h.is_var():
            args = [self.index_varinfo_vid(cast(CLHostVar, h).get_vid(), fid)]

        elif h.is_mem():
            args = [self.index_exp(cast(CLHostMem, h).get_exp(), subst=subst, fid=fid)]

        else:
            raise Exception("Unknown type of lhost: \"" + str(h) + "\"")

        return self.lhost_table.add_tags_args(h.tags, args, f_lhost)

    def index_lval(self, lval: CLval, subst: Dict[Any, Any] = {}, fid: int = -1) -> int:
        args = [
            self.index_lhost(lval.get_lhost(), subst=subst, fid=fid),
            self.index_offset(lval.get_offset()),
        ]

        def f(index: int, tags: List[str], args: List[int]) -> CLval:
            itv = IT.IndexedTableValue(index, tags, args)
            return CLval(self, itv)

        return self.lval_table.add_tags_args([], args, f)

    def mk_offset_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> COffsetBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, COffsetBase)

        return self.offset_table.add_tags_args(tags, args, f)

    def index_offset(self, o: COffsetBase, fid: int = -1) -> int:
        if not o.has_offset():
            return self.mk_offset_index(o.tags, o.args)

        if o.is_field():
            ckey = self.convert_ckey(cast(CFieldOffset, o).get_ckey(), cast(Any, o.cd).cfile.index)
            args = [ckey, self.index_offset(cast(CFieldOffset, o).get_offset(), fid)]
            return self.mk_offset_index(o.tags, args)

        if o.is_index():
            args = [
                self.index_exp(cast(CIndexOffset, o).get_index_exp()),
                self.index_offset(cast(CIndexOffset, o).get_offset(), fid),
            ]
            return self.mk_offset_index(o.tags, args)

        raise UF.CHError("cdict: no case yet for " + str(o))

    def mk_typ(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CTypBase:
            itv = IT.IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CTypBase)

        return self.typ_table.add_tags_args(tags, args, f)

    def index_typ(self, t: CTypBase) -> int:  # TBF
        # omit attributes argument if there are no attributes
        def ia(attrs: CAttributes) -> List[int]:
            return [] if len(attrs.get_attributes()) == 0 else [self.index_attributes(attrs)]

        if t.is_void():
            tags = ["tvoid"]
            args = ia(t.get_attributes())
            '''
            def f_void(index: int, key: Tuple[str, str]) -> CTypVoid:
                return CTypVoid(self, index, tags, args)

            return self.typ_table.add(IT.get_key(tags, args), f_void)
            '''
        elif t.is_int():
            tags = ["tint", cast(CTypInt, t).get_kind()]
            args = ia(t.get_attributes())

        elif t.is_float():
            tags = ["tfloat", cast(CTypFloat, t).get_kind()]
            args = ia(t.get_attributes())

        elif t.is_pointer():
            tags = ["tptr"]
            args = [self.index_typ(cast(CTypPtr, t).get_pointedto_type())] + ia(t.get_attributes())

        elif t.is_named_type():
            tags = ["tnamed", cast(CTypNamed, t).get_name()]
            args = ia(t.get_attributes())

        elif t.is_comp():
            tags = ["tcomp"]
            ckey = self.index_compinfo_key(
                cast(CTypComp, t).get_struct(), cast(Any, t.cd).cfile.index
            )
            args = [ckey] + ia(t.get_attributes())

        elif t.is_enum():
            tags = t.tags
            args = ia(t.get_attributes())

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

        elif t.is_function():
            index_funargs_opt = self.index_funargs_opt(cast(CTypFun, t).get_args())
            ixfunargs = -1 if index_funargs_opt is None else index_funargs_opt
            tags = ["tfun"]
            args = [
                self.index_typ(cast(CTypFun, t).get_return_type()),
                ixfunargs,
                (1 if cast(CTypFun, t).is_vararg() else 0),
            ] + ia(t.get_attributes())

        elif t.is_builtin_vaargs():
            tags = ["tbuiltinvaargs"]
            args = ia(t.get_attributes())

        else:
            print("cdict: no case yet for " + str(t))
            exit(1)

        return self.mk_typ(tags, args)

    def index_typsig(self, t: object) -> None:
        return None  # TBD

    def index_typsiglist(self, t: object) -> None:
        return None  # TBD

    def index_string(self, s: str) -> int:
        return self.string_table.add(s)

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
        tnode = ET.Element(self.string_table.name)
        self.string_table.write_xml(tnode)
        node.append(tnode)

    def __str__(self) -> str:
        lines = []
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)

    def initialize(self, xnode: ET.Element, force: bool = False) -> None:
        for t in self.tables:
            t.reset()
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError("Error reading table " + t.name)
        self.string_table.reset()
        xstable = xnode.find(self.string_table.name)
        if xstable is not None:
            self.string_table.read_xml(xstable)
        else:
            raise UF.CHCError(
                "Error reading stringtable: " + self.string_table.name)
