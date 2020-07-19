# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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

file_tables = {
    # contexts
    'cfgcontext': lambda f: f.contexttable.cfgtable,
    'expcontext': lambda f:f.contexttable.exptable,
    'context': lambda f:f.contexttable.contexttable,
    
    # declarations
    'compinfo': lambda f:f.declarations.compinfo_table,
    'enuminfo': lambda f:f.declarations.enuminfo_table,
    'enumitem': lambda f:f.declarations.enumitem_table,
    'fieldinfo': lambda f:f.declarations.fieldinfo_table,
    'filename': lambda f:f.declarations.filename_table,
    'location': lambda f:f.declarations.location_table,
    'typeinfo': lambda f:f.declarations.typeinfo_table,
    'varinfo': lambda f:f.declarations.varinfo_table,

    # dictionary
    'attrparam': lambda f:f.declarations.dictionary.attrparam_table,
    'attribute': lambda f:f.declarations.dictionary.attribute_table,
    'attributes': lambda f:f.declarations.dictionary.attributes_table,
    'constant': lambda f:f.declarations.dictionary.constant_table,
    'exp': lambda f:f.declarations.dictionary.exp_table,
    'funarg': lambda f:f.declarations.dictionary.funarg_table,
    'funargs': lambda f:f.declarations.dictionary.funargs_table,
    'lhost': lambda f:f.declarations.dictionary.lhost_table,
    'lval': lambda f:f.declarations.dictionary.lval_table,
    'offset': lambda f:f.declarations.dictionary.offset_table,
    'typ': lambda f:f.declarations.dictionary.typ_table,
    'typsig': lambda f:f.declarations.dictionary.typsig_table,
    'typsiglist': lambda f:f.declarations.dictionary.typsiglist_table,
    'string': lambda f:f.declarations.dictionary.string_table,
    
    # predicatedictionary
    'predicate':lambda f:f.predicatedictionary.po_predicate_table,

    # interface dictionary
    'api-parameter': lambda f:f.interfacedictionary.api_parameter_table,
    's-term': lambda f:f.interfacedictionary.s_term_table,
    'xpredicate': lambda f:f.interfacedictionary.xpredicate_table,
    'postrequest': lambda f:f.interfacedictionary.postrequest_table,
    }

function_tables = {
    # declarations
    'local_varinfo': lambda f:f.fdecls.local_varinfo_table,

    # proof types
    'assumption_type': lambda f:f.podictionary.assumption_type_table,
    'ppo_type': lambda f:f.podictionary.ppo_type_table,
    'spo_type': lambda f:f.podictionary.spo_type_table,

    # vard
    'memory_base': lambda f:f.vard.memory_base_table,
    'memory_reference_data': lambda f:f.vard.memory_reference_data_table,
    'constant_value_variable': lambda f:f.vard.constant_value_variable_table,
    'c_variable_denotation': lambda f:f.vard.c_variable_denotation_table,

    # invd
    'non_relational_value': lambda f:f.invd.non_relational_value_table,
    'invariant_fact': lambda f:f.invd.invariant_fact_table,
    
    # xpr
    'numerical': lambda f:f.vard.xd.numerical_table,
    'symbol': lambda f:f.vard.xd.symbol_table,
    'variable': lambda f:f.vard.xd.variable_table,
    'xcst': lambda f:f.vard.xd.xcst_table,
    'xpr': lambda f:f.vard.xd.xpr_table
    }

def list_file_tables():
    lines = []
    lines.append('*' * 80)
    for k in sorted(file_tables):
        lines.append('  ' + k)
    lines.append('*' * 80)
    return '\n'.join(lines)

def list_function_tables():
    lines = []
    lines.append('*' * 80)
    for k in sorted(function_tables):
        lines.append('  ' + k)
    lines.append('*' * 80)
    return '\n'.join(lines)

def get_file_table(f,tablename):
    lines = []
    if tablename in file_tables:
        table = file_tables[tablename](f)
        if table.size() > 0:
            lines.append(str(table))
        else:
            lines.append('\n' + table.name + ' is empty' + '\n')
    else:
        lines.append('File table ' + tablename + ' not found.\nTables available:')
        lines.append(list_file_tables())
    return '\n'.join(lines)


def get_function_table(f,functionname,tablename):
    lines = []
    
    if not tablename in function_tables:
        lines.append('File table ' + tablename + ' not found.\nTables available:')
        lines.append(list_function_tables())
        return '\n'.join(lines)

    if not f.has_function_by_name(functionname):
        lines.append('*' * 80)        
        lines.append('Function name ' + functionname + ' not found in file '
                         + f.name + '\nFunction names available:')
        for k in sorted(f.functionnames):
            lines.append ('  ' + k)
        lines.append('*' * 80)
        return '\n'.join(lines)

    fn = f.functions[f.functionnames[functionname]]
    table = function_tables[tablename](fn)
    if table.size() > 0:
        lines.append(str(table))
    else:
        lines.append('\n' + table.name + ' is empty' + '\n')

    return '\n'.join(lines)
                         
        
