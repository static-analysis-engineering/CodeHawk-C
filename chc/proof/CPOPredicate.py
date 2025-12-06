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
"""Proof obligation predicate."""

from typing import cast, Dict, List, TYPE_CHECKING

import chc.app.CExp as CX

from chc.proof.CFilePredicateRecord import CFilePredicateRecord, pdregistry

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CExp import CExp, CExpLval
    from chc.app.CLHost import CLHostVar
    from chc.app.CLval import CLval
    from chc.app.COffset import COffset
    from chc.app.CTyp import CTyp
    from chc.app.CVarInfo import CVarInfo
    from chc.proof.CFilePredicateDictionary import CFilePredicateDictionary


po_predicate_names: Dict[str, str] = {
    'ab': 'allocation-base',
    'b': 'buffer',
    'c': 'cast',
    'cb': 'common-base',
    'cbt': 'common-base-type',
    'cls': 'can-leave-scope',
    'cr': 'controlled-resource',
    'cssl': 'signed-to-signed-cast-lb',
    'cssu': 'signed-to-signed-cast-ub',
    'csul': 'signed-to-unsigned-cast-lb',
    'csuu': 'signed-to-unsigned-cast-ub',
    'cus': 'unsigned-to-signed-cast',
    'cuu': 'unsigned-to-unsigned-cast',
    'dr': 'distinct-region',
    'fc': 'format-cast',
    'ft': 'format-string',
    'ga': 'global-address',
    'ha': 'heap-address',
    'i': 'initialized',
    'ilb': 'index-lower-bound',
    'io': 'int-overflow',
    'ir': 'initialized-range',
    'is': 'in-scope',
    'iu': 'int-underflow',
    'iub': 'index-upper-bound',
    'lb': 'lower-bound',
    'li': 'locally-initialized',
    'nm': 'new-memory',
    'nn': 'not-null',
    'nneg': 'non-negative',
    'no': 'no-overlap',
    'nt': 'null-terminated',
    'null': 'null',
    "opa": "output_parameter-argument",
    'opi': 'output_parameter-initialized',
    "opne": "output_parameter-no-escape",
    "ops": "output_parameter-scalar",
    'opu': 'output_parameter-unaltered',
    'pc': 'pointer-cast',
    'plb': 'ptr-lower-bound',
    'pre': 'precondition',
    'prm': 'preserved-all-memory',
    'pub': 'ptr-upper-bound',
    'pubd': 'ptr-upper-bound-deref',
    'pv': 'preserves-value',
    'sae': 'stack-address-escape',
    'tao': 'type-at-offset',
    'ub': 'upper-bound',
    'uio': 'uint-overflow',
    'uiu': 'uint-underflow',
    'up': 'unique-pointer',
    'va': 'var-args',
    'vc': 'value-constraint',
    'vm': 'valid-mem',
    'w': 'width-overflow',
    'z': 'not-zero'
    }


def get_predicate_tag(name: str) -> str:
    revnames = {v: k for (k, v) in po_predicate_names.items()}
    if name in revnames:
        return revnames[name]
    else:
        return name


def get_predicate_name(tag: str) -> str:
    if tag in po_predicate_names:
        return po_predicate_names[tag]
    else:
        return tag


class CPOPredicate(CFilePredicateRecord):
    """Base class for all predicates."""

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFilePredicateRecord.__init__(self, pd, ixval)

    @property
    def predicate_name(self) -> str:
        return get_predicate_name(self.tags[0])

    @property
    def is_allocation_base(self) -> bool:
        return False

    @property
    def is_buffer(self) -> bool:
        return False

    @property
    def is_cast(self) -> bool:
        return False

    @property
    def is_common_base(self) -> bool:
        return False

    @property
    def is_format_cast(self) -> bool:
        return False

    @property
    def is_controlled_resource(self) -> bool:
        return False

    @property
    def is_format_string(self) -> bool:
        return False

    @property
    def is_in_scope(self) -> bool:
        return False

    @property
    def is_can_leave_scope(self) -> bool:
        return False

    @property
    def is_global_address(self) -> bool:
        return False

    @property
    def is_heap_address(self) -> bool:
        return False

    @property
    def is_index_lower_bound(self) -> bool:
        return False

    @property
    def is_index_upper_bound(self) -> bool:
        return False

    @property
    def is_initialized(self) -> bool:
        return False

    @property
    def is_locally_initialized(self) -> bool:
        return False

    @property
    def is_initialized_range(self) -> bool:
        return False

    @property
    def is_int_overflow(self) -> bool:
        return False

    @property
    def is_int_underflow(self) -> bool:
        return False

    @property
    def is_lower_bound(self) -> bool:
        return False

    @property
    def is_new_memory(self) -> bool:
        return False

    @property
    def is_non_negative(self) -> bool:
        return False

    @property
    def is_no_overlap(self) -> bool:
        return False

    @property
    def is_not_null(self) -> bool:
        return False

    @property
    def is_not_zero(self) -> bool:
        return False

    @property
    def is_null(self) -> bool:
        return False

    @property
    def is_null_terminated(self) -> bool:
        return False

    @property
    def is_output_parameter_initialized(self) -> bool:
        return False

    @property
    def is_output_parameter_unaltered(self) -> bool:
        return False

    @property
    def is_pointer_cast(self) -> bool:
        return False

    @property
    def is_preserved_all_memory(self) -> bool:
        return False

    @property
    def is_ptr_lower_bound(self) -> bool:
        return False

    @property
    def is_ptr_upper_bound(self) -> bool:
        return False

    @property
    def is_ptr_upper_bound_deref(self) -> bool:
        return False

    @property
    def is_rev_buffer(self) -> bool:
        return False

    @property
    def is_signed_to_signed_cast_lb(self) -> bool:
        return False

    @property
    def is_signed_to_signed_cast_ub(self) -> bool:
        return False

    @property
    def is_signed_to_unsigned_cast_lb(self) -> bool:
        return False

    @property
    def is_signed_to_unsigned_cast_ub(self) -> bool:
        return False

    @property
    def is_unsigned_to_signed_cast(self) -> bool:
        return False

    @property
    def is_unsigned_to_unsigned_cast(self) -> bool:
        return False

    @property
    def is_stack_address_escape(self) -> bool:
        return False

    @property
    def is_type_at_offset(self) -> bool:
        return False

    @property
    def is_unique_pointer(self) -> bool:
        return False

    @property
    def is_upper_bound(self) -> bool:
        return False

    @property
    def is_valid_mem(self) -> bool:
        return False

    @property
    def is_value_constraint(self) -> bool:
        return False

    @property
    def is_width_overflow(self) -> bool:
        return False

    def has_variable(self, vid: int) -> bool:
        """Return true if the variable with vid occurs in any subexpression."""

        return False

    def has_variable_deref(self, vid: int) -> bool:
        """Return true if the with variable with vid is dereferenced in any subexpression."""

        return False

    def has_argument(self, vid: int) -> bool:
        """Return true if the single exp predicate argument is the variable with vid."""

        return False

    def has_variable_op(self, vid: int, op: str) -> bool:
        return False

    def has_ref_type(self) -> bool:
        return False

    def tgtkind(self) -> str:
        raise Exception(f"tgtkind not defined for {self}")

    def __str__(self) -> str:
        return "po-predicate " + self.tags[0]


@pdregistry.register_tag("nn", CPOPredicate)
class CPONotNull(CPOPredicate):
    """not-null(exp): exp is not NULL

    args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.pd.dictionary.get_exp(self.args[0])

    @property
    def is_not_null(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid

        return False

    def __str__(self) -> str:
        return "not-null(" + str(self.exp) + ")"


@pdregistry.register_tag("ga", CPOPredicate)
class CPOGlobalAddress(CPOPredicate):
    """global-address(exp): exp is a global address

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_global_address(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid
        return False

    def __str__(self) -> str:
        return "global-address(" + str(self.exp) + ")"


@pdregistry.register_tag("ha", CPOPredicate)
class CPOHeapAddress(CPOPredicate):
    """heap-address(exp): exp is a heap address

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(int(self.args[0]))

    @property
    def is_heap_address(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid

        return False

    def __str__(self) -> str:
        return "heap-address(" + str(self.exp) + ")"


@pdregistry.register_tag("dr", CPOPredicate)
class CPODistinctRegion(CPOPredicate):
    """Memory referenced by i is disinct from memory pointed to by exp.

    - args[0]: index of exp in cdictionary
    - args[1]: memref index
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(int(self.args[0]))

    @property
    def memref(self) -> int:
        return int(self.args[1])

    @property
    def is_distinct_region(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid
        return False

    def __str__(self) -> str:
        return "distinct-region(" + str(self.exp) + "," + str(self.memref) + ")"


@pdregistry.register_tag("null", CPOPredicate)
class CPONull(CPOPredicate):
    """null(exp): the expression is NULL

    - args[0]: exp
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_null(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "null(" + str(self.exp) + ")"


@pdregistry.register_tag("vm", CPOPredicate)
class CPOValidMem(CPOPredicate):
    """valid-mem(exp): exp points to valid memory (not freed).

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_valid_mem(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid
        return False

    def __str__(self) -> str:
        return "valid-mem(" + str(self.exp) + ")"


@pdregistry.register_tag("cr", CPOPredicate)
class CPOControlledResource(CPOPredicate):
    """controlled-resource(name, exp): controlled resource, with [name] is not
    tainted.

    - tags[1]: name of resource
    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def resource(self) -> str:
        return self.tags[1]

    @property
    def is_controlled_resource(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid
        return False

    def __str__(self) -> str:
        return (
            "controlled-resource:" + self.resource + "(" + str(self.exp) + ")")


@pdregistry.register_tag("sae", CPOPredicate)
class CPOStackAddressEscape(CPOPredicate):
    """Pointer is not assigned to lval with longer lifetime and is not returned.

    - args[0]: index of lval in cdictionary or -1 if None
    - args[1]: index exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(int(self.args[0]))

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def has_lval(self) -> bool:
        return (int(self.args[0])) >= 0

    @property
    def is_stack_address_escape(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        lval = ""
        if self.has_lval():
            lval = str(self.lval) + ","
        return "stack-address-escape(" + lval + str(self.exp) + ")"


@pdregistry.register_tag("is", CPOPredicate)
class CPOInScope(CPOPredicate):
    """in-scope(exp): memory pointed to by exp is in scope.

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_in_scope(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "in-scope(" + str(self.exp) + ")"


@pdregistry.register_tag("ab", CPOPredicate)
class CPOAllocationBase(CPOPredicate):
    """allocation-base(exp): exp is the start address of a dynamically allocated region.

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_allocation_base(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "allocation-base(" + str(self.exp) + ")"


@pdregistry.register_tag("nm", CPOPredicate)
class CPONewMemory(CPOPredicate):
    """new-memory(exp): the memory pointed to was allocated fresh (not aliased).

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_new_memory(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "new-memory(" + str(self.exp) + ")"


@pdregistry.register_tag("b", CPOPredicate)
class CPOBuffer(CPOPredicate):
    """buffer(exp, size): exp points to a buffer of at least size bytes.

    - args[0]: index of exp in cdictionary
    - args[1]: index of size in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def size(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_buffer(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid) or self.size.has_variable(vid)

    def __str__(self) -> str:
        return ("buffer(" + str(self.exp) + ",size:" + str(self.size) + ")")


@pdregistry.register_tag("rb", CPOPredicate)
class CPORevBuffer(CPOPredicate):
    """rev-buffer(exp, size) exp points into a buffer with at least size bytes
    preceding.

    - args[0]: index of exp in cdictionary
    - args[1]: index of presize expression in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def size(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_rev_buffer(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid) or self.size.has_variable(vid)

    def __str__(self) -> str:
        return ("rev-buffer(" + str(self.exp) + ",size:" + str(self.size) + ")")


@pdregistry.register_tag("tao", CPOPredicate)
class CPOTypeAtOffset(CPOPredicate):
    """type-at-offset(typ, exp): exp has the given type.

    - args[0]: index of typ in cdictionary
    - args[1]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    @property
    def is_type_at_offset(self) -> bool:
        return True

    def __str__(self) -> str:
        return ("type-at-offset(" + str(self.typ) + "," + str(self.exp) + ")")


@pdregistry.register_tag("lb", CPOPredicate)
class CPOLowerBound(CPOPredicate):
    """lower-bound(typ, exp): the value of pointer exp is greater than or equal to zero.

    - args[0]: index of typ in cdictionary
    - args[1]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    @property
    def is_lower_bound(self) -> bool:
        return True

    def __str__(self) -> str:
        return ("lower-bound(" + str(self.typ) + "," + str(self.exp) + ")")


@pdregistry.register_tag("ub", CPOPredicate)
class CPOUpperBound(CPOPredicate):
    """upper-bound(typ, exp): the value of pointer exp is less than or equal to the
    maximum address allowed by typ.

    - args[0]: index of typ in cdictionary
    - args[1]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    @property
    def is_upper_bound(self) -> bool:
        return True

    def __str__(self) -> str:
        return ("upper-bound(" + str(self.typ) + "," + str(self.exp) + ")")


@pdregistry.register_tag("ilb", CPOPredicate)
class CPOIndexLowerBound(CPOPredicate):
    """index-lower-bound(exp): the value of index expression exp is greater than or
    equal to zero.

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    @property
    def is_index_lower_bound(self) -> bool:
        return True

    def __str__(self) -> str:
        return ("index-lower-bound(" + str(self.exp) + ")")


@pdregistry.register_tag("iub", CPOPredicate)
class CPOIndexUpperBound(CPOPredicate):
    """index-upper-bound(exp): the value of index expression exp is less than the
    size of the array.

    - args[0]: index of exp in cdictionary
    - args[1]: index of array size expression in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def bound(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_index_upper_bound(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "index-upper-bound("
            + str(self.exp)
            + ",bound:"
            + str(self.bound)
            + ")"
        )


@pdregistry.register_tag("i", CPOPredicate)
class CPOInitialized(CPOPredicate):
    """initialized(lval): location lval has been initialized.

    - args[0]: index of lval in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(self.args[0])

    @property
    def is_initialized(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.lval.has_variable(vid)

    def has_variable_deref(self, vid: int) -> bool:
        return self.lval.has_variable_deref(vid)

    def has_ref_type(self) -> bool:
        return self.lval.has_ref_type()

    def __str__(self) -> str:
        return "initialized(" + str(self.lval) + ")"


@pdregistry.register_tag("li", CPOPredicate)
class CPOLocallyInitialized(CPOPredicate):
    """locally initialized(lval): location initialized within the function.

    - args[0]: index of lval in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
            ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def varinfo(self) -> "CVarInfo":
        return self.cdeclarations.get_varinfo(self.args[0])

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(self.args[1])

    @property
    def is_locally_initialized(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.lval.has_variable(vid)

    def has_variable_deref(self, vid: int) -> bool:
        return self.lval.has_variable_deref(vid)

    def has_ref_type(self) -> bool:
        return self.lval.has_ref_type()

    def __str__(self) -> str:
        return (
            "locally-initialized("
            + str(self.varinfo.vname)
            + ", "
            + str(self.lval)
            + ")")


@pdregistry.register_tag("ir", CPOPredicate)
class CPOInitializedRange(CPOPredicate):
    """initialized-range(exp, size): the memory range starting at the address
    pointed to by exp is initialized for at least size bytes.

    - args[0]: index of exp in cdictionary
    - args[1]: index of size in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def size(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_initialized_range(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "initialized-range("
            + str(self.exp)
            + ", len:"
            + str(self.size)
            + ")")


@pdregistry.register_tag("c", CPOPredicate)
class CPOCast(CPOPredicate):
    """cast(srctyp, tgttyp, exp): cast of exp from srctyp to tgttyp is safe.

    - args[0]: index of srctyp in cdictionary
    - args[1]: index of tgttyp in cdictionary
    - args[2]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def srctyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def tgttyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[1])

    @property
    def is_cast(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "cast("
            + str(self.exp)
            + ", from:"
            + str(self.srctyp)
            + ", to:"
            + str(self.tgttyp)
            + ")")


@pdregistry.register_tag("fc", CPOPredicate)
class CPOFormatCast(CPOPredicate):
    """format-cast(srctyp, tgttyp, exp): cast of exp from srctyp to tgttyp is safe

    Note: this predicate is used specifically in the context of the cast of an
    argument passed for a given format argument specifier.

    - args[0]: index of srctyp in cdictionary
    - args[1]: index of tgttyp in tgtdictionary
    - args[2]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def srctyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def tgttyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[1])

    @property
    def is_format_cast(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "format-cast("
            + str(self.exp)
            + ", from:"
            + str(self.srctyp)
            + ", to:"
            + str(self.tgttyp)
            + ")")


@pdregistry.register_tag("pc", CPOPredicate)
class CPOPointerCast(CPOPredicate):
    """pointer-cast(srctyp, tgttyp, exp): cast of exp from srctyp to tgttyp is safe

    Note: this predicate is used specifically for casting of pointers to other pointers

    - args[0]: index of srctyp in cdictionary
    - args[1]: index of tgttyp in tgtdictionary
    - args[2]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def srctyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def tgttyp(self) -> "CTyp":
        return self.cd.get_typ(self.args[1])

    @property
    def is_pointer_cast(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def has_argument(self, vid: int) -> bool:
        if self.exp.is_lval:
            xlval = cast("CExpLval", self.exp)
            lhost = xlval.lval.lhost
            if lhost.is_var:
                lhost = cast("CLHostVar", lhost)
                return lhost.vid == vid
        return False

    def __str__(self) -> str:
        return (
            "pointer-cast("
            + str(self.exp)
            + ", from:"
            + str(self.srctyp)
            + ", to:"
            + str(self.tgttyp)
            + ")")


@pdregistry.register_tag("csul", CPOPredicate)
class CPOSignedToUnsignedCastLB(CPOPredicate):
    """signed-to-unsigned-cast-lb(srckind, tgtkind, exp): integer cast of exp from
    signed srckind to unsigned tgtkind is safe wrt its lowerbound

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_signed_to_unsigned_cast_lb(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "signed-to-unsigned-cast-lb("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("csuu", CPOPredicate)
class CPOSignedToUnsignedCastUB(CPOPredicate):
    """signed-to-unsigned-cast-ub(srckind, tgtkind, exp): integer cast from
    signed srckind to unsigned ikind is safe wrt its upperbound

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_signed_to_unsigned_cast_ub(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "signed-to-unsigned-cast-ub("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("cus", CPOPredicate)
class CPOUnsignedToSignedCast(CPOPredicate):
    """unsigned-to-signed cast(srckind, tgtkind, exp): integer cast from srckind
    to tgtkind is safe.

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_unsigned_to_signed_cast(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "unsigned-to-signed-cast("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("cuu", CPOPredicate)
class CPOUnsignedToUnsignedCast(CPOPredicate):
    """unsigned-to-unsigned-cast(srckind, tgtkind, exp): integer cast from
    unsigned srckind to unsigned tgtkind is safe.

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_unsigned_to_unsigned_cast(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "unsigned-to-unsigned-cast("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("cssl", CPOPredicate)
class CPOSignedToSignedCastLB(CPOPredicate):
    """signed-to-signed-cast-lb(srckind, tgtkind, exp): integer cast from
    signed srckind to signed tgtkind is safe wrt its lowerbound.

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_signed_to_signed_cast_lb(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "signed-to-signed-cast-lb("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("cssu", CPOPredicate)
class CPOSignedToSignedCastUB(CPOPredicate):
    """signed-to-signed-cast-ub(srckind, tgtkind, exp): integer cast from
    signed srckind to tgtkind is safe wrt to its upperbound.

    - tags[1]: srckind
    - tags[2]: tgtkind

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def srckind(self) -> str:
        return self.tags[1]

    @property
    def tgtkind(self) -> str:
        return self.tags[2]

    @property
    def is_signed_to_signed_cast_ub(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return (
            "signed-to-signed-cast-ub("
            + "from:"
            + self.srckind
            + ", to:"
            + self.tgtkind
            + ", "
            + str(self.exp)
            + ")")


@pdregistry.register_tag("z", CPOPredicate)
class CPONotZero(CPOPredicate):
    """not-zero(exp): exp is not zero

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_not_zero(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "not-zero(" + str(self.exp) + ")"


@pdregistry.register_tag("nneg", CPOPredicate)
class CPONonNegative(CPOPredicate):
    """non-negative(exp): exp is nonnegative (>= 0)

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_non_negative(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "non-negative(" + str(self.exp) + ")"


@pdregistry.register_tag("nt", CPOPredicate)
class CPONullTerminated(CPOPredicate):
    """null-terminated(exp): the string pointed to by exp is null-terminated

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_null_terminated(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "null-terminated(" + str(self.exp) + ")"


@pdregistry.register_tag("iu", CPOPredicate)
class CPOIntUnderflow(CPOPredicate):
    """int-underflow(exp1, exp2, binop): the result of the binary operation
    exp1 binop exp2 does not result in an integer underflow

    - tags[1]: binop
    - tags[2]: ikind

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def ikind(self) -> str:
        return self.tags[2]

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_int_underflow(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "int-underflow("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", ikind: "
            + self.ikind
            + ")")


@pdregistry.register_tag("io", CPOPredicate)
class CPOIntOverflow(CPOPredicate):
    """int-overflow(exp1, exp2, binop): the result of the binary operation
    exp1 binop exp2 does not result in an integer overflow

    - tags[1]: binop
    - tags[2]: ikind

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def ikind(self) -> str:
        return self.tags[2]

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_int_overflow(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "int-overflow("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", ikind: "
            + self.ikind
            + ")")


@pdregistry.register_tag("uiu", CPOPredicate)
class CPOUIntUnderflow(CPOPredicate):
    """uint-underflow(exp1, exp2, binop): the result of the binary operation
    exp1 binop exp2 does not result in an unsigned integer underflow

    Note: this property is kept separate, because it does not lead to undefined
    behavior and can be enabled/disabled as desired.

    - tags[1]: binop
    - tags[2]: ikind

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def ikind(self) -> str:
        return self.tags[2]

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_uint_underflow(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "uint-underflow("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", ikind: "
            + self.ikind
            + ")")


@pdregistry.register_tag("uio", CPOPredicate)
class CPOUIntOverflow(CPOPredicate):
    """uint-overflow(exp1, exp2, binop): the result of the binary operation
    exp1 binop exp2 does not result in an unsigned integer underflow

    Note: this property is kept separate, because it does not lead to undefined
    behavior and can be enabled/disabled as desired.

    - tags[1]: binop
    - tags[2]: ikind

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def ikind(self) -> str:
        return self.tags[2]

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_uint_overflow(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "uint-overflow("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", ikind: "
            + self.ikind
            + ")")


@pdregistry.register_tag("w", CPOPredicate)
class CPOWidthOverflow(CPOPredicate):
    """width-overflow(exp, ikind): the value of the expression fits in an integer
    of ikind.

    - tags[1]: ikind

    - args[0]: exp
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def ikind(self) -> str:
        return self.tags[1]

    @property
    def is_width_overflow(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return ("width-overflow(" + str(self.exp) + ", " + self.ikind + ")")


@pdregistry.register_tag("plb", CPOPredicate)
class CPOPtrLowerBound(CPOPredicate):
    """ptr-lower-bound(exp1, exp2, op, typ): the pointer arithmetic operation
    exp1 op exp2 with resulttype typ does not violate its lower bound.

    - tags[1]: binop

    - args[0]: typ
    - args[1]: exp1
    - args[2]: exp2
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def is_ptr_lower_bound(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "ptr-lower-bound("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", typ: "
            + str(self.typ)
            + ")")


@pdregistry.register_tag("pub", CPOPredicate)
class CPOPtrUpperBound(CPOPredicate):
    """ptr-upper-bound(exp1, exp2, op, typ): the pointer arithmetic operation
    exp1 op exp2 with resulttype typ does not violate its upper bound.

    - tags[1]: binop

    - args[0]: typ
    - args[1]: exp1
    - args[2]: exp2
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def is_ptr_upper_bound(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "ptr-upper-bound("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", typ: "
            + str(self.typ)
            + ")")


@pdregistry.register_tag("pubd", CPOPredicate)
class CPOPtrUpperBoundDeref(CPOPredicate):
    """ptr-upper-bound-deref(exp1, exp2, op, typ): the pointer arithmetic operation
    exp1 op exp2 with resulttype typ does not violate its upper bound.

    - tags[1]: binop

    - args[0]: typ
    - args[1]: exp1
    - args[2]: exp2
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    @property
    def binop(self) -> str:
        return self.tags[1]

    @property
    def is_ptr_upper_bound_deref(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return (
            "ptr-upper-bound-deref("
            + str(self.exp1)
            + ", "
            + str(self.exp2)
            + ", op:"
            + self.binop
            + ", typ: "
            + str(self.typ)
            + ")")


@pdregistry.register_tag("cb", CPOPredicate)
class CPOCommonBase(CPOPredicate):
    """common-base(exp1, exp2): pointer expressions exp1 and exp2 point into the
    same object.

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_common_base(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return ("common-base(" + str(self.exp1) + ", " + str(self.exp2) + ")")


@pdregistry.register_tag("cbt", CPOPredicate)
class CPOCommonBaseType(CPOPredicate):
    """common-base-type(exp1, exp2): pointer expressions exp1 and exp2 point into
    objects with the same type.

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_common_base_type(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return ("common-base-type(" + str(self.exp1) + ", " + str(self.exp2) + ")")


@pdregistry.register_tag("ft", CPOPredicate)
class CPOFormatString(CPOPredicate):
    """format-string(exp): pointer exp points to a format string.

    Note: this property reflects best practices, to ensure that functions that
    expect a format string argument are not invoked with a user-constructed
    string. This property does not directly lead to undefined behavior.

    - args[0]: index exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(int(self.args[0]))

    @property
    def is_format_string(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "format-string(" + str(self.exp) + ")"


@pdregistry.register_tag("va", CPOPredicate)
class CPOVarArgs(CPOPredicate):
    """var-args(fmt, n, args): the number or arguments provided matches the
    number of arguments requested by the format string.

    - args[0]: index of fmt (pointer to format string) in cdictionary
    - args[1]: expected number of arguments
    - args[2]: args:

      - 0: int (expected number of arguments)
      - 1: index of fmt in cdictionary
      - 2..: indices of args in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def fmt(self) -> "CExp":
        return self.cd.get_exp(int(self.args[1]))

    @property
    def argcount(self) -> int:
        return int(self.args[0])

    @property
    def arguments(self) -> List["CExp"]:
        return [self.cd.get_exp(int(x)) for x in self.args[2:]]

    def __str__(self) -> str:
        return (
            "varargs("
            + str(self.fmt)
            + ", n:"
            + str(self.argcount)
            + ", ".join(str(arg) for arg in self.args)
            + ")")


@pdregistry.register_tag("no", CPOPredicate)
class CPONoOverlap(CPOPredicate):
    """no-overlap(exp1, exp2): the objects pointed to by exp1 and exp2 do not
    overlap.

    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp1(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    @property
    def is_no_overlap(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def __str__(self) -> str:
        return ("no-overlap(" + str(self.exp1) + ", " + str(self.exp2) + ")")


@pdregistry.register_tag("vc", CPOPredicate)
class CPOValueConstraint(CPOPredicate):
    """value-constraint(exp): boolean expression exp evaluates to true.

    Note: although most properties could be expressed as value constraints, it
    is preferable to use the dedicated property if available, to better convey
    the origin of the proof obligation (and possibly add additional context
    information)

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_value_constraint(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "value-constraint(" + str(self.exp) + ")"


@pdregistry.register_tag("up", CPOPredicate)
class CPOUniquePointer(CPOPredicate):

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_unique_pointer(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "unique-pointer(" + str(self.exp) + ")"


@pdregistry.register_tag("prm", CPOPredicate)
class CPOPreservedAllMemory(CPOPredicate):
    """preserves-all-memory(): true of a function that does not free any memory.
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def is_preserves_all_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-all-memory()"


@pdregistry.register_tag("pv", CPOPredicate)
class CPOPreservedValue(CPOPredicate):
    """preserves-value(exp): true of a function that preserves the value of exp.

    - args[0]: index of exp in cdictionary
    """

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def __str__(self) -> str:
        return "preserves-value(" + str(self.exp) + ")"


@pdregistry.register_tag("opi", CPOPredicate)
class CPOOutputParameterInitialized(CPOPredicate):
    """

    - args[0]: index of varinfo in cdecls
    """
    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def varinfo(self) -> "CVarInfo":
        return self.cdeclarations.get_varinfo(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    @property
    def is_output_parameter_initialized(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.varinfo.vid == vid

    def __str__(self) -> str:
        return (
            "output_parameter-initialized("
            + str(self.varinfo.vname)
            + ", "
            + str(self.offset)
            + ")")


@pdregistry.register_tag("opu", CPOPredicate)
class CPOOutputParameterUnaltered(CPOPredicate):
    """

    - args[0]: index of varinfo in cdecls
    """
    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def varinfo(self) -> "CVarInfo":
        return self.cdeclarations.get_varinfo(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    @property
    def is_output_parameter_unaltered(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.varinfo.vid == vid

    def __str__(self) -> str:
        return (
            "output_parameter-unaltered("
            + str(self.varinfo.vname)
            + ", "
            + str(self.offset)
            + ")")


@pdregistry.register_tag("opa", CPOPredicate)
class CPOOutputParameterArgument(CPOPredicate):

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    def __str__(self) -> str:
        return "output-parameter-argument(" + str(self.exp) + ")"


@pdregistry.register_tag("ops", CPOPredicate)
class CPOOutputParameterScalar(CPOPredicate):

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def varinfo(self) -> "CVarInfo":
        return self.cdeclarations.get_varinfo(self.args[0])

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def __str__(self) -> str:
        return (
            "output-parameter-scalar("
            + str(self.varinfo) + ", "
            + str(self.exp) + ")")


@pdregistry.register_tag("opne", CPOPredicate)
class CPOOutputParameterNoEscape(CPOPredicate):

    def __init__(
            self, pd: "CFilePredicateDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CPOPredicate.__init__(self, pd, ixval)

    @property
    def varinfo(self) -> "CVarInfo":
        return self.cdeclarations.get_varinfo(self.args[0])

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[1])

    def __str__(self) -> str:
        return (
            "output-parameter-no-escape("
            + str(self.varinfo) + ", "
            + str(self.exp) + ")")
