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
"""Abstract superclass for CGlobalDictionary and CFileDictionary."""

import xml.etree.ElementTree as ET

from abc import ABC, abstractmethod
from typing import (
    cast, Any, Callable, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING)

from chc.app.CAttributes import CAttr, CAttribute, CAttributes
from chc.app.CConst import CConst
from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry
from chc.app.CExp import CExp
from chc.app.CLHost import CLHost
from chc.app.CLval import CLval
from chc.app.COffset import COffset
from chc.app.CTyp import CTyp, CFunArg, CFunArgs
from chc.app.CTypsig import CTypsig, CTypsigList

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue
from chc.util.loggingutil import chklogger
from chc.util.StringIndexedTable import StringIndexedTable

if TYPE_CHECKING:
    from chc.api.ApiParameter import APGlobal
    from chc.api.STerm import STerm, STNumConstant, STArgValue
    from chc.app.CAttributes import CAttrInt, CAttrStr, CAttrCons
    from chc.app.CAttributes import CAttrSizeOf, CAttrSizeOfE, CAttrSizeOfS
    from chc.app.CAttributes import CAttrAlignOf, CAttrAlignOfE, CAttrAlignOfS
    from chc.app.CAttributes import CAttrUnOp, CAttrBinOp
    from chc.app.CAttributes import CAttrDot, CAttrStar, CAttrAddrOf
    from chc.app.CAttributes import CAttrIndex, CAttrQuestion
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CConst import CConstStr, CConstEnum
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CExp import CExpConst, CExpUnOp, CExpBinOp, CExpQuestion
    from chc.app.CExp import CExpCastE, CExpLval
    from chc.app.CExp import CExpAddrOf, CExpStartOf
    from chc.app.CExp import CExpAlignOf, CExpAlignOfE
    from chc.app.CExp import CExpSizeOf, CExpSizeOfE, CExpSizeOfStr
    from chc.app.CExp import CExpFnApp, CExpCnApp
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CLHost import CLHostVar, CLHostMem
    from chc.app.COffset import CFieldOffset, CIndexOffset
    from chc.app.CTyp import CTypPtr, CTypComp, CTypArray, CTypFun
    from chc.app.CVarInfo import CVarInfo


class CDictionary(ABC):
    """Indexed types.

    subclassed by

    - CFileDictionary: Corresponds with cchlib/cCHDictionary.
    - CGlobalDictionary: constructed in the python api
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
            self.typsiglist_table]
        self._objmaps: Dict[
            str, Callable[[], Mapping[int, IndexedTableValue]]] = {
            "attrparam": self.get_attrparam_map,
            "attribute": self.get_attribute_map,
            "attributes": self.get_attributes_map,
            "constant": self.get_constant_map,
            "exp": self.get_exp_map,
            "funarg": self.get_funarg_map,
            "funargs": self.get_funargs_map,
            "lhost": self.get_lhost_map,
            "lval": self.get_lval_map,
            "offset": self.get_offset_map,
            "typ": self.get_typ_map,
            "typsig": self.get_typsig_map,
            "typsiglist": self.get_typsig_list_map}
        # self.string_table = StringIndexedTable("string-table")

    @property
    @abstractmethod
    def cfile(self) -> "CFile":
        ...

    @property
    @abstractmethod
    def decls(self) -> "CDeclarations":
        ...

    @property
    @abstractmethod
    def is_global(self) -> bool:
        ...

    # -------------- Retrieve items from dictionary tables -------------------

    def get_attrparam(self, ix: int) -> CAttr:
        return cdregistry.mk_instance(
            self, self.attrparam_table.retrieve(ix), CAttr)

    def get_attrparam_map(self) -> Dict[int, IndexedTableValue]:
        return self.attrparam_table.objectmap(self.get_attrparam)

    def get_attribute(self, ix: int) -> CAttribute:
        return CAttribute(self, self.attribute_table.retrieve(ix))

    def get_attribute_map(self) -> Dict[int, IndexedTableValue]:
        return self.attribute_table.objectmap(self.get_attribute)

    def get_attributes(self, ix: int) -> CAttributes:
        return CAttributes(self, self.attributes_table.retrieve(ix))

    def get_attributes_map(self) -> Dict[int, IndexedTableValue]:
        return self.attributes_table.objectmap(self.get_attributes)

    def get_constant(self, ix: int) -> CConst:
        return cdregistry.mk_instance(
            self, self.constant_table.retrieve(ix), CConst)

    def get_constant_map(self) -> Dict[int, IndexedTableValue]:
        return self.constant_table.objectmap(self.get_constant)

    def get_funarg(self, ix: int) -> CFunArg:
        return CFunArg(self, self.funarg_table.retrieve(ix))

    def get_funarg_map(self) -> Dict[int, IndexedTableValue]:
        return self.funarg_table.objectmap(self.get_funarg)

    def get_funargs(self, ix: int) -> CFunArgs:
        return CFunArgs(self, self.funargs_table.retrieve(ix))

    def get_funargs_map(self) -> Dict[int, IndexedTableValue]:
        return self.funargs_table.objectmap(self.get_funargs)

    def get_funargs_opt(self, ix: int) -> Optional[CFunArgs]:
        if ix >= 0:
            return self.get_funargs(ix)
        else:
            return None

    def get_lhost(self, ix: int) -> CLHost:
        return cdregistry.mk_instance(
            self, self.lhost_table.retrieve(ix), CLHost)

    def get_lhost_map(self) -> Dict[int, IndexedTableValue]:
        return self.lhost_table.objectmap(self.get_lhost)

    def get_lval(self, ix: int) -> CLval:
        return CLval(self, self.lval_table.retrieve(ix))

    def get_lval_map(self) -> Dict[int, IndexedTableValue]:
        return self.lval_table.objectmap(self.get_lval)

    def get_offset(self, ix: int) -> COffset:
        return cdregistry.mk_instance(
            self, self.offset_table.retrieve(ix), COffset)

    def get_offset_map(self) -> Dict[int, IndexedTableValue]:
        return self.offset_table.objectmap(self.get_offset)

    def get_typ(self, ix: int) -> CTyp:
        return cdregistry.mk_instance(
            self, self.typ_table.retrieve(ix), CTyp)

    def get_typ_map(self) -> Dict[int, IndexedTableValue]:
        return self.typ_table.objectmap(self.get_typ)

    def get_exp(self, ix: int) -> CExp:
        return cdregistry.mk_instance(
            self, self.exp_table.retrieve(ix), CExp)

    def get_exp_map(self) -> Dict[int, IndexedTableValue]:
        return self.exp_table.objectmap(self.get_exp)

    def get_exp_opt(self, ix: int) -> Optional[CExp]:
        if ix >= 0:
            return self.get_exp(ix)
        else:
            return None

    def get_typsig(self, ix: int) -> CTypsig:
        return cdregistry.mk_instance(
            self, self.typsig_table.retrieve(ix), CTypsig)

    def get_typsig_map(self) -> Dict[int, IndexedTableValue]:
        return self.typsig_table.objectmap(self.get_typsig)

    def get_typsig_list(self, ix: int) -> CTypsigList:
        itv = self.typsiglist_table.retrieve(ix)
        return CTypsigList(self, itv)

    def get_typsig_list_map(self) -> Dict[int, IndexedTableValue]:
        return self.typsiglist_table.objectmap(self.get_typsig_list)

    def get_string(self, ix: int) -> str:
        return self.string_table.retrieve(ix)

    # --------Provide read_xml/write_xml service for semantics files ----------

    def read_xml_funargs(self, node: ET.Element, tag: str = "iargs") -> CFunArgs:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_funargs(int(xml_value))
        else:
            raise Exception('xml node was missing the tag "' + tag + '"')

    def write_xml_exp(
            self, node: ET.Element, exp: CExp, tag: str = "iexp") -> None:
        node.set(tag, str(self.index_exp(exp)))

    def read_xml_exp(self, node: ET.Element, tag: str = "iexp") -> CExp:
        xml_value = node.get(tag)
        if xml_value:
            return self.get_exp(int(xml_value))
        else:
            raise Exception('xml node was missing the tag "' + tag + '"')

    def write_xml_exp_opt(
        self,
        node: ET.Element,
        exp: Optional[CExp],
        tag: str = "iexp",
    ) -> None:
        if exp is None:
            return
        self.write_xml_exp(node, exp)

    def read_xml_exp_opt(
            self, node: ET.Element, tag: str = "iexp") -> Optional[CExp]:
        xml_tag = node.get(tag)
        if xml_tag is None:
            return None
        else:
            return self.get_exp_opt(int(xml_tag))

    # --------------- stubs, overridden in file/global dictionary -------------

    def index_compinfo_key(self, compinfo: "CCompInfo", _: object) -> int:
        return compinfo.ckey

    def index_varinfo_vid(self, vid: int, _: int) -> int:
        return vid

    def convert_ckey(self, ckey: int, fid: int = -1) -> int:
        return ckey

    # -------------------- Index items by category ---------------------------

    def mk_attrparam(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CAttr:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CAttr)

        return self.attrparam_table.add_tags_args(tags, args, f)

    def index_attrparam(self, a: CAttr) -> int:
        args: List[int]

        if a.is_int:
            return self.mk_attrparam(a.tags, a.args)

        if a.is_str:
            args = [self.index_string(cast("CAttrStr", a).stringvalue)]
            return self.mk_attrparam(a.tags, args)

        if a.is_cons:
            a = cast("CAttrCons", a)
            args = [self.index_attrparam(p) for p in a.params]
            return self.mk_attrparam(a.tags, args)

        if a.is_sizeof:
            a = cast("CAttrSizeOf", a)
            args = [self.index_typ(a.typ)]
            return self.mk_attrparam(a.tags, args)

        if a.is_sizeofe:
            a = cast("CAttrSizeOfE", a)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_sizeofs:
            a = cast("CAttrSizeOfS", a)
            args = [self.index_typsig(a.typsig)]
            return self.mk_attrparam(a.tags, args)

        if a.is_alignof:
            a = cast("CAttrAlignOf", a)
            args = [self.index_typ(a.typ)]
            return self.mk_attrparam(a.tags, args)

        if a.is_alignofe:
            a = cast("CAttrAlignOfE", a)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_alignofs:
            a = cast("CAttrAlignOfS", a)
            args = [self.index_typsig(a.typsig)]
            return self.mk_attrparam(a.tags, args)

        if a.is_unop:
            a = cast("CAttrUnOp", a)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_binop:
            a = cast("CAttrBinOp", a)
            args = [
                self.index_attrparam(a.param1), self.index_attrparam(a.param2)]
            return self.mk_attrparam(a.tags, args)

        if a.is_dot:
            a = cast("CAttrDot", a)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_star:
            a = cast("CAttrStar", a)
            if a.index == a.param.index:
                args = [a.index]
                chklogger.logger.info("Index self-referential attribute")
                return self.mk_attrparam(a.tags, args)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_addrof:
            a = cast("CAttrAddrOf", a)
            args = [self.index_attrparam(a.param)]
            return self.mk_attrparam(a.tags, args)

        if a.is_index:
            a = cast("CAttrIndex", a)
            args = [
                self.index_attrparam(a.param1), self.index_attrparam(a.param2)]
            return self.mk_attrparam(a.tags, args)

        if a.is_question:
            a = cast("CAttrQuestion", a)
            args = [
                self.index_attrparam(a.param1),
                self.index_attrparam(a.param2),
                self.index_attrparam(a.param3)]
            return self.mk_attrparam(a.tags, args)

        else:
            raise Exception("Unknown attrparam type")

    def index_attribute(self, a: CAttribute) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CAttribute:
            itv = IndexedTableValue(index, tags, args)
            return CAttribute(self, itv)

        args: List[int] = [self.index_attrparam(p) for p in a.params]
        return self.attribute_table.add_tags_args(a.tags, args, f)

    def index_attributes(self, aa: CAttributes) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CAttributes:
            itv = IndexedTableValue(index, tags, args)
            return CAttributes(self, itv)

        args: List[int] = [self.index_attribute(a) for a in aa.attributes]
        return self.attributes_table.add_tags_args(aa.tags, args, f)

    def mk_constant_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CConst:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CConst)

        return self.constant_table.add_tags_args(tags, args, f)

    def index_constant(self, c: CConst) -> int:  # TBF
        args: List[int]

        if c.is_int:
            return self.mk_constant_index(c.tags, c.args)

        if c.is_str:
            c = cast("CConstStr", c)
            args = [self.index_string(c.stringvalue)]
            return self.mk_constant_index(c.tags, args)

        if c.is_wstr:
            return self.mk_constant_index(c.tags, c.args)

        if c.is_chr:
            return self.mk_constant_index(c.tags, c.args)

        if c.is_real:
            return self.mk_constant_index(c.tags, c.args)

        if c.is_enum:
            c = cast("CConstEnum", c)
            args = [self.index_exp(c.exp)]
            return self.mk_constant_index(c.tags, args)

        else:
            raise Exception("Unknown constant type")

    def mk_exp_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CExp:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CExp)

        return self.exp_table.add_tags_args(tags, args, f)

    def mk_typ_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CTyp:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CTyp)

        return self.typ_table.add_tags_args(tags, args, f)

    def mk_lhost_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CLHost:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, CLHost)

        return self.lhost_table.add_tags_args(tags, args, f)

    def mk_lval_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CLval:
            itv = IndexedTableValue(index, tags, args)
            return CLval(self, itv)

        return self.lval_table.add_tags_args(tags, args, f)

    def mk_offset_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> COffset:
            itv = IndexedTableValue(index, tags, args)
            return cdregistry.mk_instance(self, itv, COffset)

        return self.offset_table.add_tags_args(tags, args, f)

    def varinfo_to_exp_index(self, vinfo: "CVarInfo") -> int:
        lhostix = self.mk_lhost_index(["var", vinfo.vname], [vinfo.real_vid])
        offsetix = self.mk_offset_index(["n"], [])
        lvalix = self.mk_lval_index([], [lhostix, offsetix])
        return self.mk_exp_index(["lval"], [lvalix])

    def s_term_to_exp_index(
            self, t: "STerm", subst: Dict[Any, Any] = {}, fid: int = -1) -> int:
        """Create exp index from interface s_term"""
        if t.is_return_value:
            if "return" in subst:
                return self.index_exp(subst["return"])
            else:
                raise Exception("Error in index_s_term: no return found")

        elif t.is_num_constant:
            t = cast("STNumConstant", t)
            c = t.constantvalue
            ctags = ["int", str(c), "iint"]
            tags = ["const"]
            args = [self.mk_constant_index(ctags, [])]
            return self.mk_exp_index(tags, args)

        elif t.is_arg_value:
            t = cast("STArgValue", t)
            par = t.parameter
            if par.is_global:
                gname = cast("APGlobal", par).name
                if gname in subst:
                    return self.index_exp(subst[gname])
                else:
                    raise Exception(
                        "Error in index_s_term: global variable "
                        + gname
                        + " not found"
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

    def index_opt_exp(
            self,
            e: Optional[CExp],
            subst: Dict[int, CExp] = {},
            fid: int = -1) -> int:

        if e is None:
            return -1
        else:
            return self.index_exp(e, subst=subst, fid=fid)

    def index_exp(
            self,
            e: CExp,
            subst: Dict[int, CExp] = {},
            fid: int = -1) -> int:

        args: List[int]

        if e.is_constant:
            e = cast("CExpConst", e)
            args = [self.index_constant(e.constant)]
            return self.mk_exp_index(e.tags, args)

        if e.is_sizeof:
            e = cast("CExpSizeOf", e)
            args = [self.index_typ(e.typ)]
            return self.mk_exp_index(e.tags, args)

        if e.is_sizeofe:
            e = cast("CExpSizeOfE", e)
            args = [self.index_exp(e.exp, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_sizeofstr:
            e = cast("CExpSizeOfStr", e)
            args = [self.index_string(e.stringvalue)]
            return self.mk_exp_index(e.tags, args)

        if e.is_unop:
            e = cast("CExpUnOp", e)
            args = [
                self.index_exp(e.exp, subst=subst, fid=fid),
                self.index_typ(e.typ)]
            return self.mk_exp_index(e.tags, args)

        if e.is_binop:
            e = cast("CExpBinOp", e)
            args = [
                self.index_exp(e.exp1, subst=subst, fid=fid),
                self.index_exp(e.exp2, subst=subst, fid=fid),
                self.index_typ(e.typ)]
            return self.mk_exp_index(e.tags, args)

        if e.is_question:
            e = cast("CExpQuestion", e)
            args = [
                self.index_exp(e.condition, subst=subst, fid=fid),
                self.index_exp(e.true_exp, subst=subst, fid=fid),
                self.index_exp(e.false_exp, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_caste:
            e = cast("CExpCastE", e)
            args = [
                self.index_typ(e.typ),
                self.index_exp(e.exp, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_alignof:
            e = cast("CExpAlignOf", e)
            args = [self.index_typ(e.typ)]
            return self.mk_exp_index(e.tags, args)

        if e.is_alignofe:
            e = cast("CExpAlignOfE", e)
            args = [self.index_exp(e.exp, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_addrof:
            e = cast("CExpAddrOf", e)
            args = [self.index_lval(e.lval, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_startof:
            e = cast("CExpStartOf", e)
            args = [self.index_lval(e.lval, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_lval:
            e = cast("CExpLval", e)
            args = [self.index_lval(e.lval, subst=subst, fid=fid)]
            return self.mk_exp_index(e.tags, args)

        if e.is_fn_app:
            e = cast("CExpFnApp", e)
            args = [
                e.args[0],   # line number
                e.args[1],   # byte number
                self.index_exp(e.exp, subst=subst, fid=fid)]
            args = (
                args
                + [self.index_opt_exp(optx, subst=subst, fid=fid)
                   for optx in e.arguments])
            return self.mk_exp_index(e.tags, args)

        if e.is_cn_app:
            e = cast("CExpCnApp", e)
            args = [self.index_typ(e.typ)]
            args = (
                args
                + [self.index_opt_exp(optx, subst=subst, fid=fid)
                   for optx in e.arguments])
            return self.mk_exp_index(e.tags, args)

        else:
            raise Exception("cdict:no case yet for exp " + str(e))

    def index_funarg(self, funarg: CFunArg) -> int:
        args: List[int] = [self.index_typ(funarg.typ)]

        def f(index: int, tags: List[str], args: List[int]) -> CFunArg:
            itv = IndexedTableValue(index, tags, args)
            return CFunArg(self, itv)

        return self.funarg_table.add_tags_args(funarg.tags, args, f)

    def index_funargs_opt(self, opt_funargs: Optional[CFunArgs]) -> int:
        if opt_funargs is None:
            return -1

        def f(index: int, tags: List[str], args: List[int]) -> CFunArgs:
            itv = IndexedTableValue(index, tags, args)
            return CFunArgs(self, itv)

        args: List[int] = [
            self.index_funarg(f) for f in opt_funargs.arguments]
        return self.funargs_table.add_tags_args(opt_funargs.tags, args, f)

    def index_lhost(
            self, h: CLHost, subst: Dict[int, CExp] = {}, fid: int = -1) -> int:

        args: List[int]

        if h.is_var:
            h = cast("CLHostVar", h)
            args = [self.index_varinfo_vid(h.vid, fid)]
            return self.mk_lhost_index(h.tags, args)

        elif h.is_mem:
            h = cast("CLHostMem", h)
            args = [self.index_exp(h.exp, subst=subst, fid=fid)]
            return self.mk_lhost_index(h.tags, args)

        else:
            raise Exception("Unknown type of lhost: \"" + str(h) + "\"")

    def index_lval(
            self, lval: CLval, subst: Dict[int, CExp] = {}, fid: int = -1) -> int:
        args: List[int] = [
            self.index_lhost(lval.lhost, subst=subst, fid=fid),
            self.index_offset(lval.offset, fid=fid)]
        return self.mk_lval_index(lval.tags, args)

    def index_offset(self, o: COffset, fid: int = -1) -> int:

        args: List[int]

        if not o.has_offset():
            return self.mk_offset_index(o.tags, o.args)

        if o.is_field:
            o = cast("CFieldOffset", o)
            ckey = self.convert_ckey(o.ckey, cast(Any, o.cd).cfile.index)
            args = [ckey, self.index_offset(o.offset, fid)]
            return self.mk_offset_index(o.tags, args)

        if o.is_index:
            o = cast("CIndexOffset", o)
            args = [
                self.index_exp(o.index_exp),
                self.index_offset(o.offset, fid)]
            return self.mk_offset_index(o.tags, args)

        raise UF.CHError("cdict: no case yet for " + str(o))

    def index_typ(self, t: CTyp) -> int:  # TBF

        # omit attributes argument if there are no attributes
        def ia(attrs: CAttributes) -> List[int]:
            if len(attrs.attributes) == 0:
                return []
            else:
                return [self.index_attributes(attrs)]

        args: List[int] = ia(t.attributes)

        if t.is_void:
            return self.mk_typ_index(t.tags, args)

        if t.is_int:
            return self.mk_typ_index(t.tags, args)

        elif t.is_float:
            return self.mk_typ_index(t.tags, args)

        if t.is_pointer:
            t = cast("CTypPtr", t)
            args = [self.index_typ(t.pointedto_type)] + args
            return self.mk_typ_index(t.tags, args)

        if t.is_named_type:
            return self.mk_typ_index(t.tags, args)

        if t.is_comp:
            t = cast("CTypComp", t)
            fid = cast(Any, t.cd).cfile.index
            ckey = self.index_compinfo_key(t.compinfo, fid)
            args = [ckey] + args
            return self.mk_typ_index(t.tags, args)

        if t.is_enum:
            return self.mk_typ_index(t.tags, args)

        if t.is_array:
            t = cast("CTypArray", t)
            if t.has_array_size_expr():
                ixsize = self.index_exp(t.array_size_expr)
            else:
                ixsize = -1
            args = (
                [self.index_typ(t.array_basetype), ixsize] + args)
            return self.mk_typ_index(t.tags, args)

        if t.is_function:
            t = cast("CTypFun", t)
            index_funargs_opt = self.index_funargs_opt(t.funargs)
            args = ([
                self.index_typ(t.return_type),
                index_funargs_opt,
                (1 if t.is_vararg else 0)] + args)
            return self.mk_typ_index(t.tags, args)

        if t.is_builtin_vaargs:
            return self.mk_typ_index(t.tags, args)

        else:
            print("cdict: no case yet for " + str(t))
            exit(1)

    def index_typsig(self, t: CTypsig) -> int:
        return -1  # TBD

    def index_typsiglist(self, t: CTypsigList) -> int:
        return -1  # TBD

    def index_string(self, s: str) -> int:
        return self.string_table.add(s)

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
            if not self.is_global:
                chklogger.logger.info(
                    "%s: Write table %s with %d entries",
                    self.cfile.name, t.name, t.size())
        tnode = ET.Element(self.string_table.name)
        self.string_table.write_xml(tnode)
        node.append(tnode)

    # --------------------------- printing -------------------------------------

    def objectmap_to_string(self, name: str) -> str:
        if name in self._objmaps:
            objmap = self._objmaps[name]()
            lines: List[str] = []
            if len(objmap) == 0:
                lines.append(f"\nTable for {name} is empty\n")
            else:
                lines.append("index  value")
                lines.append("-" * 80)
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "    " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name + " does not correspond to a table")

    def __str__(self) -> str:
        lines = []
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)

    # -------------------------- initialization --------------------------------

    def initialize(self, xnode: ET.Element, force: bool = False) -> None:
        for t in self.tables:
            t.reset()
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.read_xml(xtable, "n")
                if not self.is_global:
                    chklogger.logger.info(
                        "%s: Read xml table %s with %d entries",
                        self.cfile.name, t.name, t.size())
            else:
                raise UF.CHCError("Error reading table " + t.name)
        self.string_table.reset()
        xstable = xnode.find(self.string_table.name)
        if xstable is not None:
            self.string_table.read_xml(xstable)
        else:
            raise UF.CHCError(
                "Error reading stringtable: " + self.string_table.name)
