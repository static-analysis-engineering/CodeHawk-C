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
"""Dictionary of all non-local symbolic values."""

from typing import (
    Any, cast, Callable, Dict, List, Mapping, Tuple, Optional, TYPE_CHECKING)
import xml.etree.ElementTree as ET

from chc.api.ApiParameter import ApiParameter, APFormal, APGlobal
from chc.api.GlobalAssumption import GlobalAssumption
from chc.api.InterfaceDictionaryRecord import (
    InterfaceDictionaryRecord, ifdregistry)
from chc.api.PostAssume import PostAssume
from chc.api.PostRequest import PostRequest
from chc.api.SOffset import (
    SOffset, STArgNoOffset, STArgFieldOffset, STArgIndexOffset)
from chc.api.STerm import STerm
from chc.api.XPredicate import XPredicate

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTable, IndexedTableValue

# import chc.api.GlobalAssumption as GA
# import chc.api.PostRequest as PR

# import chc.api.PostAssume as PA

import chc.api.STerm as ST
import chc.api.XPredicate as XP



if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFileDictionary import CFileDictionary


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
    """Function interface constructs.

    Args:
        cfile (CFile): c-file that owns the dictionary
        xnode (Optional[ET.Element]): xml element that holds the entries
            in the dictionary
    """

    def __init__(self, cfile: "CFile", xnode: Optional[ET.Element]):
        self._cfile = cfile
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
            self.ds_condition_table]
        self._objmaps: Dict[str, Callable[[], Mapping[int, IndexedTableValue]]] = {
            "apiparam": self.get_api_parameter_map,
            "postassume": self.get_postassume_map,
            "postrequest": self.get_postrequest_map,
            "sterm": self.get_s_term_map,
            "soffset": self.get_s_offset_map,
            "xpred": self.get_xpredicate_map}
        self._initialize(xnode)

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def declarations(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def dictionary(self) -> "CFileDictionary":
        return self.cfile.dictionary

    # ----------------- Retrieve items from dictionary tables ----------------

    def get_api_parameter(self, ix: int) -> ApiParameter:
        return ifdregistry.mk_instance(
            self, self.api_parameter_table.retrieve(ix), ApiParameter)

    def get_api_parameter_map(self) -> Dict[int, IndexedTableValue]:
        return self.api_parameter_table.objectmap(self.get_api_parameter)

    def get_s_offset(self, ix: int) -> SOffset:
        return ifdregistry.mk_instance(
            self, self.s_offset_table.retrieve(ix), SOffset)

    def get_s_offset_map(self) -> Dict[int, IndexedTableValue]:
        return self.s_offset_table.objectmap(self.get_s_offset)

    def get_s_term(self, ix: int) -> STerm:
        return ifdregistry.mk_instance(
            self, self.s_term_table.retrieve(ix), STerm)

    def get_opt_s_term(self, ix: int) -> Optional[STerm]:
        if ix == -1:
            return None
        else:
            return self.get_s_term(ix)

    def get_s_term_map(self) -> Dict[int, IndexedTableValue]:
        return self.s_term_table.objectmap(self.get_s_term)

    def get_xpredicate(self, ix: int) -> XPredicate:
        return ifdregistry.mk_instance(
            self, self.xpredicate_table.retrieve(ix), XPredicate)

    def get_xpredicate_map(self) -> Dict[int, IndexedTableValue]:
        return self.xpredicate_table.objectmap(self.get_xpredicate)

    def get_postrequest(self, ix: int) -> PostRequest:
        return PostRequest(self, self.postrequest_table.retrieve(ix))

    def get_postrequest_map(self) -> Dict[int, IndexedTableValue]:
        return self.postrequest_table.objectmap(self.get_postrequest)

    def get_postassume(self, ix: int) -> PostAssume:
        return PostAssume(self, self.postassume_table.retrieve(ix))

    def get_postassume_map(self) -> Dict[int, IndexedTableValue]:
        return self.postassume_table.objectmap(self.get_postassume)

    # --------------------- Index items by category --------------------------

    def index_api_parameter(self, p: ApiParameter) -> int:
        return self.mk_api_parameter(p.tags, p.args)

    def mk_api_parameter(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> ApiParameter:
            itv = IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, ApiParameter)

        return self.api_parameter_table.add_tags_args(tags, args, f)

    def mk_formal_api_parameter(self, n: int) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pf"], [n]))

    def mk_global_api_parameter(self, g: str) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pg", g], []))

    def index_s_offset(self, t: SOffset) -> int:
        if t.is_field:
            t = cast(STArgFieldOffset, t)
            args = [self.index_s_offset(t.offset)]
        elif t.is_index:
            t = cast(STArgIndexOffset, t)
            args = [self.index_s_offset(t.offset)]
        else:
            args = t.args

        return self.mk_s_offset(t.tags, args)

    def mk_s_offset(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> SOffset:
            itv = IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, SOffset)

        return self.s_offset_table.add_tags_args(tags, args, f)

    def mk_arg_no_offset(self) -> SOffset:
        return self.get_s_offset(self.mk_s_offset(["no"], []))

    def index_s_term(self, t: STerm) -> int:

        if t.is_arg_value:
            t = cast(ST.STArgValue, t)
            args = [
                self.index_api_parameter(t.parameter),
                self.index_s_offset(t.offset),
            ]
        elif t.is_index_size:
            t = cast(ST.STIndexSize, t)
            args = [self.index_s_term(t.term)]
        elif t.is_byte_size:
            t = cast(ST.STByteSize, t)
            args = [self.index_s_term(t.term)]
        elif t.is_arg_addressed_value:
            t = cast(ST.STArgAddressedValue, t)
            args = [self.index_s_term(t.term), self.index_s_offset(t.offset)]
        elif t.is_arg_null_terminator_pos:
            t = cast(ST.STArgNullTerminatorPos, t)
            args = [self.index_s_term(t.term)]
        elif t.is_arg_size_of_type:
            t = cast(ST.STArgSizeOfType, t)
            args = [self.index_s_term(t.term)]
        elif t.is_formatted_output_size:
            t = cast(ST.STFormattedOutputSize, t)
            args = [self.index_s_term(t.term)]
        elif t.is_arithmetic_expr:
            t_arith = cast(ST.STArithmeticExpr, t)
            args = [
                self.index_s_term(t_arith.term1),
                self.index_s_term(t_arith.term2),
            ]
        else:
            args = t.args

        return self.mk_s_term(t.tags, args)

    def index_opt_s_term(self, t: Optional[STerm]) -> int:
        if t is None:
            return -1
        else:
            return self.index_s_term(t)

    def mk_s_term(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> STerm:
            itv = IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, STerm)

        return self.s_term_table.add_tags_args(tags, args, f)

    def mk_field_s_term(self, fieldname: str) -> STerm:
        index = self.mk_s_term(["fo", fieldname], [])
        return self.get_s_term(index)

    def mk_xpredicate(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> XPredicate:
            itv = IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, XPredicate)

        return self.xpredicate_table.add_tags_args(tags, args, f)

    def mk_initialized_xpredicate(self, t: STerm) -> XPredicate:
        index = self.mk_xpredicate(["i"], [self.index_s_term(t)])
        return self.get_xpredicate(index)

    def index_xpredicate(self, p: XPredicate) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> XPredicate:
            itv = IndexedTableValue(index, tags, args)
            return ifdregistry.mk_instance(self, itv, XPredicate)

        if p.is_new_memory:
            p = cast(XP.XNewMemory, p)
            args = [self.index_s_term(p.term)]

        elif p.is_heap_address:
            p = cast(XP.XHeapAddress, p)
            args = [self.index_s_term(p.term)]

        elif p.is_global_address:
            p = cast(XP.XGlobalAddress, p)
            args = [self.index_s_term(p.term)]

        elif p.is_stack_address:
            args = p.args

        elif p.is_allocation_base:
            p = cast(XP.XAllocationBase, p)
            args = [self.index_s_term(p.term)]

        elif p.is_block_write:
            bw = cast(XP.XBlockWrite, p)
            args = [
                self.index_s_term(bw.term),
                self.index_s_term(bw.length),
            ]

        elif p.is_null:
            p = cast(XP.XNull, p)
            args = [self.index_s_term(p.term)]

        elif p.is_not_null:
            p = cast(XP.XNotNull, p)
            args = [self.index_s_term(p.term)]

        elif p.is_not_zero:
            p = cast(XP.XNotZero, p)
            args = [self.index_s_term(p.term)]

        elif p.is_non_negative:
            p  = cast(XP.XNonNegative, p)
            args = [self.index_s_term(p.term)]

        elif p.is_initialized:
            p = cast(XP.XInitialized, p)
            args = [self.index_s_term(p.term)]

        elif p.is_initialized_range:
            p = cast(XP.XInitializedRange, p)
            args = [self.index_s_term(p.buffer), self.index_s_term(p.length)]

        elif p.is_null_terminated:
            p = cast(XP.XNullTerminated, p)
            args = [self.index_s_term(p.term)]

        elif p.is_false:
            args = p.args

        elif p.is_relational_expr:
            re = cast(XP.XRelationalExpr, p)
            args = [self.index_s_term(re.term1), self.index_s_term(re.term2)]

        elif p.is_preserves_all_memory:
            args = p.args

        elif p.is_tainted:
            p = cast(XP.XTainted, p)
            args = [
                self.index_s_term(p.term),
                self.index_opt_s_term(p.lower_bound),
                self.index_opt_s_term(p.upper_bound),
            ]

        elif p.is_buffer:
            p = cast(XP.XBuffer, p)
            args = [
                self.index_s_term(p.buffer), self.index_s_term(p.length)]

        elif p.is_rev_buffer:
            p = cast(XP.XRevBuffer, p)
            args = [self.index_s_term(p.buffer), self.index_s_term(p.length)]

        elif p.is_controlled_resource:
            p = cast(XP.XControlledResource, p)
            args = [self.index_s_term(p.size)]

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

    def _initialize(self, xnode: Optional[ET.Element]) -> None:
        if xnode is None:
            return
        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is None:
                raise Exception('Expected element "' + t.name + '"')
            else:
                t.reset()
                t.read_xml(xtable, "n")

    def reinitialize(self, xnode: ET.Element) -> None:
        self._initialize(xnode)

    # ----------------------- Printing ---------------------------------------

    def objectmap_to_string(self, name: str) -> str:
        if name in self._objmaps:
            objmap = self._objmaps[name]()
            lines: List[str] = []
            if len(objmap) == 0:
                lines.append("Table is empty")
            else:
                for (ix, obj) in objmap.items():
                    lines.append(str(ix).rjust(3) + "  " + str(obj))
            return "\n".join(lines)
        else:
            raise UF.CHCError(
                "Name: " + name +  " does not correspond to a table")

    def write_xml(self, node: ET.Element) -> None:
        def f(n: ET.Element, r: Any) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)
