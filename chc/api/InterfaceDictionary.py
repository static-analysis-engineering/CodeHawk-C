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

from typing import cast, Callable, Dict, List, Tuple, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.IndexedTable import IndexedTable, IndexedTableValue, IndexedTableSuperclass

import chc.api.ApiParameter as AP
from chc.api.ApiParameter import ApiParameter, APFormal, APGlobal
import chc.api.GlobalAssumption as GA
import chc.api.PostRequest as PR
from chc.api.PostRequest import PostRequest
import chc.api.PostAssume as PA
from chc.api.PostAssume import PostAssume
import chc.api.STerm as ST
from chc.api.STerm import SOffset, STerm, STArgNoOffset, STArgFieldOffset, STArgIndexOffset
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

api_parameter_constructors: Dict[
    str,
    Callable[[Tuple["InterfaceDictionary", int, List[str], List[int]]], ApiParameter],
] = {
    "pf": lambda x: AP.APFormal(*x),
    "pg": lambda x: AP.APGlobal(*x),
}

s_offset_constructors: Dict[
    str,
    Callable[[Tuple["InterfaceDictionary", int, List[str], List[int]]], SOffset],
] = {
    "no": lambda x: ST.STArgNoOffset(*x),
    "fo": lambda x: ST.STArgFieldOffset(*x),
    "io": lambda x: ST.STArgIndexOffset(*x),
}


s_term_constructors: Dict[
    str,
    Callable[[Tuple["InterfaceDictionary", int, List[str], List[int]]], STerm],
] = {
    "av": lambda x: ST.STArgValue(*x),
    "rv": lambda x: ST.STReturnValue(*x),
    "nc": lambda x: ST.STNamedConstant(*x),
    "ic": lambda x: ST.STNumConstant(*x),
    "is": lambda x: ST.STIndexSize(*x),
    "bs": lambda x: ST.STByteSize(*x),
    "fo": lambda x: ST.STFieldOffset(*x),
    "aa": lambda x: ST.STArgAddressedValue(*x),
    "at": lambda x: ST.STArgNullTerminatorPos(*x),
    "st": lambda x: ST.STArgSizeOfType(*x),
    "ax": lambda x: ST.STArithmeticExpr(*x),
    "fs": lambda x: ST.STFormattedOutputSize(*x),
    "rt": lambda x: ST.STRuntimeValue(*x),
}

xpredicate_constructors: Dict[
    str,
    Callable[[Tuple["InterfaceDictionary", int, List[str], List[int]]], XPredicate],
] = {
    "ab": lambda x: XP.XAllocationBase(*x),
    "bw": lambda x: XP.XBlockWrite(*x),
    "b": lambda x: XP.XBuffer(*x),
    "c": lambda x: XP.XConstTerm(*x),
    "cr": lambda x: XP.XControlledResource(*x),
    "f": lambda x: XP.XFalse(*x),
    "fi": lambda x: XP.XFormattedInput(*x),
    "fr": lambda x: XP.XFreed(*x),
    "fn": lambda x: XP.XFunctional(*x),
    "ga": lambda x: XP.XGlobalAddress(*x),
    "ha": lambda x: XP.XHeapAddress(*x),
    "i": lambda x: XP.XInitialized(*x),
    "ir": lambda x: XP.XInitializedRange(*x),
    "iv": lambda x: XP.XInvalidated(*x),
    "ifs": lambda x: XP.XInputFormatString(*x),
    "nm": lambda x: XP.XNewMemory(*x),
    "no": lambda x: XP.XNoOverlap(*x),
    "nn": lambda x: XP.XNotNull(*x),
    "nng": lambda x: XP.XNonNegative(*x),
    "nz": lambda x: XP.XNotZero(*x),
    "null": lambda x: XP.XNull(*x),
    "nt": lambda x: XP.XNullTerminated(*x),
    "ofs": lambda x: XP.XOutputFormatString(*x),
    "pr": lambda x: XP.XPreservesMemory(*x),
    "pv": lambda x: XP.XPreservesValue(*x),
    "prm": lambda x: XP.XPreservesAllMemory(*x),
    "prmx": lambda x: XP.XPreservesAllMemoryX(*x),
    "prn": lambda x: XP.XPreservesNullTermination(*x),
    "prv": lambda x: XP.XPreservesValidity(*x),
    "rb": lambda x: XP.XRevBuffer(*x),
    "rep": lambda x: XP.XRepositioned(*x),
    "sa": lambda x: XP.XStackAddress(*x),
    "x": lambda x: XP.XRelationalExpr(*x),
    "cf": lambda x: XP.XConfined(*x),
    "tt": lambda x: XP.XTainted(*x),
    "up": lambda x: XP.XUniquePointer(*x),
    "vm": lambda x: XP.XValidMem(*x),
}


class InterfaceDictionary(object):
    """Function interface constructs."""

    def __init__(self, cfile: "CFile"):
        self.cfile = cfile
        self.declarations = self.cfile.declarations
        self.dictionary = self.declarations.dictionary
        self.api_parameter_table: IndexedTable[ApiParameter] = IndexedTable(
            "api-parameter-table"
        )
        self.s_offset_table: IndexedTable[SOffset] = IndexedTable("s-offset-table")
        self.s_term_table: IndexedTable[STerm] = IndexedTable("s-term-table")
        self.xpredicate_table: IndexedTable[XPredicate] = IndexedTable(
            "xpredicate-table"
        )
        self.postrequest_table: IndexedTable[PostRequest] = IndexedTable(
            "postrequest-table"
        )
        self.postassume_table: IndexedTable[PostAssume] = IndexedTable(
            "postassume-table"
        )
        self.ds_condition_table: IndexedTable[IndexedTableValue] = IndexedTable(
            "ds-condition-table"
        )
        self.tables: List[Tuple[IndexedTableSuperclass, Callable[[ET.Element], None]]] = [
            (self.api_parameter_table, self._read_xml_api_parameter_table),
            (self.s_offset_table, self._read_xml_s_offset_table),
            (self.s_term_table, self._read_xml_s_term_table),
            (self.xpredicate_table, self._read_xml_xpredicate_table),
            (self.postrequest_table, self._read_xml_postrequest_table),
            (self.postassume_table, self._read_xml_postassume_table),
            (self.ds_condition_table, self._read_xml_ds_condition_table),
        ]
        self.initialize()

    # ----------------- Retrieve items from dictionary tables ----------------

    def get_api_parameter(self, ix: int) -> ApiParameter:
        return self.api_parameter_table.retrieve(ix)

    def get_s_offset(self, ix: int) -> SOffset:
        return self.s_offset_table.retrieve(ix)

    def get_s_term(self, ix: int) -> STerm:
        return self.s_term_table.retrieve(ix)

    def get_xpredicate(self, ix: int) -> XPredicate:
        return self.xpredicate_table.retrieve(ix)

    def get_postrequest(self, ix: int) -> PostRequest:
        return self.postrequest_table.retrieve(ix)

    # --------------------- Index items by category --------------------------

    def index_api_parameter(self, p: ApiParameter) -> int:
        if p.is_formal():

            def f_formal(index: int, key: object) -> APFormal:
                return APFormal(self, index, p.tags, p.args)

            return self.api_parameter_table.add(IT.get_key(p.tags, p.args), f_formal)
        if p.is_global():

            def f_global(index: int, key: object) -> APGlobal:
                return APGlobal(self, index, p.tags, p.args)

            return self.api_parameter_table.add(IT.get_key(p.tags, p.args), f_global)
        raise Exception("Unknown variant of ApiParameter")

    def mk_api_parameter(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: object) -> ApiParameter:
            return api_parameter_constructors[tags[0]]((self, index, tags, args))

        return self.api_parameter_table.add(IT.get_key(tags, args), f)

    def mk_formal_api_parameter(self, n: int) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pf"], [n]))

    def mk_global_api_parameter(self, g: str) -> ApiParameter:
        return self.get_api_parameter(self.mk_api_parameter(["pg", g], []))

    def index_s_offset(self, t: SOffset) -> int:
        if t.is_nooffset():

            def f_nooffset(index: int, key: object) -> STArgNoOffset:
                return STArgNoOffset(self, index, t.tags, t.args)

            return self.s_offset_table.add(IT.get_key(t.tags, t.args), f_nooffset)
        if t.is_field_offset():
            args = [self.index_s_offset(cast(STArgFieldOffset, t).get_offset())]

            def f_fieldoffset(index: int, key: object) -> STArgFieldOffset:
                return STArgFieldOffset(self, index, t.tags, args)

            return self.s_offset_table.add(IT.get_key(t.tags, args), f_fieldoffset)
        if t.is_index_offset():

            def f_indexoffset(index: int, key: object) -> STArgIndexOffset:
                return STArgIndexOffset(self, index, t.tags, t.args)

            return self.s_offset_table.add(IT.get_key(t.tags, t.args), f_indexoffset)
        raise Exception("Unknown variant of SOffset: \"" + str(t) + "\"")

    def mk_s_offset(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: object) -> SOffset:
            return s_offset_constructors[tags[0]]((self, index, tags, args))

        return self.s_offset_table.add(IT.get_key(tags, args), f)

    def mk_arg_no_offset(self) -> SOffset:
        return self.get_s_offset(self.mk_s_offset(["no"], []))

    def index_s_term(self, t: STerm) -> int:
        if t.is_arg_value():
            args = [
                self.index_api_parameter(cast(ST.STArgValue, t).get_parameter()),
                self.index_s_offset(cast(ST.STArgValue, t).get_offset()),
            ]

            def f_argvalue(index: int, key: object) -> ST.STArgValue:
                return ST.STArgValue(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_argvalue)
        if t.is_return_value():

            def f_returnvalue(index: int, key: object) -> ST.STReturnValue:
                return ST.STReturnValue(self, index, t.tags, t.args)

            return self.s_term_table.add(IT.get_key(t.tags, t.args), f_returnvalue)
        if t.is_named_constant():

            def f_namedconstant(index: int, key: object) -> ST.STNamedConstant:
                return ST.STNamedConstant(self, index, t.tags, t.args)

            return self.s_term_table.add(IT.get_key(t.tags, t.args), f_namedconstant)
        if t.is_num_constant():

            def f_numconstant(index: int, key: object) -> ST.STNumConstant:
                return ST.STNumConstant(self, index, t.tags, t.args)

            return self.s_term_table.add(IT.get_key(t.tags, t.args), f_numconstant)
        if t.is_index_size():
            args = [self.index_s_term(cast(ST.STIndexSize, t).get_term())]

            def f_indexsize(index: int, key: object) -> ST.STIndexSize:
                return ST.STIndexSize(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_indexsize)
        if t.is_byte_size():
            args = [self.index_s_term(cast(ST.STByteSize, t).get_term())]

            def f_bytesize(index: int, key: object) -> ST.STByteSize:
                return ST.STByteSize(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_bytesize)
        if t.is_field_offset():

            def f_fieldoffset(index: int, key: object) -> ST.STFieldOffset:
                return ST.STFieldOffset(self, index, t.tags, t.args)

            return self.s_term_table.add(IT.get_key(t.tags, t.args), f_fieldoffset)
        if t.is_arg_addressed_value():
            args = [
                self.index_s_term(cast(ST.STArgAddressedValue, t).get_base_term()),
                self.index_s_offset(cast(ST.STArgAddressedValue, t).get_offset()),
            ]

            def f_argaddressedvalue(index: int, key: object) -> ST.STArgAddressedValue:
                return ST.STArgAddressedValue(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_argaddressedvalue)
        if t.is_arg_null_terminator_pos():
            args = [self.index_s_term(cast(ST.STArgNullTerminatorPos, t).get_term())]

            def f_nullterminatorpos(index: int, key: object) -> ST.STArgNullTerminatorPos:
                return ST.STArgNullTerminatorPos(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_nullterminatorpos)
        if t.is_arg_size_of_type():
            args = [self.index_s_term(cast(ST.STArgSizeOfType, t).get_term())]

            def f_sizeoftype(index: int, key: object) -> ST.STArgSizeOfType:
                return ST.STArgSizeOfType(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_sizeoftype)
        if t.is_arithmetic_expr():
            t_arith = cast(ST.STArithmeticExpr, t)
            args = [self.index_s_term(t_arith.get_term1()), self.index_s_term(t_arith.get_term2())]

            def f_arithmeticexpr(index: int, key: object) -> ST.STArithmeticExpr:
                return ST.STArithmeticExpr(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_arithmeticexpr)
        if t.is_formatted_output_size():
            args = [self.index_s_term(cast(ST.STFormattedOutputSize, t).get_term())]

            def f_formattedoutputsize(index: int, key: object) -> ST.STFormattedOutputSize:
                return ST.STFormattedOutputSize(self, index, t.tags, args)

            return self.s_term_table.add(IT.get_key(t.tags, args), f_formattedoutputsize)
        if t.is_runtime_value():

            def f_runtimevalue(index: int, key: object) -> ST.STRuntimeValue:
                return ST.STRuntimeValue(self, index, t.tags, t.args)

            return self.s_term_table.add(IT.get_key(t.tags, t.args), f_runtimevalue)
        raise Exception("Unknown STerm variant: \"" + str(t) + "\"")

    def index_opt_s_term(self, t: Optional[STerm]) -> int:
        if t is None:
            return -1
        else:
            return self.index_s_term(t)

    def mk_s_term(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: object) -> STerm:
            return s_term_constructors[tags[0]]((self, index, tags, args))

        return self.s_term_table.add(IT.get_key(tags, args), f)

    def mk_field_s_term(self, fieldname: str) -> STerm:
        index = self.mk_s_term(["fo", fieldname], [])
        return self.get_s_term(index)

    def mk_xpredicate(self, tags: List[str], args: List[int]) -> int:
        def f(index: int, key: object) -> XPredicate:
            return xpredicate_constructors[tags[0]]((self, index, tags, args))

        return self.xpredicate_table.add(IT.get_key(tags, args), f)

    def mk_initialized_xpredicate(self, t: STerm) -> XPredicate:
        index = self.mk_xpredicate(["i"], [self.index_s_term(t)])
        return self.get_xpredicate(index)

    def index_xpredicate(self, p):
        if p.is_new_memory():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNewMemory(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_heap_address():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XHeapAddress(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_global_address():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XGlobalAddress(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_stack_address():

            def f(index, key):
                return XP.XStackAddress(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_allocation_base():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XAllocationBase(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_block_write():
            args = [self.index_s_term(p.get_term()), self.index_s_term(p.get_length())]

            def f(index, key):
                return XP.XBlockWrite(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_null():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNull(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_not_null():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNotNull(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_not_zero():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNotZero(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_non_negative():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNonNegative(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_initialized():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XInitialized(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_initialized_range():
            args = [
                self.index_s_term(p.get_buffer()),
                self.index_s_term(p.get_length()),
            ]

            def f(index, key):
                return XP.XInitializedRange(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_null_terminated():
            args = [self.index_s_term(p.get_term())]

            def f(index, key):
                return XP.XNullTerminated(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_false():

            def f(index, key):
                return XP.XFalse(self, index, p.tags, p.args)

            return self.xpredicate_table.add(IT.get_key(p.tags, p.args), f)
        if p.is_relational_expr():
            args = [self.index_s_term(p.get_term1()), self.index_s_term(p.get_term2())]

            def f(index, key):
                return XP.XRelationalExpr(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_preserves_all_memory():

            def f(index, key):
                return XP.XPreservesAllMemory(self, index, p.tags, p.args)

            return self.xpredicate_table.add(IT.get_key(p.tags, p.args), f)
        if p.is_tainted():
            args = [
                self.index_s_term(p.get_term()),
                self.index_opt_s_term(p.get_lower_bound()),
                self.index_opt_s_term(p.get_upper_bound()),
            ]

            def f(index, key):
                return XP.XTainted(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_buffer():
            args = [
                self.index_s_term(p.get_buffer()),
                self.index_s_term(p.get_length()),
            ]

            def f(index, key):
                return XP.XBuffer(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_rev_buffer():
            args = [
                self.index_s_term(p.get_buffer()),
                self.index_s_term(p.get_length()),
            ]

            def f(index, key):
                return XP.XRevBuffer(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        if p.is_controlled_resource():
            args = [self.index_s_term(p.get_size())]

            def f(index, key):
                return XP.ControlledResource(self, index, p.tags, args)

            return self.xpredicate_table.add(IT.get_key(p.tags, args), f)
        print("Index xpredicate not found for " + p.tags[0])
        exit(1)

    def parse_mathml_api_parameter(self, name, pars, gvars=[]):
        if (name not in pars) and (name not in gvars):
            print("Error in reading user data: " + name + " in file " + self.cfile.name)
        if name in pars:
            tags = ["pf"]
            args = [pars[name]]

            def f(index, key):
                return AP.APFormal(self, index, tags, args)

            return self.api_parameter_table.add(IT.get_key(tags, args), f)
        if name in gvars:
            tags = ["pg", name]
            args = []

            def f(index, key):
                return AP.APGlobal(self, index, tags, args)

            return self.api_parameter_table.add(IT.get_key(tags, args), f)
        print(
            "Api parameter name "
            + name
            + " not found in parameters or global variables"
        )
        exit(1)

    def parse_mathml_offset(self, tnode):
        if tnode is None:
            tags = ["no"]

            def f(index, key):
                return ST.STArgNoOffset(self, index, tags, [])

            return self.s_offset_table.add(IT.get_key(tags, []), f)
        elif tnode.tag == "field":
            offsetnode = tnode[0] if len(tnode) > 0 else None
            tags = ["fo", tnode.get("name")]
            args = [self.parse_mathml_offset(offsetnode)]

            def f(index, key):
                return ST.STArgFieldOffset(self, index, tags, args)

            return self.s_offset_table.add(IT.get_key(tags, args), f)
        elif tnode.tag == "index":
            offsetnode = tnode[0] if len(tnode) > 0 else None
            tags = ["io", tnode.get("i")]
            args = [self.parse_mathml_offset(offsetnode)]

            def f(index, key):
                return ST.STArgIndexOffset(self, index, tags, args)

            return self.s_offset_table.add(IT.get_key(tags, args), f)
        else:
            print("Encountered index offset")
            exit(1)

    def parse_mathml_term(self, tnode, pars, gvars=[]):
        if tnode.tag in ["return", "return-value"]:
            tags = ["rv"]
            args = []

            def f(index, key):
                return ST.STReturnValue(self, index, tags, args)

            return self.s_term_table.add(IT.get_key(tags, args), f)
        if tnode.tag == "ci":
            if tnode.text in macroconstants:
                tags = ["ic", macroconstants[tnode.text]]
                args = []

                def f(index, key):
                    return ST.STNumConstant(self, index, tags, args)

            else:
                tags = ["av"]
                args = [
                    self.parse_mathml_api_parameter(tnode.text, pars, gvars=gvars),
                    self.parse_mathml_offset(None),
                ]

                def f(index, key):
                    return ST.STArgValue(self, index, tags, args)

            return self.s_term_table.add(IT.get_key(tags, args), f)
        if tnode.tag == "cn":
            tags = ["ic", tnode.text]
            args = []

            def f(index, key):
                return ST.STNumConstant(self, index, tags, args)

            return self.s_term_table.add(IT.get_key(tags, args), f)
        if tnode.tag == "field":
            tags = ["fo", tnode.get("fname")]
            args = []

            def f(index, key):
                return ST.STFieldOffset(self, index, tags, args)

            return self.s_term_table.add(IT.get_key(tags, args), f)
        if tnode.tag == "apply":
            (op, terms) = (tnode[0].tag, tnode[1:])
            if op == "addressed-value":
                offsetnode = tnode[0][0] if len(tnode[0]) > 0 else None
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_offset(offsetnode),
                ]
                tags = ["aa"]

                def f(index, key):
                    return ST.STArgAddressedValue(self, index, tags, args)

                return self.s_term_table.add(IT.get_key(tags, args), f)
            elif op == "divide":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "div"]

                def f(index, key):
                    return ST.STArithmeticExpr(self, index, tags, args)

                return self.s_term_table.add(IT.get_key(tags, args), f)
            elif op == "times":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "mult"]

                def f(index, key):
                    return ST.STArithmeticExpr(self, index, tags, args)

                return self.s_term_table.add(IT.get_key(tags, args), f)
            elif op == "plus":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "plusa"]

                def f(index, key):
                    return ST.STArithmeticExpr(self, index, tags, args)

                return self.s_term_table.add(IT.get_key(tags, args), f)
            elif op == "minus":
                args = [
                    self.parse_mathml_term(terms[0], pars, gvars=gvars),
                    self.parse_mathml_term(terms[1], pars, gvars=gvars),
                ]
                tags = ["ax", "minusa"]

                def f(index, key):
                    return ST.STArithmeticExpr(self, index, tags, args)

                return self.s_term_table.add(IT.get_key(tags, args), f)
            else:
                print("Parse mathml s-term apply not found for " + op)
                exit(1)
        else:
            print("Parse mathml s-term not found for " + tnode.tag)
            exit(1)

    def parse_mathml_xpredicate(self, pcnode, pars, gvars=[]):
        mnode = pcnode.find("math")
        anode = mnode.find("apply")

        def pt(t):
            return self.parse_mathml_term(t, pars, gvars=gvars)

        def bound(t):
            if t in anode[0].attrib:
                ctxt = anode[0].get(t)
                if ctxt in macroconstants:
                    b = int(macroconstants[ctxt])
                else:
                    b = int(ctxt)
                tags = ["ic", str(b)]
                return self.mk_s_term(tags, [])
            return -1

        (op, terms) = (anode[0].tag, anode[1:])
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

            def f(index, key):
                return XP.XRelationalExpr(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "global-address":
            args = [pt(terms[0])]
            tags = ["ga"]

            def f(index, key):
                return XP.XGlobalAddress(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "heap-address":
            args = [pt(terms[0])]
            tags = ["ha"]

            def f(index, key):
                return XP.XHeapAddress(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "not-null":
            args = [pt(terms[0])]
            tags = ["nn"]

            def f(index, key):
                return XP.XNotNull(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "not-zero":
            args = [pt(terms[0])]
            tags = ["nz"]

            def f(index, key):
                return XP.XNotZero(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "non-negative":
            args = [pt(terms[0])]
            tags = ["nng"]

            def f(index, key):
                return XP.XNonNegative(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "preserves-all-memory":
            args = []
            tags = ["prm"]

            def f(index, key):
                return XP.XPreservesAllMemory(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "false":
            args = []
            tags = ["f"]

            def f(index, key):
                return XP.XFalse(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "initialized":
            args = [pt(terms[0])]
            tags = ["i"]

            def f(index, key):
                return XP.XInitialized(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "tainted":
            args = [pt(terms[0]), bound("lb"), bound("ub")]
            tags = ["tt"]

            def f(index, key):
                return XP.XTainted(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "allocation-base":
            args = [pt(terms[0])]
            tags = ["ab"]

            def f(index, key):
                return XP.XAllocationBase(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "block-write":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["bw"]

            def f(index, key):
                return XP.XBlockWrite(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "valid-mem":
            args = [pt(terms[0])]
            tags = ["vm"]

            def f(index, key):
                return XP.XValidMem(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "new-memory":
            args = [pt(terms[0])]
            tags = ["nm"]

            def f(index, key):
                return XP.XNewMemory(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "buffer":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["b"]

            def f(index, key):
                return XP.XBuffer(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if op == "rev-buffer":
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["b"]

            def f(index, key):
                return XP.XRevBuffer(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        if (op == "initializes-range") or (op == "initialized-range"):
            args = [pt(terms[0]), pt(terms[1])]
            tags = ["ir"]

            def f(index, key):
                return XP.XInitializedRange(self, index, tags, args)

            return self.xpredicate_table.add(IT.get_key(tags, args), f)
        else:
            print(
                "Parse mathml xpredicate not found for "
                + op
                + " in file "
                + self.cfile.name
            )
            exit(1)

    # ------------------------ Read/write xml services -----------------------

    def read_xml_xpredicate(self, node, tag="ipr"):
        return self.get_xpredicate(int(node.get(tag)))

    def read_xml_postcondition(self, node, tag="ixpre"):
        return self.get_xpredicate(int(node.get(tag)))

    def write_xml_postcondition(self, node, pc, tag="ixpre"):
        return node.set(tag, str(self.index_xpredicate(pc)))

    def read_xml_postrequest(self, node, tag="iipr"):
        return self.get_postrequest(int(node.get(tag)))

    def read_xml_global_assumption_request(self, node, tag="ipr"):
        return self.get_global_assumption_request(int(node.get(tag)))

    # ------------------- Initialize dictionary ------------------------------

    def initialize(self) -> None:
        xnode = UF.get_cfile_interface_dictionary_xnode(
            self.cfile.capp.path, self.cfile.name
        )
        if xnode is None:
            return
        for (t, f) in self.tables:
            elem = xnode.find(t.name)
            if elem is None:
                raise Exception("Expected element \"" + t.name + "\"")
            f(elem)

    # ----------------------- Printing ---------------------------------------

    def write_xml(self, node):
        def f(n, r):
            r.write_xml(n)

        for (t, _) in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)

    # --------------------- Initialization -----------------------------------

    def _read_xml_api_parameter_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> ApiParameter:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return api_parameter_constructors[tag](args)

        self.api_parameter_table.read_xml(txnode, "n", get_value)

    def _read_xml_s_offset_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> SOffset:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return s_offset_constructors[tag](args)

        self.s_offset_table.read_xml(txnode, "n", get_value)

    def _read_xml_s_term_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> STerm:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return s_term_constructors[tag](args)

        self.s_term_table.read_xml(txnode, "n", get_value)

    def _read_xml_xpredicate_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> XPredicate:
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return xpredicate_constructors[tag](args)

        self.xpredicate_table.read_xml(txnode, "n", get_value)

    def _read_xml_postrequest_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> PostRequest:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return PostRequest(*args)

        self.postrequest_table.read_xml(txnode, "n", get_value)

    def _read_xml_postassume_table(self, txnode: ET.Element) -> None:
        def get_value(node: ET.Element) -> PostAssume:
            rep = IT.get_rep(node)
            args = (self,) + rep
            return PA.PostAssume(*args)

        self.postassume_table.read_xml(txnode, "n", get_value)

    def _read_xml_ds_condition_table(self, txnode: ET.Element) -> None:
        pass
