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

import chc.app.CDictionaryRecord as CD

class CConstBase(CD.CDictionaryRecord):
    """Constant expression."""

    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def get_exp(self,ix): return self.cd.get_exp(ix)
    def get_strings(self): return []

    def is_int(self): return False
    def is_str(self): return False
    def is_chr(self): return False
    def is_real(self): return False

    def __str__(self): return 'constantbase:' + self.tags[0]

class CConstInt(CConstBase):
    '''
    tags:
        0: 'int'
        1: string representation of value
        2: ikind

    args: -
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_int(self): return int(self.tags[1])

    def get_kind(self): return self.tags[2]

    def is_int(self): return True

    def __str__(self): return str(self.get_int())
        

class CConstStr(CConstBase):
    '''
    tags:
        0: 'cstr'

    args:
        0: string index
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_string(self): return self.cd.get_string(self.args[0])

    def get_strings(self): return [ self.get_string() ]

    def is_str(self): return True

    def __str__(self):
        strg = str(self.get_string())
        if len(strg) > 25:
            strg = str(len(strg)) + '-char string'
        return 'str(' + strg + ')'
        

class CConstWStr(CConstBase):
    '''
    tags:
        0: 'cwstr'
        1 -> : string representation of int64 integers

    args: -
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_string(self): return '-'.join(self.tags[1:])

    def __str__(self): return 'wstr(' + self.get_string() + ')'
        

class CConstChr(CConstBase):
    '''
    tags:
        0: 'cchr'

    args:
        0: char code
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_chr(self): return "'" + str(chr(self.args[0])) + "'"

    def is_chr(self): return True

    def __str__(self): return 'chr(' + self.get_chr() + ')'
        

class CConstReal(CConstBase):
    '''
    tags:
       0: 'creal'
       1: string representation of real

    args: -
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_real(self): return float(self.tags[1])

    def get_kind(self): return self.tags[2]

    def is_real(self): return True

    def __str__(self): return str(self.get_real())
        

class CConstEnum(CConstBase):
    '''
    tags:
        0: 'cenum'
        1: enum name
        2: item name

    args:
        0: exp
    '''

    def __init__(self,cd,index,tags,args):
        CConstBase.__init__(self,cd,index,tags,args)

    def get_enum_name(self): return self.tags[1]

    def get_item_name(self): return self.tags[2]

    def get_exp(self): return CConstBase.getexp(self,self.args[0])

    def __str__(self):
        return (self.get_enum_name + ':' + self.get_item_name
                    + '(' + str(self.get_exp()) + ')')



class CStringConstant(CD.CDictionaryRecord):
    '''
    tags:
        0: string value or hexadecimal representation of string value
        1: 'x' (optional) if string value is represented in hexadecimal

    args:
        0: length of original string
    '''
    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def get_string(self):
        if len(self.tags) > 0:
            return self.tags[0]
        else:                              # empty string is filtered out
            return ''

    def get_string_length(self): return self.args[0]

    def is_hex(self): return len(self.tags) > 1

    def __str__(self):
        if self.is_hex():
            return ('(' + str(self.get_string_length()) + '-char string')
        else:
            return self.get_string()
