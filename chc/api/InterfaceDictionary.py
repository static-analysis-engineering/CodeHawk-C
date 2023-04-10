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

from typing import Any, cast, Callable, Dict, List, Tuple, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.IndexedTable import (
    IndexedTable,
    IndexedTableValue,
    IndexedTableSuperclass,
)

import chc.api.ApiParameter as AP
from chc.api.ApiParameter import ApiParameter, APFormal, APGlobal

from chc.api.InterfaceDictionaryRecord import InterfaceDictionaryRecord, ifdregistry

import chc.api.GlobalAssumption as GA
import chc.api.PostRequest as PR
from chc.api.PostRequest import PostRequest
import chc.api.PostAssume as PA
from chc.api.PostAssume import PostAssume
import chc.api.STerm as ST
from chc.api.STerm import (
    SOffset,
    STerm,
    STArgNoOffset,
    STArgFieldOffset,
    STArgIndexOffset,
)
import chc.api.XPredicate as XP
from chc.api.XPredicate import XPredicate

if TYPE_CHECKING:
    from chc.app.CFile import CFile

macroconstants = {
    "MININT8": "-128",
    "MAXINT8": "127",
    "MAXUINT8": "255",
    "MININT16": "-32768",
    "MAXINT16": "32767",
    "MAXUINT16": "65535",
    "MININT32": "-2147483648",
    "MAXINT32": "2147483647",
    "MAXUINT32": "4294967295",
    "MININT64": "-9223372036854775808",
    "MAXINT64": "9223372036854775807",
    "MAXUINT64": "18446744073709551615",
}


class InterfaceDictionary(object):
    """Function interface constructs."""

    def __init__(self, cfile: "CFile", xnode: ET.Element):
        self.cfile = cfile
        self.declarations = self.cfile.declarations
        self.dictionary = self.declarations.dictionary
        self.api_parameter_table = IndexedTable("api-parameter-table")
        self.s_offset_table = IndexedTable("s-offset-table")
        self.s_term_table = IndexedTable("s-term-table")
        self.xpredicate_table = IndexedTable("xpredicate-table")
        self.postrequest_table = IndexedTable("postrequest-table")
        self.postassume_table = IndexedTable("postassume-table")
        self.ds_condition_table = IndexedTable("ds-condition-table")
        self.tables: List[IndexedTable] = [
            self.api_parameter_table,
            self.s_offset_table,
            self.s_term_table,
            self.xpredicate_table,
            self.postrequest_table,
            self.postassume_table,
            self.ds_condition_table
        ]
        self.initialize(xnode)

    # ----------------- Retrieve items from dictionary tables ----------------

    def get_api_parameter(self, ix: int) -> ApiParameter:
        return ifdregistry.mk_instance(
            self, self.api_parameter_table.retrieve(ix), ApiParameter)

    def get_s_offset(self, ix: int) -> SOffset:
        return ifdregistry.mk_instance(
            self, self.s_offset_table.retrieve(ix), SOffset)

    def get_s_term(self, ix: int) -> STerm:
        return ifdregistry.mk_instance(
            self, self.s_term_table.retrieve(ix), STerm)

    def get_xpredicate(self, ix: int) -> XPredicate:
        return ifdregistry.mk_instance(
            self, self.xpredicate_table.retrieve(ix), XPredicate)

    def get_postrequest(self, ix: int) -> PostRequest:
        return ifdregistry.mk_instance(
            self, self.postrequest_table.retrieve(ix), PostRequest)

    # --------------------- Index items by category --------------------------

    def index_api_parameter(self, p: ApiParameter) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> ApiParameter:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, ApiParameter)

        return self.api_parameter_table.add_tags_args(p.tags, p.args, f)

    def mk_api_parameter(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> ApiParameter:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, ApiParameter)

        return self.api_parameter_table.add_tags_args(tags, args, f)

    def mk_formal_api_parameter(self, n: int) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pf"], [n]))

    def mk_global_api_parameter(self, g: str) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pg", g], []))

    def index_s_offset(self, t: SOffset) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> SOffset:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, SOffset)

        if t.is_field_offset():
            args = [self.index_s_offset(cast(STArgFieldOffset, t).get_offset())]
        elif t.is_index_offset():
            args = [self.index_s_offset(cast(STArgIndexOffset, t).get_offset())]
        else:
            args = t.args

        return self.s_offset_table.add_tags_args(t.tags, args, f)

    def mk_s_offset(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> SOffset:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, SOffset)

        return self.s_offset_table.add_tags_args(tags, args, f)

    def mk_arg_no_offset(self) -> SOffset:
        return self.get_s_offset(self.mk_s_offset(["no"], []))

    def index_s_term(self, t: STerm) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> STerm:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, STerm)

        if t.is_arg_value():
            args = [
                self.index_api_parameter(cast(ST.STArgValue, t).get_parameter()),
                self.index_s_offset(cast(ST.STArgValue, t).get_offset()),
            ]
        elif t.is_index_size():
            args = [self.index_s_term(cast(ST.STIndexSize, t).get_term())]
        elif t.is_byte_size():
            args = [self.index_s_term(cast(ST.STByteSize, t).get_term())]
        elif t.is_arg_addressed_value():
            args = [
                self.index_s_term(cast(ST.STArgAddressedValue, t).get_base_term()),
                self.index_s_offset(cast(ST.STArgAddressedValue, t).get_offset()),
            ]
        elif t.is_arg_null_terminator_pos():
            args = [self.index_s_term(cast(ST.STArgNullTerminatorPos, t).get_term())]
        elif t.is_arg_size_of_type():
            args = [self.index_s_term(cast(ST.STArgSizeOfType, t).get_term())]
        elif t.is_formatted_output_size():
            args = [self.index_s_term(cast(ST.STFormattedOutputSize, t).get_term())]
        elif t.is_arithmetic_expr():
            t_arith = cast(ST.STArithmeticExpr, t)
            args = [
                self.index_s_term(t_arith.get_term1()),
                self.index_s_term(t_arith.get_term2()),
            ]
        else:
            args = t.args

        return self.s_term_table.add_tags_args(t.tags, args, f)

    def index_opt_s_term(self, t: Optional[STerm]) -> int:
        if t is None:
            return -1
        else:
            return self.index_s_term(t)

    def mk_s_term(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> STerm:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, STerm)
            # return s_term_constructors[tags[0]]((self, index, tags, args))

        return self.s_term_table.add_tags_args(tags, args, f)

    def mk_field_s_term(self, fieldname: str) -> STerm:
        index = self.mk_s_term(["fo", fieldname], [])
        return self.get_s_term(index)

    def mk_xpredicate(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> XPredicate:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, XPredicate)

        return self.xpredicate_table.add_tags_args(tags, args, f)

    def mk_initialized_xpredicate(self, t: STerm) -> XPredicate:
        index = self.mk_xpredicate(["i"], [self.index_s_term(t)])
        return self.get_xpredicate(index)

    def index_xpredicate(self, p: XPredicate) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> XPredicate:
            itv = IT.IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, XPredicate)

        if p.is_new_memory():
            args = [self.index_s_term(cast(XP.XNewMemory, p).get_term())]

        elif p.is_heap_address():
            args = [self.index_s_term(cast(XP.XHeapAddress, p).get_term())]

        elif p.is_global_address():
            args = [self.index_s_term(cast(XP.XGlobalAddress, p).get_term())]

        elif p.is_stack_address():
            args = p.args

        elif p.is_allocation_base():
            args = [self.index_s_term(cast(XP.XAllocationBase, p).get_term())]

        elif p.is_block_write():
            bw = cast(XP.XBlockWrite, p)
            args = [
                self.index_s_term(bw.get_term()),
                self.index_s_term(bw.get_length()),
            ]

        elif p.is_null():
            args = [self.index_s_term(cast(XP.XNull, p).get_term())]

        elif p.is_not_null():
            args = [self.index_s_term(cast(XP.XNotNull, p).get_term())]

        elif p.is_not_zero():
            args = [self.index_s_term(cast(XP.XNotZero, p).get_term())]

        elif p.is_non_negative():
            args = [self.index_s_term(cast(XP.XNonNegative, p).get_term())]

        elif p.is_initialized():
            args = [self.index_s_term(cast(XP.XInitialized, p).get_term())]

        elif p.is_initialized_range():
            args = [
                self.index_s_term(cast(XP.XInitializedRange, p).get_buffer()),
                self.index_s_term(cast(XP.XInitializedRange, p).get_length()),
            ]

        elif p.is_null_terminated():
            args = [self.index_s_term(cast(XP.XNullTerminated, p).get_term())]

        elif p.is_false():
            args = p.args

        elif p.is_relational_expr():
            re = cast(XP.XRelationalExpr, p)
            args = [
                self.index_s_term(re.get_term1()),
                self.index_s_term(re.get_term2()),
            ]

        elif p.is_preserves_all_memory():
            args = p.args

        elif p.is_tainted():
            args = [
                self.index_s_term(cast(XP.XTainted, p).get_term()),
                self.index_opt_s_term(cast(XP.XTainted, p).get_lower_bound()),
                self.index_opt_s_term(cast(XP.XTainted, p).get_upper_bound()),
            ]

        elif p.is_buffer():
            args = [
                self.index_s_term(cast(XP.XBuffer, p).get_buffer()),
                self.index_s_term(cast(XP.XBuffer, p).get_length()),
            ]

        elif p.is_rev_buffer():
            args = [
                self.index_s_term(cast(XP.XRevBuffer, p).get_buffer()),
                self.index_s_term(cast(XP.XRevBuffer, p).get_length()),
            ]

        elif p.is_controlled_resource():
            args = [self.index_s_term(cast(XP.XControlledResource, p).get_size())]

        else:
            args = p.args

        return self.xpredicate_table.add_tags_args(p.tags, args, f)

    def parse_mathml_api_parameter(
        self, name: str, pars: Dict[str, int], gvars: List[str] = []
    ) -> int:
        if (name not in pars) and (name not in gvars):
            raise Exception("Error in reading user data: " + name + " in file " + self.cfile.name)
        if name in pars:
            tags = ["pf"]
            args = [pars[name]]
        elif name in gvars:
            tags = ["pg", name]
            args = []
        else:
            raise Exception(
                "Api parameter name "
                + name
                + " not found in parameters or global variables"
            )
        return self.mk_api_parameter(tags, args)

    def parse_mathml_offset(self, tnode: Optional[ET.Element]) -> int:
        if tnode is None:
            return self.mk_s_offset(["no"], [])

        elif tnode.tag == "field":
            offsetnode = tnode[0] if len(tnode) > 0 else None
            xml_name = tnode.get("name")
            if xml_name is None:
                raise Exception('missing attribute "name"')
            tags = ["fo", xml_name]
            args = [self.parse_mathml_offset(offsetnode)]
            return self.mk_s_offset(tags, args)

        elif tnode.tag == "index":
            offsetnode = tnode[0] if len(tnode) > 0 else None
            xml_i = tnode.get("i")
            if xml_i is None:
                raise Exception('missing attribute "i"')
            tags = ["io", xml_i]
            args = [self.parse_mathml_offset(offsetnode)]
            return self.mk_s_offset(tags, args)

        else:
            raise Exception("Encountered index offset")

    def parse_mathml_term(
        self, tnode: ET.Element, pars: Dict[str, int], gvars: List[str] = []
    ) -> int:
        if tnode.tag in ["return", "return-value"]:
            tags = ["rv"]
            args: List[int] = []

        elif tnode.tag == "ci":
            if tnode.text in macroconstants:
                tags = ["ic", macroconstants[tnode.text]]
                args = []
            else:
                tags = ["av"]
                tnode_text = tnode.text
                if tnode_text is None:
                    raise Exception("Expected element to have text")
                args = [
                    self.parse_mathml_api_parameter(tnode_text, pars, gvars=gvars),
                    self.parse_mathml_offset(None),
                ]

        elif tnode.tag == "cn":
            tnode_text = tnode.text
            if tnode_text is None:
                raise Exception("Expected element to have text")
            tags = ["ic", tnode_text]
            args = []

        elif tnode.tag == "field":
            tnode_fname = tnode.get("fname")
            if tnode_fname is None:
                raise Exception('Expected attribute "fname"')
            tags = ["fo", tnode_fname]
            args = []

        elif tnode.tag == "apply":
            (op, terms) = (tnode[0].tag, tnode[1:])
            if op == "addressed-value":
                offsetnode = tnode[0][0] if len(tnode[0]) > 0 else None
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_offset(offsetnode),
                ]
                tags = ["aa"]

            elif op == "divide":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "div"]

            elif op == "times":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "mult"]

            elif op == "plus":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "plusa"]

            elif op == "minus":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "minusa"]

            else:
                raise Exception('Parse mathml s-term apply not found for "' + op + '"')
        else:
            raise Exception('Parse mathml s-term not found for "' + tnode.tag + '"')

        return self.mk_s_term(tags, args)

    def parse_mathml_xpredicate(
        self,
        pcnode: ET.Element,
        pars: Dict[str, int],
        gvars: List[str] = [],
    ) -> int:
        mnode = pcnode.find("math")
        if mnode is None:
            raise Exception('Expected "math" child node')
        anode = mnode.find("apply")
        if anode is None:
            raise Exception('Expected "apply" child node')
        anode_first = anode[0]
        if anode_first is None:
            raise Exception("Expected child of anode")

        def pt(t: ET.Element) -> int:
            return self.parse_mathml_term(t, pars, gvars=gvars)

        def bound(t: str) -> int:
            if t in anode_first.attrib:
                ctxt = anode_first.get(t)
                if ctxt is None:
                    raise Exception('Missing attribute "' + t + '"')
                if ctxt in macroconstants:
                    b = int(macroconstants[ctxt])
                else:
                    b = int(ctxt)
                tags = ["ic", str(b)]
                return self.mk_s_term(tags, [])
            return -1

        (op, terms) = (anode_first.tag, anode[1:])
        optransformer = {
            "eq": "eq",
            "neq": "ne",
            "gt": "gt",
            "lt": "lt",
            "geq": "ge",
            "leq": "le",
        }
        if op in ["eq", "neq", "gt", "lt", "geq", "leq"]:
            args = [pt(t) for t in terms]
            op = optransformer[op]
            tags = ["x", op]

        elif op == "global-address":
            args = [pt(terms[0])]
            tags = ["ga"]

        elif op == "heap-address":
            args = [pt(terms[0])]
            tags = ["ha"]

        elif op == "not-null":
            args = [pt(terms[0])]
            tags = ["nn"]

        elif op == "not-zero":
            args = [pt(terms[0])]
            tags = ["nz"]

        elif op == "non-negative":
            args = [pt(terms[0])]
            tags = ["nng"]

        elif op == "preserves-all-memory":
            args = []
            tags = ["prm"]

        elif op == "false":
            args = []
            tags = ["f"]

        elif op == "initialized":
            args = [pt(terms[0])]
            tags = ["i"]

        elif op == "tainted":
            args = [pt(terms[0]), bound("lb"), bound("ub")]
            tags = ["tt"]

        elif op == "allocation-base":
            args = [pt(terms[0])]
            tags = ["ab"]

        elif op == "block-write":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["bw"]

        elif op == "valid-mem":
            args = [pt(terms[0])]
            tags = ["vm"]

        elif op == "new-memory":
            args = [pt(terms[0])]
            tags = ["nm"]

        elif op == "buffer":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["b"]

        elif op == "rev-buffer":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["b"]

        elif (op == "initializes-range") or (op == "initialized-range"):
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["ir"]

        else:
            raise Exception(
                "Parse mathml xpredicate not found for "
                + op
                + " in file "
                + self.cfile.name
            )

        return self.mk_xpredicate(tags, args)

    # ------------------------ Read/write xml services -----------------------

    def read_xml_xpredicate(self, node: ET.Element, tag: str = "ipr") -> XPredicate:
        xml_value = node.get(tag)
        if xml_value is None:
            raise Exception('No value for tag "' + tag + '"')
        return self.get_xpredicate(int(xml_value))

    def read_xml_postcondition(self, node: ET.Element, tag: str = "ixpre") -> XPredicate:
        xml_value = node.get(tag)
        if xml_value is None:
            raise Exception('No value for tag "' + tag + '"')
        return self.get_xpredicate(int(xml_value))

    def write_xml_postcondition(self, node: ET.Element, pc: XPredicate, tag: str = "ixpre") -> None:
        return node.set(tag, str(self.index_xpredicate(pc)))

    def read_xml_postrequest(self, node: ET.Element, tag: str = "iipr") -> PostRequest:
        xml_value = node.get(tag)
        if xml_value is None:
            raise Exception('No value for tag "' + tag + '"')
        return self.get_postrequest(int(xml_value))

    # ------------------- Initialize dictionary ------------------------------

    def initialize(self, xnode: ET.Element) -> None:
        if xnode is None:
            return
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is None:
                raise Exception('Expected element "' + t.name + '"')
            else:
                t.reset()
                t.read_xml(xtable, "n")

    # ----------------------- Printing ---------------------------------------

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
