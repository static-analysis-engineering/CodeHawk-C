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
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF


class GlobalAssignmentBase(object):
    """Base class for all assignment objects."""

    def __init__(self,ad,index,tags,args):
        self.ad = ad
        self.cdecls = self.ad.declarations
        self.cd = self.ad.dictionary
        self.index = index
        self.tags = tags
        self.args = args

    def is_init_assignment(self): return False
    def is_global_assignment(self): return False
    def is_global_index_assignment(self): return False
    def is_static_assignment(self): return False
    def is_static_index_assignment(self): return False
    def is_field_assignment(self): return False
    def is_unknown_assignment(self): return False

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))

class GlobalAssignmentFunctionName(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def get_name(self): return self.tags[0]

    def __str__(self): return self.get_name()


class InitAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_init_assignment(self): return True

    def get_lhs(self): return self.cdecls.get_global_varinfo(self.args[0])

    def get_rhs(self): return self.cdecls.get_initinfo(self.args[1])

    def __str__(self): return 'I:' + str(self.get_lhs()) + ' := ' + str(self.get_rhs())


class GlobalAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_global_assignment(self): return True

    def get_lhs(self): return self.cdecls.get_global_varinfo(self.args[0])

    def get_rhs(self): return self.cd.get_exp(self.args[2])

    def __str__(self): return 'G:' + str(self.get_lhs()) + ' := ' + str(self.get_rhs())


class GlobalIndexAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_global_index_assignment(self): return True

    def get_lhs(self): return self.cdecls.get_global_varinfo(self.args[0])

    def get_rhs(self): return self.cd.get_exp(self.args[3])

    def get_index(self): return self.args[2]

    def __str__(self):
        return ('G:' + str(self.get_lhs()) + '[' + str(self.get_index()) + '] '
                    + ' := ' + str(self.get_rhs()))
   


class StaticAssignment(GlobalAssignmentBase):
    
    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_static_assignment(self): return True

    def get_lhs(self): return self.cdecls.get_global_varinfo(self.args[0])

    def get_rhs(self): return self.cd.get_exp(self.args[2])

    def __str__(self): return 'S:' + str(self.get_lhs()) + ' := ' + str(self.get_rhs())


class StaticIndexAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_static_index_assignment(self): return True

    def get_lhs(self): return self.cdecls.get_global_varinfo(self.args[0])

    def get_rhs(self): return self.cd.get_exp(self.args[2])

    def __str__(self):
        return ('S:' + str(self.get_lhs()) + '[' + str(self.get_index()) + '] '
                    + ' := ' + str(self.get_rhs()))
   


class FieldAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_field_assignment(self): return True

    def get_field(self): return self.cdecls.get_global_varinfo(self.tags[1])

    def get_rhs(self): return self.cd.get_exp(self.args[3])

    def __str__(self): return 'F:' + str(self.get_field()) + ' := ' + str(self.get_rhs())


class UnknownAssignment(GlobalAssignmentBase):

    def __init__(self,ad,index,tags,args):
        GlobalAssignmentBase.__init__(self,ad,index,tags,args)

    def is_unknown_assignment(self): return True

    def get_lhs(self): return self.cd.get_lval(self.args[1])

    def get_rhs(self): return self.cd.get_exp(self.args[2])

    def __str__(self): return 'U:' + str(self.get_lhs()) + ' := ' + str(self.get_rhs())
    
