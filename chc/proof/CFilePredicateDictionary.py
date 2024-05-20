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
"""Dictionary for proof obligation predicates."""

import xml.etree.ElementTree as ET

from typing import (
    Any, Callable, cast, Dict, List, Mapping, Optional, TYPE_CHECKING)

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue

from chc.proof.CFilePredicateRecord import pdregistry
import chc.proof.CPOPredicate as PO

if TYPE_CHECKING:
    from chc.app.CExp import CExp
    from chc.app.CFile import CFile
    from chc.app.CFileDictionary import CFileDictionary


class CFilePredicateDictionary(object):
    """Dictionary that encodes proof obligation predicates."""

    def __init__(self, cfile: "CFile", xnode: Optional[ET.Element]) -> None:
        self._cfile = cfile
        self.po_predicate_table = IndexedTable("po-predicate-table")
        self.tables = [self.po_predicate_table]
        self._objmaps: Dict[
            str, Callable[[], Mapping[int, IndexedTableValue]]] = {
                "predicate": self.get_predicate_map}
        self.initialize(xnode)

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def dictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    def get_predicate(self, ix: int) -> PO.CPOPredicate:
        return pdregistry.mk_instance(
            self, self.po_predicate_table.retrieve(ix), PO.CPOPredicate)

    def get_predicate_map(self) -> Dict[int, IndexedTableValue]:
        return self.po_predicate_table.objectmap(self.get_predicate)

    '''
    def mk_predicate_index(self, tags: List[str], args: List[int]) -> int:

        def f(index:int, tags: List[str], args: List[int]) -> int:
            itv = IndexedTableValue(index, tags, args)
            return pdregistry.mk_instance(self, itv, PO.CPOPredicate)
            # return po_predicate_constructors[tags[0]]((self, index, tags, args))

        return self.po_predicate_table.add_tags_args(tags, args, f)

    def index_xpredicate(self, p: CPOPredicate, subst={}) -> int:
        def gett(t):
            return self.dictionary.s_term_to_exp_index(t, subst=subst)

        if p.is_not_null():
            args = [gett(p.get_term())]
            tags = ["nn"]

            def f(index, key):
                return PO.CPONotNull(self, index, tags, args)

            return self.po_predicate_table.add(get_key(tags, args), f)
        if p.is_relational_expr():
            expsubst = {}
            for name in subst:
                expix = self.dictionary.varinfo_to_exp_index(subst[name])
                expsubst[name] = self.dictionary.get_exp(expix)
            expix = self.dictionary.s_term_bool_expr_to_exp_index(
                p.get_op(), p.get_term1(), p.get_term2(), expsubst
            )
            args = [expix]
            tags = ["vc"]

            def f(index, key):
                return PO.CPOValueConstraint(self, index, tags, args)

            return self.po_predicate_table.add(get_key(tags, args), f)
        print("Index xpredicate missing: " + str(p))
        exit(1)
    '''

    def index_predicate(
            self,
            p: PO.CPOPredicate,
            subst: Dict[int, "CExp"]={}) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> PO.CPOPredicate:
            itv = IndexedTableValue(index, tags, args)
            return pdregistry.mk_instance(self, itv, PO.CPOPredicate)

        if p.is_not_null:
            p = cast(PO.CPONotNull, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_null:
            p = cast(PO.CPONull, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_valid_mem:
            p = cast(PO.CPOValidMem, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_in_scope:
            p = cast(PO.CPOInScope, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

            '''
        elif p.is_can_leave_scope:
            p = cast(PO.CPOCanLeaveScope, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]
            '''

        elif p.is_stack_address_escape:
            p = cast(PO.CPOStackAddressEscape, p)
            if p.has_lval():
                args = [
                    self.dictionary.index_lval(p.lval, subst=subst),
                    self.dictionary.index_exp(p.exp, subst=subst),
                ]
            else:
                args = [-1, self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_allocation_base:
            p = cast(PO.CPOAllocationBase, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_type_at_offset:
            p = cast(PO.CPOTypeAtOffset, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp, subst=subst),
            ]

        elif p.is_lower_bound:
            p = cast(PO.CPOLowerBound, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp, subst=subst),
            ]

        elif p.is_upper_bound:
            p = cast(PO.CPOUpperBound, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp, subst=subst),
            ]

        elif p.is_index_lower_bound:
            p = cast(PO.CPOIndexLowerBound, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_index_upper_bound:
            p = cast(PO.CPOIndexUpperBound, p)
            args = [
                self.dictionary.index_exp(p.exp, subst=subst),
                self.dictionary.index_exp(p.bound, subst=subst),
            ]

        elif p.is_initialized:
            p = cast(PO.CPOInitialized, p)
            args = [self.dictionary.index_lval(p.lval, subst=subst)]

        elif p.is_initialized_range:
            p = cast(PO.CPOInitializedRange, p)
            args = [
                self.dictionary.index_exp(p.exp, subst=subst),
                self.dictionary.index_exp(p.size, subst=subst),
            ]

        elif p.is_cast:
            p = cast(PO.CPOCast, p)
            args = [
                self.dictionary.index_typ(p.srctyp),
                self.dictionary.index_typ(p.tgttyp),
                self.dictionary.index_exp(p.exp, subst=subst),
            ]

        elif p.is_pointer_cast:
            p = cast(PO.CPOPointerCast, p)
            args = [
                self.dictionary.index_typ(p.srctyp),
                self.dictionary.index_typ(p.tgttyp),
                self.dictionary.index_exp(p.exp, subst=subst),
            ]

        elif p.is_signed_to_signed_cast_lb:
            p = cast(PO.CPOSignedToSignedCastLB, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_signed_to_signed_cast_ub:
            p = cast(PO.CPOSignedToSignedCastUB, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_signed_to_unsigned_cast_lb:
            p = cast(PO.CPOSignedToUnsignedCastLB, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_signed_to_unsigned_cast_ub:
            p = cast(PO.CPOSignedToUnsignedCastUB, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_unsigned_to_signed_cast:
            p = cast(PO.CPOUnsignedToSignedCast, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_unsigned_to_unsigned_cast:
            p = cast(PO.CPOUnsignedToSignedCast, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_not_zero:
            p = cast(PO.CPONotZero, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_non_negative:
            p = cast(PO.CPONonNegative, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_no_overlap:
            p = cast(PO.CPONoOverlap, p)
            args = [
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_null_terminated:
            p = cast(PO.CPONullTerminated, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_int_underflow:
            p = cast(PO.CPOIntUnderflow, p)
            args = [
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_int_overflow:
            p = cast(PO.CPOIntOverflow, p)
            args = [
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_width_overflow:
            p = cast(PO.CPOWidthOverflow, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_ptr_lower_bound:
            p = cast(PO.CPOPtrLowerBound, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_ptr_upper_bound:
            p = cast(PO.CPOPtrUpperBound, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_ptr_upper_bound_deref:
            p = cast(PO.CPOPtrUpperBoundDeref, p)
            args = [
                self.dictionary.index_typ(p.typ),
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_value_constraint:
            p = cast(PO.CPOValueConstraint, p)
            args = [self.dictionary.index_exp(p.exp, subst=subst)]

        elif p.is_common_base:
            p = cast(PO.CPOCommonBase, p)
            args = [
                self.dictionary.index_exp(p.exp1, subst=subst),
                self.dictionary.index_exp(p.exp2, subst=subst),
            ]

        elif p.is_buffer:
            p = cast(PO.CPOBuffer, p)
            args = [
                self.dictionary.index_exp(p.exp, subst=subst),
                self.dictionary.index_exp(p.size, subst=subst),
            ]

        elif p.is_rev_buffer:
            p = cast(PO.CPORevBuffer, p)
            args = [
                self.dictionary.index_exp(p.exp, subst=subst),
                self.dictionary.index_exp(p.size, subst=subst),
            ]

        else:
            raise UF.CHCError("**** Predicate without indexing: " + str(p))

        return self.po_predicate_table.add_tags_args(p.tags, args, f)

    def read_xml_predicate(self, xnode: ET.Element, tag: str = "ipr") -> PO.CPOPredicate:
        xipr = xnode.get(tag)
        if xipr is not None:
            return self.get_predicate(int(xipr))
        else:
            raise UF.CHCError("ipr attribute missing from cpo predicate")

    def write_xml_predicate(
            self, xnode: ET.Element, pred: PO.CPOPredicate, tag: str = "ipr"
    ) -> None:
        xnode.set(tag, str(self.index_predicate(pred)))

    def initialize(
            self, xnode: Optional[ET.Element], force: bool = False) -> None:
        if self.po_predicate_table.size() > 0 and not force:
            return
        if xnode is None:
            return
        for t in self.tables:
            t.reset()
            xtable = xnode.find(t.name)
            if xtable is not None:
                t.read_xml(xtable, "n")
            else:
                raise UF.CHCError("Error reading table " + t.name)

    # ----------------------------- printing -----------------------------------

    def objectmap_to_string(self, name: str) -> str:
        if name == "predicate":
            objmap = self.get_predicate_map()
            lines: List[str] = []
            if len(objmap) == 0:
                lines.append("\nTable for {name} is empty\n")
            else:
                lines.append("index  value")
                lines.append("-" * 80)
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "    " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name +  " does not correspond to a table")

    def __str__(self) -> str:
        lines: List[str] = []
        for t in self.tables:
            lines.append(str(t))
        return "\n".join(lines)

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
