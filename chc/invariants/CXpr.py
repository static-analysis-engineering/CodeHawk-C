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

xpr_operator_strings = {
    "plus": " + " ,
    "minus": " - " ,
    "mult": " * " ,
    "div": " / * ",
    "ge": " >= " ,
    "le": " <= " 
    }

class XDictionaryRecord(object):
    '''Base class for all objects kept in the XprDictionary.'''

    def __init__(self,xd,index,tags,args):
        self.xd = xd
        self.vd = self.xd.vd
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))

class CXNumerical(XDictionaryRecord):
    '''Numerical value.'''

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def get_value(self): return int(self.tags[0])

    def equals(self,other): return (self.get_value() == other.get_value())

    def __str__(self): return self.tags[0]


class CXSymbol(XDictionaryRecord):
    '''Symbolic value.'''

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def get_name(self): return self.tags[0]

    def get_attrs(self): return self.tags[1:]

    def get_seqnr(self): return int(self.args[0])

    def __str__(self):
        if len(self.tags) > 1:
            attrs = '_' + '_'.join(self.get_attrs())
        else:
            attrs = ''
        seqnr = self.get_seqnr()
        pseqnr = '_s:' + str(seqnr) if seqnr >= 0 else ''
        return self.get_name() + attrs + pseqnr

class CXVariable(XDictionaryRecord):
    '''CHIF variable.'''

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def get_name(self): return self.xd.get_symbol(int(self.args[0])).get_name()

    def get_seqnr(self): return self.xd.get_symbol(int(self.args[0])).get_seqnr()

    def get_type(self): return self.tags[0]

    def get_denotation(self): return self.vd.get_c_variable_denotation(self.get_seqnr())

    def __str__(self):
        # return (str(self.get_name()) + '(' + str(self.get_seqnr()) + ')')
        vtype = 'S' if self.get_type() == 'sv' else 'N'
        return (vtype + ':' + str(self.get_name()))


class CXXCstBase(XDictionaryRecord):
    '''Expression Constant.'''

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def is_symset(self): return False
    def is_intconst(self): return False
    def is_boolconst(self): return False
    def is_random(self): return False
    def is_unknown_int(self): return False
    def is_unknown_set(self): return False

    def __str__(self): return 'basexcst:' + self.tags[0]

class CXCSymSet(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_symset(self): return True

    def get_symbols(self): return [ self.xd.get_symbol(int(i)) for i in self.args ]

    def __str__(self): return '[' + ','.join([str(x) for x in self.get_symbols()]) + ']'


class CXIntConst(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_intconst(self): return True

    def get_constant(self): return self.xd.get_numerical(int(self.args[0]))

    def __str__(self): return str(self.get_constant())

class CXCBoolConst(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_boolconst(self): return True

    def is_true(self): return int(self.args[0]) == 1

    def is_false(self): return int(self.args[0]) == 0

    def __str__(self): return 'true' if self.is_true() else 'false'

class CXRandom(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_random(self): return True

    def __str__(self): return 'random'

class CXUnknownInt(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_unknow_nint(self): return True

    def __str__(self): return 'unknown int'

class CXUnknownSet(CXXCstBase):

    def __init__(self,xd,index,tags,args):
        CXXCstBase.__init__(self,xd,index,tags,args)

    def is_unknown_set(self): return True

    def __str__(self): return 'unknown set'


class CXXprBase(XDictionaryRecord):
    '''Analysis base expression.'''

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def is_var(self): return False
    def is_const(self): return False
    def is_op(self): return False
    def is_attr(self): return False

    def __str__(self): return 'basexpr:' + self.tags[0]

class CXVar(CXXprBase):

    def __init__(self,xd,index,tags,args):
        CXXprBase.__init__(self,xd,index,tags,args)

    def is_var(self): return True

    def get_variable(self): return self.xd.get_variable(int(self.args[0]))

    def __str__(self): return str(self.get_variable())

class CXConst(CXXprBase):

    def __init__(self,xd,index,tags,args):
        CXXprBase.__init__(self,xd,index,tags,args)

    def is_const(self): return True

    def get_const(self): return self.xd.get_xcst(int(self.args[0]))

    def __str__(self): return str(self.get_const())

class CXOp(CXXprBase):

    def __init__(self,xd,index,tags,args):
        CXXprBase.__init__(self,xd,index,tags,args)

    def is_op(self): return True

    def get_op(self): return self.tags[1]

    def get_args(self): return [ self.xd.get_xpr(int(i)) for i in self.args ]

    def __str__(self):
        args = self.get_args()
        if len(args) == 1:
            return '(' + xpr_operator_strings[self.get_op()]  + str(args[0]) + ')'
        elif len(args) == 2:
            return '(' + str(args[0]) + xpr_operator_strings[self.get_op()] + str(args[1]) + ')'
        else:
            return ('(' + xpr_operator_strings[self.get_op()]
                        + '(' + ','.join(str(x) for x in args) + ')')

class CXAttr(CXXprBase):

    def __init_(self,xd,index,tags,args):
        CXXprBase.__init__(self,xd,index,tags,args)

    def is_attr(self): return True

    def get_attr(self): return self.tags[1]

    def get_xpr(self): return self.xd.get_xpr(int(self.args[0]))

    def __str__(self):
        return 'attr(' + self.get_attr() + ',' + str(self.get_xpr()) + ')'

class CXprList(XDictionaryRecord):

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def get_exprs(self): return [ self.xd.get_xpr(int(i)) for i in self.args ]

    def __str__(self):
        return ' && '.join([str(x) for x in self.get_exprs()])

class CXprListList(XDictionaryRecord):

    def __init__(self,xd,index,tags,args):
        XDictionaryRecord.__init__(self,xd,index,tags,args)

    def get_expr_lists(self): return [ self.xd.get_xpr_list(int(i)) for i in self.args ]

    def __str__(self):
        return ' || '.join([('(' + str(x) + ')') for x in self.get_expr_lists()])
