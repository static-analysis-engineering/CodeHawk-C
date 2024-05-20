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
"""Object representation of sum type xpredicate_t.

Object representation of the corresponding OCaml sumtype: xpredicate_t: a
predicate over s_term_t terms (terms that are visible outside of a function).

The properties of an xpredicate are constructed from its indexed value in the
InterfaceDictionary

"""

from typing import cast, List, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

from chc.api.InterfaceDictionaryRecord import (
    InterfaceDictionaryRecord, ifdregistry)

import chc.util.IndexedTable as IT

printops = {"eq": "=", "lt": "<", "gt": ">", "ge": ">=", "le": "<="}

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.STerm import STerm


def get_printop(s: str) -> str:
    if s in printops:
        return printops[s]
    else:
        return s


class XPredicate(InterfaceDictionaryRecord):
    """Base class of external predicate."""

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, ifd, ixval)

    def get_iterm(self, argix: int) -> "STerm":
        if len(self.args) >= argix:
            return self.ifd.get_s_term(int(self.args[argix]))
        raise Exception(
            "Term index "
            + str(argix)
            + " out of range ("
            + str(len(self.args))
            + " args found)"
        )

    @property
    def is_allocation_base(self) -> bool:
        return False

    @property
    def is_block_write(self) -> bool:
        return False

    @property
    def is_buffer(self) -> bool:
        return False

    @property
    def is_confined(self) -> bool:
        return False

    @property
    def is_const_term(self) -> bool:
        return False

    @property
    def is_controlled_resource(self) -> bool:
        return False

    @property
    def is_false(self) -> bool:
        return False

    @property
    def is_formatted_input(self) -> bool:
        return False

    @property
    def is_freed(self) -> bool:
        return False

    @property
    def is_functional(self) -> bool:
        return False

    @property
    def is_global_address(self) -> bool:
        return False

    @property
    def is_heap_address(self) -> bool:
        return False

    @property
    def is_initialized(self) -> bool:
        return False

    @property
    def is_initialized_range(self) -> bool:
        return False

    @property
    def is_input_formatstring(self) -> bool:
        return False

    @property
    def is_invalidated(self) -> bool:
        return False

    @property
    def is_new_memory(self) -> bool:
        return False

    @property
    def is_no_overlap(self) -> bool:
        return False

    @property
    def is_not_zero(self) -> bool:
        return False

    @property
    def is_non_negative(self) -> bool:
        return False

    @property
    def is_not_null(self) -> bool:
        return False

    @property
    def is_null(self) -> bool:
        return False

    @property
    def is_null_terminated(self) -> bool:
        return False

    @property
    def is_output_formatstring(self) -> bool:
        return False

    @property
    def is_preserves_all_memory(self) -> bool:
        return False

    @property
    def is_preserves_all_memory_x(self) -> bool:
        return False

    @property
    def is_preserves_memory(self) -> bool:
        return False

    @property
    def is_preserves_null_termination(self) -> bool:
        return False

    @property
    def is_preserves_validity(self) -> bool:
        return False

    @property
    def is_preserves_value(self) -> bool:
        return False

    @property
    def is_relational_expr(self) -> bool:
        return False

    @property
    def is_repositioned(self) -> bool:
        return False

    @property
    def is_rev_buffer(self) -> bool:
        return False

    @property
    def is_stack_address(self) -> bool:
        return False

    @property
    def is_tainted(self) -> bool:
        return False

    @property
    def is_unique_pointer(self) -> bool:
        return False

    @property
    def is_valid_mem(self) -> bool:
        return False

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        raise Exception("Missing write_mathml for " + self.tags[0])

    def pretty(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "xpredicate: " + self.tags[0]


@ifdregistry.register_tag("ab", XPredicate)
class XAllocationBase(XPredicate):
    """Term points to start of allocated region that can be freed.

    * args[0]: index of term in interface dictionary
    """
    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_allocation_base(self) -> bool:
        return True

    def __str__(self) -> str:
        return "allocation-base(" + str(self.term) + ")"


@ifdregistry.register_tag("bw", XPredicate)
class XBlockWrite(XPredicate):
    """Unstructured write of bytes to pointed address with given length.

    * args[0]: index of address term in interface dictionary
    * args[1]: index of length term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def length(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_block_write(self) -> bool:
        return True

    def __str__(self) -> str:
        return "block-write(" + str(self.term) + "," + str(self.length) + ")"


@ifdregistry.register_tag("b", XPredicate)
class XBuffer(XPredicate):
    """Term points to a buffer with at least a given number of bytes.

    * args[0]: index of pointer to buffer in interface dictionary
    * args[1]: index of size term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def buffer(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def length(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_buffer(self) -> bool:
        return True

    def __str__(self) -> str:
        return "buffer(" + str(self.buffer) + "," + str(self.length) + ")"


@ifdregistry.register_tag("rb", XPredicate)
class XRevBuffer(XPredicate):
    """Term points to buffer with at least given number of bytes before the pointer

    args[0]: index of buffer-term in interface dictionary
    args[1]: index of length term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def buffer(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def length(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_rev_buffer(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "rev-buffer(" + str(self.buffer) + "," + str(self.length) + ")"
        )


@ifdregistry.register_tag("cr", XPredicate)
class XControlledResource(XPredicate):
    """Term is not / must not be tainted.

    * tags[1]: name of resource
    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def size(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def resource(self) -> str:
        return self.tags[1]

    @property
    def is_controlled_resource(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "controlled-resource:"
            + self.resource
            + "("
            + str(self.size)
            + ")"
        )


@ifdregistry.register_tag("cf", XPredicate)
class XConfined(XPredicate):
    """Pointer expression that is out of scope without leaking references.

    args[0]: index of pointer term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_confined(self) -> bool:
        return True

    def __str__(self) -> str:
        return "confined(" + str(self.term) + ")"


@ifdregistry.register_tag("c", XPredicate)
class XConstTerm(XPredicate):
    """Pointed-to term is not modified.

    args[0]: index of pointed-to term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_const_term(self) -> bool:
        return True

    def __str__(self) -> str:
        return "const-term(" + str(self.term) + ")"


@ifdregistry.register_tag("f", XPredicate)
class XFalse(XPredicate):
    """Property is always false."""

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def is_false(self) -> bool:
        return True

    def write_mathml(self, node: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("false")
        anode.append(opnode)
        node.append(anode)

    def __str__(self) -> str:
        return "FALSE"


@ifdregistry.register_tag("fi", XPredicate)
class XFormattedInput(XPredicate):
    """Term is a format string.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_formatted_input(self) -> bool:
        return True

    def __str__(self) -> str:
        return "formatted-input(" + str(self.term) + ")"


@ifdregistry.register_tag("fr", XPredicate)
class XFreed(XPredicate):
    """Term pointed to is freed.

    * args[0]: index of term in interface dictionary.
    """
    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_freed(self) -> bool:
        return True

    def __str__(self) -> str:
        return "freed(" + str(self.term) + ")"


@ifdregistry.register_tag("fn", XPredicate)
class XFunctional(XPredicate):
    """Function has no observable side-effects."""

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def is_functional(self) -> bool:
        return True

    def __str__(self) -> str:
        return "functional"


@ifdregistry.register_tag("i", XPredicate)
class XInitialized(XPredicate):
    """Lval denoted is initialized.

    args[0]: index of lval term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_initialized(self) -> bool:
        return True

    def write_mathml(self, node: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("initialized")
        rnode = self.term.get_mathml_node(signature)
        anode.extend([opnode, rnode])
        node.append(anode)

    def __str__(self) -> str:
        return "initialized(" + str(self.term) + ")"


@ifdregistry.register_tag("ir", XPredicate)
class XInitializedRange(XPredicate):
    """Term pointed to is initialized for the given length (in bytes).

    * args[0]: index of buffer pointed-to term in interface dictionary
    * args[1]: index of length term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def buffer(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def length(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_initialized_range(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "initialized-range(" + str(self.buffer) + str(self.length) + ")"
        )


@ifdregistry.register_tag("ifs", XPredicate)
class XInputFormatString(XPredicate):
    """Term points to scanf format string.

    * args[0]: index of format-string term in interface dictionary.
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_input_formatstring(self) -> bool:
        return True

    def __str__(self) -> str:
        return "input-formatstring(" + str(self.term) + ")"


@ifdregistry.register_tag("iv", XPredicate)
class XInvalidated(XPredicate):
    """Term pointed to may not be valid any more.

    * args[0]: index of pointed-to term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_invalidated(self) -> bool:
        return True

    def __str__(self) -> str:
        return "invalidated(" + str(self.term) + ")"


@ifdregistry.register_tag("nm", XPredicate)
class XNewMemory(XPredicate):
    """Term points to newly allocated memory (stack or heap).

    Specifically, memory that is newly allocated since the start of the function.

    * args[0]: index of term pointing to new memory in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_new_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "new-memory(" + str(self.term)


@ifdregistry.register_tag("ga", XPredicate)
class XGlobalAddress(XPredicate):
    """Term points to global memory.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_global_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "global-address(" + str(self.term)


@ifdregistry.register_tag("ha", XPredicate)
class XHeapAddress(XPredicate):
    """Term points to heap memory.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_heap_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "heap-address(" + str(self.term)


@ifdregistry.register_tag("sa", XPredicate)
class XStackAddress(XPredicate):
    """Term points to stack memory.

    args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_stack_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "stack-address(" + str(self.term)


@ifdregistry.register_tag("no", XPredicate)
class XNoOverlap(XPredicate):
    """The two pointed-to memory regions do not overlap.

    args[0]: index of first term in interface dictionary
    args[1]: index of second term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term1(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def term2(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_no_overlap(self) -> bool:
        return True

    def __str__(self) -> str:
        return "no-overlap(" + str(self.term1) + "," + str(self.term2) + ")"


@ifdregistry.register_tag("nn", XPredicate)
class XNotNull(XPredicate):
    """Term is not null.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_not_null(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("not-null")
        rnode = self.term.get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "not-null(" + str(self.term) + ")"


@ifdregistry.register_tag("nng", XPredicate)
class XNonNegative(XPredicate):
    """Term is non-negative.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_non_negative(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("non-negative")
        rnode = self.term.get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "non-negative(" + str(self.term) + ")"


@ifdregistry.register_tag("nz", XPredicate)
class XNotZero(XPredicate):
    """Term is not zero.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_not_zero(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("not-zero")
        rnode = self.term.get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "not-zero(" + str(self.term) + ")"


@ifdregistry.register_tag("null", XPredicate)
class XNull(XPredicate):
    """Term is null.

    args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_null(self) -> bool:
        return True

    def __str__(self) -> str:
        return "null(" + str(self.term) + ")"


@ifdregistry.register_tag("nt", XPredicate)
class XNullTerminated(XPredicate):
    """Term is null-terminated.

    * args[0]: index of interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_null_terminated(self) -> bool:
        return True

    def __str__(self) -> str:
        return "null-terminated(" + str(self.term) + ")"


@ifdregistry.register_tag("ofs", XPredicate)
class XOutputFormatString(XPredicate):
    """Term points to printf-style format string.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_output_formatstring(self) -> bool:
        return True

    def __str__(self) -> str:
        return "output-formatstring(" + str(self.term) + ")"


@ifdregistry.register_tag("prm", XPredicate)
class XPreservesAllMemory(XPredicate):
    """Function does not free any external memory."""

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def is_preserves_all_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-all-memory"


@ifdregistry.register_tag("prmx", XPredicate)
class XPreservesAllMemoryX(XPredicate):
    """Function does not free any external memory except for given terms.

    * args[0..]: indices of terms in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def is_preserves_all_memory_x(self) -> bool:
        return True

    @property
    def terms(self) -> List["STerm"]:
        return [self.get_iterm(i) for i in self.args]

    def __str__(self) -> str:
        return (
            "preserves-all-memory-x("
            + ",".join([str(x) for x in self.terms])
            + ")"
        )


@ifdregistry.register_tag("pr", XPredicate)
class XPreservesMemory(XPredicate):
    """Function does not free pointed-to memory.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_preserves_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-memory(" + str(self.term) + ")"


@ifdregistry.register_tag("prn", XPredicate)
class XPreservesNullTermination(XPredicate):
    """Function does not strip null-terminating byte from string pointed-to

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_preserves_null_termination(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-null-termination(" + str(self.term) + ")"


@ifdregistry.register_tag("prv", XPredicate)
class XPreservesValidity(XPredicate):
    """Validity of pointed-to resources is maintained.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_preserves_validity(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-validity(" + str(self.term) + ")"


@ifdregistry.register_tag("pv", XPredicate)
class XPreservesValue(XPredicate):
    """Function does not modify the value of the term.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_preserves_value(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-value(" + str(self.term) + ")"


@ifdregistry.register_tag("x", XPredicate)
class XRelationalExpr(XPredicate):
    """Relational expression of terms.

    * tags[1]: operator
    * args[0]: index of first term in interface dictionary
    * args[1]: index of second term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def op(self) -> str:
        return self.tags[1]

    @property
    def term1(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def term2(self) -> "STerm":
        return self.get_iterm(1)

    @property
    def is_relational_expr(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element(self.op)
        anode.append(opnode)
        cnode.append(anode)
        anode.append(self.term1.get_mathml_node(signature))
        anode.append(self.term2.get_mathml_node(signature))

    def pretty(self) -> str:
        return (
            self.term1.pretty()
            + " "
            + get_printop(self.op)
            + " "
            + self.term2.pretty()
        )

    def __str__(self) -> str:
        return (
            "expr("
            + self.op
            + " "
            + str(self.term1)
            + ","
            + str(self.term2)
            + ")"
        )


@ifdregistry.register_tag("rep", XPredicate)
class XRepositioned(XPredicate):
    """Term pointed to may be freed and reassigned.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_repositioned(self) -> bool:
        return True

    def __str__(self) -> str:
        return "repositioned(" + str(self.term) + ")"


@ifdregistry.register_tag("tt", XPredicate)
class XTainted(XPredicate):
    """Value of term is externally controlled with optional upper/lower bound.

    * args[0]: index of term in interface dictionary
    * args[1]: index of lower bound in interface dictionary (optional)
    * args[2]: index of upper bound in interface dictionary (optional)
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def lower_bound(self) -> Optional["STerm"]:
        if (int(self.args[1])) > 0:
            return self.get_iterm(1)
        return None

    @property
    def upper_bound(self) -> Optional["STerm"]:
        if (int(self.args[2])) > 0:
            return self.get_iterm(2)
        return None

    @property
    def is_tainted(self) -> bool:
        return True

    def __str__(self) -> str:
        lb = self.lower_bound
        ub = self.upper_bound
        slb = "" if lb is None else " LB:" + str(lb)
        sub = "" if ub is None else " UB:" + str(ub)
        return "tainted(" + str(self.term) + ")" + slb + sub


@ifdregistry.register_tag("up", XPredicate)
class XUniquePointer(XPredicate):
    """Term is the only pointer pointing at resource.

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_unique_pointer(self) -> bool:
        return True

    def __str__(self) -> str:
        return "unique-pointer(" + str(self.term) + ")"


@ifdregistry.register_tag("vm", XPredicate)
class XValidMem(XPredicate):
    """Pointed-to memory has not been freed (at time of delivery).

    * args[0]: index of term in interface dictionary
    """

    def __init__(
            self, ifd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, ifd, ixval)

    @property
    def term(self) -> "STerm":
        return self.get_iterm(0)

    @property
    def is_valid_mem(self) -> bool:
        return True

    def __str__(self) -> str:
        return "valid-mem(" + str(self.term) + ")"
