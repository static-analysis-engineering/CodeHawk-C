# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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

from typing import Callable, Dict, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.util.IndexedTable import IndexedTable


file_tables: Dict[str, Tuple[str, str]] = {
    "cfgcontext": ("ctxtd", "cfg"),
    "expcontext": ("ctxtd", "exp"),
    "context": ("ctxtd", "p"),

    "compinfo": ("fdecls", "compinfo"),
    "enuminfo": ("fdecls", "enuminfo"),
    "enumitem": ("fdecls", "enumitem"),
    "fieldinfo": ("fdecls", "fieldinfo"),
    "initinfo": ("fdecls", "initinfo"),
    "location": ("fdecls", "location"),
    "offsetinfo": ("fdecls", "offsetinfo"),
    "typeinfo": ("fdecls", "typeinfo"),
    "varinfo": ("fdecls", "varinfo"),

    "attrparam": ("cd", "attrparam"),
    "attribute": ("cd", "attribute"),
    "attributes": ("cd", "attributes"),
    "constant": ("cd", "constant"),
    "exp": ("cd", "exp"),
    "funarg": ("cd", "funarg"),
    "funargs": ("cd", "funargs"),
    "lhost": ("cd", "lhost"),
    "lval": ("cd", "lval"),
    "offset": ("cd", "offset"),
    "typ": ("cd", "typ"),
    "typsig": ("cd", "typsig"),
    "typsiglist": ("cd", "typsiglist"),

    "predicate": ("pd", "predicate"),

    "api-parameter": ("id", "apiparam"),
    "post-assume": ("id", "postassume"),
    "post-request": ("id", "postrequest"),
    "s-term": ("id", "sterm"),
    "s-offset": ("id", "soffset"),
    "xpredicate": ("id", "xpred")
}

function_tables: Dict[str, Tuple[str, str]] = {
    "local-varinfo": ("fundecls", "local-varinfo"),

    "assumption-type": ("pod", "assumption"),
    "ppo-type": ("pod", "ppo"),
    "spo-type": ("pod", "spo"),

    "memory-base": ("vard", "membase"),
    "memory-ref": ("vard", "memref"),
    "constant-value-variable": ("vard", "cvv"),
    "c-variable-denotation": ("vard", "cvd"),

    "non-relational-value": ("invd", "nrv"),
    "invariant-fact": ("invd", "invfact"),

    "numerical": ("xprd", "numerical"),
    "symbol": ("xprd", "symbol"),
    "variable": ("xprd", "variable"),
    "xcst": ("xprd", "xcst"),
    "xpr": ("xprd", "xpr")
}
'''
function_tables: Dict[str, Callable[["CFunction"], "IndexedTable"]] = {
    # declarations
    "local_varinfo": lambda f: f.fdecls.local_varinfo_table,
    # proof types
    "assumption_type": lambda f: f.podictionary.assumption_type_table,
    "ppo_type": lambda f: f.podictionary.ppo_type_table,
    "spo_type": lambda f: f.podictionary.spo_type_table,
    # vard
    "memory_base": lambda f: f.vard.memory_base_table,
    "memory_reference_data": lambda f: f.vard.memory_reference_data_table,
    "constant_value_variable": lambda f: f.vard.constant_value_variable_table,
    "c_variable_denotation": lambda f: f.vard.c_variable_denotation_table,
    # invd
    "non_relational_value": lambda f: f.invd.non_relational_value_table,
    "invariant_fact": lambda f: f.invd.invariant_fact_table,
    # xpr
    "numerical": lambda f: f.vard.xd.numerical_table,
    "symbol": lambda f: f.vard.xd.symbol_table,
    "variable": lambda f: f.vard.xd.variable_table,
    "xcst": lambda f: f.vard.xd.xcst_table,
    "xpr": lambda f: f.vard.xd.xpr_table,
}
'''

def file_table_list() -> List[str]:
    return list(file_tables.keys())


def function_table_list() -> List[str]:
    return list(function_tables.keys())


def list_file_tables() -> str:
    lines: List[str] = []
    lines.append("*" * 80)
    for k in sorted(file_tables):
        lines.append("  " + k)
    lines.append("*" * 80)
    return "\n".join(lines)


def list_function_tables() -> str:
    lines: List[str] = []
    lines.append("*" * 80)
    for k in sorted(function_tables):
        lines.append("  " + k)
    lines.append("*" * 80)
    return "\n".join(lines)


def get_file_table(f: "CFile", tablename: str) -> str:
    lines: List[str] = []
    if tablename not in file_tables:
        lines.append("File table " + tablename + " not found.\nTables available:")
        lines.append(list_file_tables())
    else:
        (d, t) = file_tables[tablename]
        if d == "ctxtd":
            return f.contextdictionary.objectmap_to_string(t)
        elif d == "fdecls":
            return f.declarations.objectmap_to_string(t)
        elif d == "cd":
            return f.dictionary.objectmap_to_string(t)
        elif d == "pd":
            return f.predicatedictionary.objectmap_to_string(t)
        elif d == "id":
            return f.interfacedictionary.objectmap_to_string(t)
        else:
            return "?"

    return "\n".join(lines)


def get_function_table(f: "CFile", functionname: str, tablename: str) -> str:
    lines: List[str] = []

    if tablename not in function_tables:
        lines.append("Function table " + tablename + " not found.\nTables available:")
        lines.append(list_function_tables())
        return "\n".join(lines)

    if not f.has_function_by_name(functionname):
        lines.append("*" * 80)
        lines.append(
            "Function name "
            + functionname
            + " not found in file "
            + f.name
            + "\nFunction names available:"
        )
        for k in sorted(f.functionnames):
            lines.append("  " + k)
        lines.append("*" * 80)
        return "\n".join(lines)

    fn = f.functions[f.functionnames[functionname]]
    (d, t) = function_tables[tablename]
    if d == "fundecls":
        return fn.cfundecls.objectmap_to_string(t)
    elif d == "pod":
        return fn.podictionary.objectmap_to_string(t)
    elif d == "vard":
        return fn.vardictionary.objectmap_to_string(t)

    return "\n".join(lines)
