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

class CAttrBase(CD.CDictionaryRecord):
    '''Attribute that comes with a C type.'''

    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def is_int(self): return False
    def is_str(self): return False
    def is_cons(self): return False
    def is_sizeof(self): return False
    def is_sizeofe(self): return False
    def is_sizeofs(self): return False
    def is_alignof(self): return False
    def is_alignofe(self): return False
    def is_alignofs(self): return False
    def is_unop(self): return False
    def is_binop(self): return False
    def is_dot(self): return False
    def is_star(self): return False
    def is_addrof(self): return False
    def is_index(self): return False
    def is_question(self): return False

    def __str__(self): return 'attrparam:' + self.tags[0]


class CAttrInt(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_int(self): return int(self.args[0])

    def is_int(self): return True

    def __str__(self): return 'aint(' + str(self.get_int()) + ')'


class CAttrStr(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_str(self): return self.args[0]

    def is_str(self): return True

    def __str__(self): return 'astr(' + str(self.get_str()) + ')'


class CAttrCons(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_cons(self): return self.tags[1]

    def get_params(self):
        return [ self.cd.get_attrparam(int(i)) for i in self.args ]

    def is_cons(self): return True

    def __str__(self): return 'acons(' + str(self.get_cons()) + ')'


class CAttrSizeOf(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.get_typ(int(self.args[0]))

    def is_sizeof(self): return True

    def __str__(self): return 'asizeof(' + str(self.get_type()) + ')'


class CAttrSizeOfE(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_sizeofe(self): return True

    def __str__(self): return 'asizeofe(' + str(self.get_param()) + ')'


class CAttrSizeOfS(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_typsig(self): return self.cd.get_typsig(int(self.args[0]))

    def is_sizeofs(self): return True

    def __str__(self): return 'asizeofs(' + str(self.get_typsig()) + ')'


class CAttrAlignOf(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.get_typ(int(self.args[0]))

    def is_alignof(self): return True

    def __str__(self): return 'aalignof(' + str(self.get_type()) + ')'


class CAttrAlignOfE(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_alignofe(self): return True

    def __str__(self): return 'aalignofe(' + str(self.get_param()) + ')'


class CAttrAlignOfS(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_typsig(self): return self.cd.get_typsig(int(self.args[0]))

    def is_alignofs(self): return True

    def __str__(self): return 'aalignofs(' + str(self.get_typsig()) + ')'


class CAttrUnOp(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_op(self): return tags[1]

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_unop(self): return True

    def __str__(self):
        return ('aunop(' + self.get_op() + ',' + str(self.get_param()) + ')')


class CAttrBinOp(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_op(self): return tags[1]

    def get_param1(self): return self.cd.get_attrparam(int(self.args[0]))

    def get_param2(self): return self.cd.get_attrparam(int(self.args[1]))

    def is_binop(self): return True

    def __str__(self):
        return ('abinop(' + str(self.get_param1()) + ' ' + self.get_op() + ' '
                    + str(self.get_param2()) + ')')


class CAttrDot(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_name(self): return tags[1]

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_dot(self): return True

    def __str__(self):
        return 'adot(' + self.get_name() + ',' + str(self.get_param()) + ')'


class CAttrStar(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_star(self): return True

    def __str__(self): return 'astar(' + str(self.get_param()) + ')'


class CAttrAddrOf(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param(self): return self.cd.get_attrparam(int(self.args[0]))

    def is_addrof(self): return True

    def __str__(self): return 'aaddrof(' + str(self.get_param()) + ')'


class CAttrIndex(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param1(self): return self.cd.get_param(int(self.args[0]))

    def get_param2(self): return self.cd.get_param(int(self.args[1]))

    def is_index(self): return True

    def __str__(self):
        return ('aindex(' + str(self.get_param1()) + ','
                    + str(self.get_param2()) + ')')


class CAttrQuestion(CAttrBase):

    def __init__(self,cd,index,tags,args):
        CAttrBase.__init__(self,cd,index,tags,args)

    def get_param1(self): return self.cd.get_param(int(self.args[0]))

    def get_param2(self): return self.cd.get_param(int(self.args[1]))

    def get_param3(self): return self.cd.get_param(int(self.args[2]))

    def __str__(self):
        return ('aquestion(' + str(self.get_param1()) + ','
                    + str(self.get_param2()) + ','
                    + str(self.get_param3()) + ')')



class CAttribute(CD.CDictionaryRecord):

    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def get_name(self): return self.tags[0]

    def get_params(self): return [ self.cd.get_attrparam(int(i)) for i in self.args ]

    def __str__(self):
        return self.get_name() + ': ' + ','.join([str(p) for p in self.get_params() ])


class CAttributes(CD.CDictionaryRecord):

    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def get_attributes(self): return [ self.cd.get_attribute(int(i)) for i in self.args ]

    def length(self): return len(self.get_attributes())

    def __str__(self):
        return ','.join([str(p) for p in self.get_attributes() ])
   

