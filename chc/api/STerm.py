# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2023 Henny Sipma
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

from typing import Dict, List, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

from chc.api.InterfaceDictionaryRecord import (
    InterfaceDictionaryRecord, ifdregistry)

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.api.ApiParameter import ApiParameter


printops: Dict[str, str] = {
    "plus": "+",
    "plusa": "+",
    "minnus": "-",
    "times": "*",
    "mult": "*",
    "divide": "/",
    "div": "/",
}


def get_printop(s: str) -> str:
    if s in printops:
        return printops[s]
    else:
        return s


class SOffset(InterfaceDictionaryRecord):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, cd, ixval)

    def is_nooffset(self) -> bool:
        return False

    def is_field_offset(self) -> bool:
        return False

    def is_index_offset(self) -> bool:
        return False

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        raise Exception("Should be implemented by a subclass")

    def __str__(self) -> str:
        return "s-offset-" + self.tags[0]


@ifdregistry.register_tag("no", SOffset)
class STArgNoOffset(SOffset):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        SOffset.__init__(self, cd, ixval)

    def is_nooffset(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        return None

    def __str__(self) -> str:
        return ""


@ifdregistry.register_tag("fo", SOffset)
class STArgFieldOffset(SOffset):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        SOffset.__init__(self, cd, ixval)

    def get_field(self) -> str:
        return self.tags[1]

    def get_offset(self) -> SOffset:
        return self.cd.get_s_offset(int(self.args[0]))

    def is_field_offset(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        fnode = ET.Element("field")
        fnode.set("name", self.get_field())
        offnode = self.get_offset().get_mathml_node(signature)
        if offnode is not None:
            fnode.append(offnode)
        return fnode

    def __str__(self) -> str:
        return "." + self.get_field() + str(self.get_offset())


@ifdregistry.register_tag("io", SOffset)
class STArgIndexOffset(SOffset):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        SOffset.__init__(self, cd, ixval)

    def get_index(self) -> int:
        return int(self.tags[1])

    def get_offset(self) -> SOffset:
        return self.cd.get_s_offset(int(self.args[0]))

    def is_index_offset(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> Optional[ET.Element]:
        inode = ET.Element("index")
        inode.set("i", str(self.get_index()))
        offnode = self.get_offset().get_mathml_node(signature)
        if offnode is not None:
            inode.append(offnode)
        return inode

    def __str__(self) -> str:
        return "[" + str(self.get_index()) + "]" + str(self.get_offset())


class STerm(InterfaceDictionaryRecord):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, cd, ixval)

    def get_iterm(self, argix: int) -> "STerm":
        return self.cd.get_s_term(int(self.args[argix]))

    def is_arg_value(self) -> bool:
        return False

    def is_return_value(self) -> bool:
        return False

    def is_named_constant(self) -> bool:
        return False

    def is_num_constant(self) -> bool:
        return False

    def is_index_size(self) -> bool:
        return False

    def is_byte_size(self) -> bool:
        return False

    def is_field_offset(self) -> bool:
        return False

    def is_arg_addressed_value(self) -> bool:
        return False

    def is_arg_null_terminator_pos(self) -> bool:
        return False

    def is_arg_size_of_type(self) -> bool:
        return False

    def is_arithmetic_expr(self) -> bool:
        return False

    def is_formatted_output_size(self) -> bool:
        return False

    def is_runtime_value(self) -> bool:
        return False

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        return ET.Element("s-term")

    def pretty(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "s-term-" + self.tags[0]


@ifdregistry.register_tag("av", STerm)
class STArgValue(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_parameter(self) -> "ApiParameter":
        return self.cd.get_api_parameter(int(self.args[0]))

    def get_offset(self) -> SOffset:
        return self.cd.get_s_offset(int(self.args[1]))

    def is_arg_value(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        node = ET.Element("ci")
        node.text = signature[self.args[0]]
        return node

    def __str__(self) -> str:
        return "arg-val(" + str(self.get_parameter()) + ")"


@ifdregistry.register_tag("rv", STerm)
class STReturnValue(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def is_return_value(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        return ET.Element("return")

    def __str__(self) -> str:
        return "returnval"


@ifdregistry.register_tag("nc", STerm)
class STNamedConstant(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_name(self) -> str:
        return self.tags[1]

    def is_named_constant(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        node = ET.Element("ci")
        node.text = self.get_name()
        return node

    def __str__(self) -> str:
        return "named-constant(" + self.get_name() + ")"


@ifdregistry.register_tag("ic", STerm)
class STNumConstant(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_constant(self) -> int:
        try:
            return int(self.tags[1])
        except ValueError as e:
            raise UF.CHCError(str(e))

    def is_num_constant(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        node = ET.Element("cn")
        node.text = str(self.get_constant())
        return node

    def pretty(self) -> str:
        return str(self.get_constant())

    def __str__(self) -> str:
        return "num-constant(" + str(self.get_constant()) + ")"


@ifdregistry.register_tag("is", STerm)
class STIndexSize(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_term(self) -> STerm:
        return self.get_iterm(0)

    def is_index_size(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("index-size")
        tnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, tnode])
        return anode

    def __str__(self) -> str:
        return "index-size(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("bs", STerm)
class STByteSize(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_term(self) -> STerm:
        return self.get_iterm(0)

    def is_byte_size(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("byte-size")
        tnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, tnode])
        return anode

    def __str__(self) -> str:
        return "byte-size(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("fo", STerm)
class STFieldOffset(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_name(self) -> str:
        return self.tags[1]

    def is_field_offset(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        node = ET.Element("field")
        node.set("fname", self.get_name())
        return node

    def __str__(self) -> str:
        return "field-offset(" + str(self.get_name()) + ")"


@ifdregistry.register_tag("aa", STerm)
class STArgAddressedValue(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_base_term(self) -> STerm:
        return self.get_iterm(0)

    def get_offset(self) -> SOffset:
        return self.cd.get_s_offset(int(self.args[1]))

    def is_arg_addressed_value(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("addressed-value")
        t1node = self.get_base_term().get_mathml_node(signature)
        offnode = self.get_offset().get_mathml_node(signature)
        if offnode is not None:
            t1node.append(offnode)
        anode.extend([opnode, t1node])
        return anode

    def __str__(self) -> str:
        return (
            "addressed-value("
            + str(self.get_base_term())
            + ")"
            + str(self.get_offset())
        )


@ifdregistry.register_tag("at", STerm)
class STArgNullTerminatorPos(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_term(self) -> STerm:
        return self.get_iterm(0)

    def is_arg_null_terminator_pos(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("nullterminator-pos")
        tnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, tnode])
        return anode

    def __str__(self) -> str:
        return "arg-null-terminator-pos(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("st", STerm)
class STArgSizeOfType(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_term(self) -> STerm:
        return self.get_iterm(0)

    def is_arg_size_of_type(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("size-of-type")
        tnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, tnode])
        return anode

    def __str__(self) -> str:
        return "arg-size-of-type(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("ax", STerm)
class STArithmeticExpr(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_op(self) -> str:
        return self.tags[1]

    def get_term1(self) -> STerm:
        return self.get_iterm(0)

    def get_term2(self) -> STerm:
        return self.get_iterm(1)

    def is_arithmetic_expr(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element(self.get_op())
        t1node = self.get_term1().get_mathml_node(signature)
        t2node = self.get_term2().get_mathml_node(signature)
        anode.extend([opnode, t1node, t2node])
        return anode

    def pretty(self) -> str:
        return (
            "("
            + self.get_term1().pretty()
            + " "
            + get_printop(self.get_op())
            + " "
            + self.get_term2().pretty()
            + ")"
        )

    def __str__(self) -> str:
        return (
            "xpr("
            + str(self.get_term1())
            + " "
            + self.get_op()
            + " "
            + str(self.get_term2())
            + ")"
        )


@ifdregistry.register_tag("fs", STerm)
class STFormattedOutputSize(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def get_term(self) -> STerm:
        return self.get_iterm(0)

    def is_formatted_output_size(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        anode = ET.Element("apply")
        opnode = ET.Element("formatted-output-size")
        tnode = self.get_term().get_mathml_node(signature)
        anode.extend([opnode, tnode])
        return anode

    def __str__(self) -> str:
        return "formatted-output-size(" + str(self.get_term()) + ")"


@ifdregistry.register_tag("rt", STerm)
class STRuntimeValue(STerm):
    def __init__(
        self,
        cd: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        STerm.__init__(self, cd, ixval)

    def is_runtime_value(self) -> bool:
        return True

    def get_mathml_node(self, signature: List[str]) -> ET.Element:
        return ET.Element("runtime-value")

    def __str__(self) -> str:
        return "runtime-value"
