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

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, cd, ixval)

    def get_iterm(self, argix: int) -> "STerm":
        if len(self.args) >= argix:
            return self.cd.get_s_term(int(self.args[argix]))
        raise Exception(
            "Term index "
            + str(argix)
            + " out of range ("
            + str(len(self.args))
            + " args found)"
        )

    def is_allocation_base(self) -> bool:
        return False

    def is_block_write(self) -> bool:
        return False

    def is_buffer(self) -> bool:
        return False

    def is_confined(self) -> bool:
        return False

    def is_const_term(self) -> bool:
        return False

    def is_controlled_resource(self) -> bool:
        return False

    def is_false(self) -> bool:
        return False

    def is_formatted_input(self) -> bool:
        return False

    def is_freed(self) -> bool:
        return False

    def is_functional(self) -> bool:
        return False

    def is_global_address(self) -> bool:
        return False

    def is_heap_address(self) -> bool:
        return False

    def is_initialized(self) -> bool:
        return False

    def is_initialized_range(self) -> bool:
        return False

    def is_input_formatstring(self) -> bool:
        return False

    def is_invalidated(self) -> bool:
        return False

    def is_new_memory(self) -> bool:
        return False

    def is_no_overlap(self) -> bool:
        return False

    def is_not_zero(self) -> bool:
        return False

    def is_non_negative(self) -> bool:
        return False

    def is_not_null(self) -> bool:
        return False

    def is_null(self) -> bool:
        return False

    def is_null_terminated(self) -> bool:
        return False

    def is_output_formatstring(self) -> bool:
        return False

    def is_preserves_all_memory(self) -> bool:
        return False

    def is_preserves_all_memory_x(self) -> bool:
        return False

    def is_preserves_memory(self) -> bool:
        return False

    def is_preserves_null_termination(self) -> bool:
        return False

    def is_preserves_validity(self) -> bool:
        return False

    def is_preserves_value(self) -> bool:
        return False

    def is_relational_expr(self) -> bool:
        return False

    def is_repositioned(self) -> bool:
        return False

    def is_rev_buffer(self) -> bool:
        return False

    def is_stack_address(self) -> bool:
        return False

    def is_tainted(self) -> bool:
        return False

    def is_unique_pointer(self) -> bool:
        return False

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
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_allocation_base(self) -> bool:
        return True

    def __str__(self) -> str:
        return "allocation-base(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("bw", XPredicate)
class XBlockWrite(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def get_length(self) -> "STerm":
        return self.get_iterm(1)

    def is_block_write(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "block-write(" + str(self.get_term()) + "," + str(self.get_length()) + ")"
        )


@ifdregistry.register_tag("b", XPredicate)
class XBuffer(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_buffer(self) -> "STerm":
        return self.get_iterm(0)

    def get_length(self) -> "STerm":
        return self.get_iterm(1)

    def is_buffer(self) -> bool:
        return True

    def __str__(self) -> str:
        return "buffer(" + str(self.get_buffer()) + "," + str(self.get_length()) + ")"


@ifdregistry.register_tag("rb", XPredicate)
class XRevBuffer(XPredicate):
    """number of bytes before the pointer"""

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_buffer(self) -> "STerm":
        return self.get_iterm(0)

    def get_length(self) -> "STerm":
        return self.get_iterm(1)

    def is_rev_buffer(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "rev-buffer(" + str(self.get_buffer()) + "," + str(self.get_length()) + ")"
        )


@ifdregistry.register_tag("cr", XPredicate)
class XControlledResource(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_size(self) -> "STerm":
        return self.get_iterm(0)

    def get_resource(self) -> str:
        return self.tags[1]

    def is_controlled_resource(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "controlled-resource:"
            + self.get_resource()
            + "("
            + str(self.get_size())
            + ")"
        )


@ifdregistry.register_tag("cf", XPredicate)
class XConfined(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_confined(self) -> bool:
        return True

    def __str__(self) -> str:
        return "confined(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("c", XPredicate)
class XConstTerm(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_const_term(self) -> bool:
        return True

    def __str__(self) -> str:
        return "const-term(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("f", XPredicate)
class XFalse(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

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

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_formatted_input(self) -> bool:
        return True

    def __str__(self) -> str:
        return "formatte-input(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("fr", XPredicate)
class XFreed(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_freed(self) -> bool:
        return True

    def __str__(self) -> str:
        return "freed(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("fn", XPredicate)
class XFunctional(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def is_functional(self) -> bool:
        return True

    def __str__(self) -> str:
        return "functional"


@ifdregistry.register_tag("i", XPredicate)
class XInitialized(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_initialized(self) -> bool:
        return True

    def write_mathml(self, node: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("initialized")
        rnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, rnode])
        node.append(anode)

    def __str__(self) -> str:
        return "initialized(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("ir", XPredicate)
class XInitializedRange(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_buffer(self) -> "STerm":
        return self.get_iterm(0)

    def get_length(self) -> "STerm":
        return self.get_iterm(1)

    def is_initialized_range(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "initialized-range(" + str(self.get_buffer()) + str(self.get_length()) + ")"
        )


@ifdregistry.register_tag("ifs", XPredicate)
class XInputFormatString(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_input_formatstring(self) -> bool:
        return True

    def __str__(self) -> str:
        return "input-formatstring(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("iv", XPredicate)
class XInvalidated(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_invalidated(self) -> bool:
        return True

    def __str__(self) -> str:
        return "invalidated(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("nm", XPredicate)
class XNewMemory(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_new_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "new-memory(" + str(self.get_term())


@ifdregistry.register_tag("ga", XPredicate)
class XGlobalAddress(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_global_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "global-address(" + str(self.get_term())


@ifdregistry.register_tag("ha", XPredicate)
class XHeapAddress(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_heap_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "heap-address(" + str(self.get_term())


@ifdregistry.register_tag("sa", XPredicate)
class XStackAddress(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_stack_address(self) -> bool:
        return True

    def __str__(self) -> str:
        return "stack-address(" + str(self.get_term())


@ifdregistry.register_tag("no", XPredicate)
class XNoOverlap(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term1(self) -> "STerm":
        return self.get_iterm(0)

    def get_term2(self) -> "STerm":
        return self.get_iterm(1)

    def is_no_overlap(self) -> bool:
        return True

    def __str__(self) -> str:
        return "no-overlap(" + str(self.get_term1()) + "," + str(self.get_term2()) + ")"


@ifdregistry.register_tag("nn", XPredicate)
class XNotNull(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_not_null(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("not-null")
        rnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "not-null(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("nng", XPredicate)
class XNonNegative(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_non_negative(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("non-negative")
        rnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "non-negative(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("nz", XPredicate)
class XNotZero(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_not_zero(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element("not-zero")
        rnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, rnode])
        cnode.append(anode)

    def __str__(self) -> str:
        return "not-zero(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("null", XPredicate)
class XNull(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_null(self) -> bool:
        return True

    def __str__(self) -> str:
        return "null(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("nt", XPredicate)
class XNullTerminated(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_null_terminated(self) -> bool:
        return True

    def __str__(self) -> str:
        return "null-terminated(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("ofs", XPredicate)
class XOutputFormatString(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_output_formatstring(self) -> bool:
        return True

    def __str__(self) -> str:
        return "output-formatstring(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("prm", XPredicate)
class XPreservesAllMemory(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def is_preserves_all_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-all-memory"


@ifdregistry.register_tag("prmx", XPredicate)
class XPreservesAllMemoryX(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def is_preserves_all_memory_x(self) -> bool:
        return True

    def get_terms(self) -> List["STerm"]:
        return [self.get_iterm(i) for i in self.args]

    def __str__(self) -> str:
        return (
            "preserves-all-memory-x("
            + ",".join([str(x) for x in self.get_terms()])
            + ")"
        )


@ifdregistry.register_tag("pr", XPredicate)
class XPreservesMemory(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_preserves_memory(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-memory(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("prn", XPredicate)
class XPreservesNullTermination(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_preserves_null_termination(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-null-termination(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("prv", XPredicate)
class XPreservesValidity(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_preserves_validity(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-validity(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("pv", XPredicate)
class XPreservesValue(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_preserves_value(self) -> bool:
        return True

    def __str__(self) -> str:
        return "preserves-value(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("x", XPredicate)
class XRelationalExpr(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_op(self) -> str:
        return self.tags[1]

    def get_term1(self) -> "STerm":
        return self.get_iterm(0)

    def get_term2(self) -> "STerm":
        return self.get_iterm(1)

    def is_relational_expr(self) -> bool:
        return True

    def write_mathml(self, cnode: ET.Element, signature: List[str]) -> None:
        anode = ET.Element("apply")
        opnode = ET.Element(self.get_op())
        anode.append(opnode)
        cnode.append(anode)
        anode.append(self.get_term1().get_mathml_node(signature))
        anode.append(self.get_term2().get_mathml_node(signature))

    def pretty(self) -> str:
        return (
            self.get_term1().pretty()
            + " "
            + get_printop(self.get_op())
            + " "
            + self.get_term2().pretty()
        )

    def __str__(self) -> str:
        return (
            "expr("
            + self.get_op()
            + " "
            + str(self.get_term1())
            + ","
            + str(self.get_term2())
            + ")"
        )


@ifdregistry.register_tag("rep", XPredicate)
class XRepositioned(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_repositioned(self) -> bool:
        return True

    def __str__(self) -> str:
        return "repositioned(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("tt", XPredicate)
class XTainted(XPredicate):
    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def get_lower_bound(self) -> Optional["STerm"]:
        if (int(self.args[1])) > 0:
            return self.get_iterm(1)
        return None

    def get_upper_bound(self) -> Optional["STerm"]:
        if (int(self.args[2])) > 0:
            return self.get_iterm(2)
        return None

    def is_tainted(self) -> bool:
        return True

    def __str__(self) -> str:
        lb = self.get_lower_bound()
        ub = self.get_upper_bound()
        slb = "" if lb is None else " LB:" + str(lb)
        sub = "" if ub is None else " UB:" + str(ub)
        return "tainted(" + str(self.get_term()) + ")" + slb + sub


@ifdregistry.register_tag("up", XPredicate)
class XUniquePointer(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_unique_pointer(self) -> bool:
        return True

    def __str__(self) -> str:
        return "unique-pointer(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("vm", XPredicate)
class XValidMem(XPredicate):

    def __init__(
            self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        XPredicate.__init__(self, cd, ixval)

    def get_term(self) -> "STerm":
        return self.get_iterm(0)

    def is_valid_mem(self) -> bool:
        return True

    def __str__(self) -> str:
        return "valid-mem(" + str(self.get_term()) + ")"
