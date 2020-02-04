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
import chc.app.CExp as CX

po_predicate_names = {
    'ab'  : 'allocation-base',
    'b'   : 'buffer',    
    'c'   : 'cast',
    'cb'  : 'common-base',
    'cbt' : 'common-base-type',    
    'cls' : 'can-leave-scope',
    'cr'  : 'controlled-resource',
    'cssl': 'signed-to-signed-cast-lb',
    'cssu': 'signed-to-signed-cast-ub',    
    'csul': 'signed-to-unsigned-cast-lb',
    'csuu': 'signed-to-unsigned-cast-ub',
    'cus' : 'unsigned-to-signed-cast',    
    'cuu' : 'unsigned-to-unsigned-cast',
    'dr'  : 'distinct-region',
    'fc'  : 'format-cast',
    'ft'  : 'format-string',
    'ga'  : 'global-address',
    'ha'  : 'heap-address',
    'i'   : 'initialized',    
    'ilb' : 'index-lower-bound',
    'io'  : 'int-overflow',    
    'ir'  : 'initialized-range',    
    'is'  : 'in-scope',
    'iu'  : 'int-underflow',    
    'iub' : 'index-upper-bound',    
    'lb'  : 'lower-bound',    
    'nm'  : 'new-memory',    
    'nn'  : 'not-null',
    'nneg': 'non-negative',
    'no'  : 'no-overlap',    
    'nt'  : 'null-terminated',
    'null': 'null',
    'pc'  : 'pointer-cast',
    'plb' : 'ptr-lower-bound',
    'pre' : 'precondition',
    'prm' : 'preserved-all-memory',    
    'pub' : 'ptr-upper-bound',
    'pubd': 'ptr-upper-bound-deref',
    'pv'  : 'preserves-value',
    'sae' : 'stack-address-escape',
    'tao' : 'type-at-offset',
    'ub'  : 'upper-bound',
    'uio' : 'uint-overflow',
    'uiu' : 'uint-underflow',
    'va'  : 'var-args',   
    'vc'  : 'value-constraint',    
    'vm'  : 'valid-mem',
    'w'   : 'width-overflow',    
    'z'   : 'not-zero'
    }

def get_predicate_tag(name):
    revnames = { v:k for (k,v) in po_predicate_names.items() }
    if name in revnames: return revnames[name]


class CPOPredicate(CD.CDictionaryRecord):

    def __init__(self,cd,index,tags,args):
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def get_tag(self): return po_predicate_names[self.tags[0]]
        
    def is_allocation_base(self): return False
    def is_buffer(self): return False
    def is_cast(self): return False
    def is_common_base(self): return False
    def is_format_cast(self): return False
    def is_controlled_resource(self): return False
    def is_format_string(self): return False
    def is_in_scope(self): return False
    def is_can_leave_scope(self): return False
    def is_global_address(self): return False
    def is_heap_address(self): return False
    def is_index_lower_bound(self): return False
    def is_index_upper_bound(self): return False
    def is_initialized(self): return False
    def is_initialized_range(self): return False
    def is_int_overflow(self): return False
    def is_int_underflow(self): return False
    def is_lower_bound(self): return False
    def is_new_memory(self): return False
    def is_non_negative(self): return False
    def is_no_overlap(self): return False
    def is_not_null(self): return False
    def is_not_zero(self): return False
    def is_null(self): return False
    def is_null_terminated(self): return False
    def is_pointer_cast(self): return False
    def is_preserved_all_memory(self): return False
    def is_ptr_lower_bound(self): return False
    def is_ptr_upper_bound(self): return False
    def is_ptr_upper_bound_deref(self): return False
    def is_rev_buffer(self): return False
    def is_signed_to_signed_cast_lb(self): return False
    def is_signed_to_signed_cast_ub(self): return False
    def is_signed_to_unsigned_cast_lb(self): return False
    def is_signed_to_unsigned_cast_ub(self): return False
    def is_unsigned_to_signed_cast(self): return False
    def is_unsigned_to_unsigned_cast(self): return False
    def is_stack_address_escape(self): return False
    def is_type_at_offset(self): return False
    def is_upper_bound(self): return False
    def is_valid_mem(self): return False
    def is_value_constraint(self): return False
    def is_width_overflow(self): return False

    def has_variable(self,vid): return False
    def has_variable_op(self,vid,op): return False
    def has_argument(self,vid): return False
    def has_variable_deref(self,vid): return False
    def has_ref_type(self): return False

    def __str__(self): return 'po-predicate ' + self.tags[0]


class CPONotNull(CPOPredicate):
    '''
    tags:
       0: 'nn'

    args:
        0: exp
    '''

    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_not_null(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return  lhost.is_var() and lhost.get_vid() == vid
        else:
            return False

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPOGlobalAddress(CPOPredicate):
    '''
    tags:
      0: 'ga'

    args:
       0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_global_address(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return lhost.is_var() and lhost.get_vid() == vid
        else:
            return False

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPOHeapAddress(CPOPredicate):
    '''
    tags:
      0: 'ha'

    args:
       0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(int(self.args[0]))

    def is_heap_address(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return lhost.is_var() and lhost.get_vid() == vid
        else:
            return False

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPODistinctRegion(CPOPredicate):
    '''
    tags:
    0: 'dr'

    args:
    0: exp
    1: memref index
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(int(self.args[0]))

    def get_memref(self): return int(self.args[1])

    def is_distinct_region(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return lhost.is_var() and lhost.get_vid() == vid
        else:
            return False

    def __str__(self):
        return self.get_tag() + '(' + str(self.get_exp()) + ',' + str(self.get_memref()) + ')'
        
class CPONull(CPOPredicate):
    '''
    tags:
       0: 'null'

    args:
       0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_null(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'



class CPOValidMem(CPOPredicate):
    '''
    tags:
        0: 'vm'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_valid_mem(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return  lhost.is_var() and lhost.get_vid() == vid
        else:
            return False


    def __str__(self): return self.get_tag() +'(' + str(self.get_exp()) + ')'


class CPOControlledResource(CPOPredicate):
    '''
    tags:
        0: 'cr',
        1: name of resource (e.g., memory)

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_resource(self): return self.tags[1]

    def is_controlled_resource(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return  lhost.is_var() and lhost.get_vid() == vid
        else:
            return False


    def __str__(self):
        return self.get_tag() + ':' + self.get_resource() + '(' + str(self.get_exp()) + ')'

class CPOCanLeaveScope(CPOPredicate):
    '''
    tags:
        0: 'cls'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_can_leave_scope(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):return self.get_tag() + '(' + str(self.get_exp()) + ')'

class CPOStackAddressEscape(CPOPredicate):
    '''
    tags:
       0: 'sae'

    args:
       0: lval option
       1: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_lval(self): return self.cd.dictionary.get_lval(int(self.args[0]))

    def get_exp(self): return self.cd.dictionary.get_exp(int(self.args[1]))

    def has_lval(self): return (int(self.args[0])) >= 0

    def is_stack_address_escape(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        lval = ''
        if self.has_lval():
            lval = str(self.get_lval()) + ','
        return (self.get_tag() + '(' + lval + str(self.get_exp()) + ')')
                
    


class CPOInScope(CPOPredicate):
    '''
    tags:
        0: 'is'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_in_scope(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPOAllocationBase(CPOPredicate):
    '''
    tags:
        0: 'ab'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_allocation_base(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):return self.get_tag() + '(' + str(self.get_exp()) + ')'

class CPONewMemory(CPOPredicate):
    '''
    tags:
       0: 'nm'

    args:
       0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_new_memory(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPOBuffer(CPOPredicate):
    '''
    tags:
       0: 'b'

    args:
       0: exp (pointer to buffer)
       1: exp (length of buffer in bytes)
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_length(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_buffer(self): return  True

    def has_variable(self,vid):
        return self.get_exp().has_variable(vid) or self.get_length().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',size:' + str(self.get_length()) + ')')

class CPORevBuffer(CPOPredicate):
    '''
    tags:
       0: 'b'

    args:
       0: exp (pointer to buffer)
       1: exp (length of buffer in bytes before pointer)
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_length(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_rev_buffer(self): return  True

    def has_variable(self,vid):
        return self.get_exp().has_variable(vid) or self.get_length().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',size:' + str(self.get_length()) + ')')

class CPOTypeAtOffset(CPOPredicate):
    '''
    tags:
        0: 'tao'

    args:
        0: typ
        1: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[1])

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def is_type_at_offset(self): return True

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_type()) + ','
            + str(self.get_exp()) + ')')



class CPOLowerBound(CPOPredicate):
    '''
    tags:
        0: 'lb'

    args:
        0: typ
        1: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_lower_bound(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_type()) + ','
            + str(self.get_exp()) + ')')



class CPOUpperBound(CPOPredicate):
    '''
    tags:
        0: 'ub'

    args:
        0: typ
        1: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[1])

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def is_upper_bound(self): return True

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_type()) + ','
            + str(self.get_exp()) + ')')


        
class CPOIndexLowerBound(CPOPredicate):
    '''
    tags:
        0: 'ilb'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_index_lower_bound(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'



class CPOIndexUpperBound(CPOPredicate):
    '''
    tags:
        0: 'iub'

    args:
        0: index-exp
        1: upperbound exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_bound(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_index_upper_bound(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',bound:' + str(self.get_bound()) + ')')



class CPOInitialized(CPOPredicate):
    '''
    tags:
       0: 'i'

    args:
        0: lval
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_lval(self): return self.cd.dictionary.get_lval(self.args[0])

    def is_initialized(self): return True

    def has_variable(self,vid): return self.get_lval().has_variable(vid)

    def has_variable_deref(self,vid): return self.get_lval().has_variable_deref(vid)

    def has_ref_type(self): return self.get_lval().has_ref_type()

    def __str__(self): return self.get_tag() + '(' + str(self.get_lval()) + ')'



class CPOInitializedRange(CPOPredicate):
    '''
    tags:
        0: 'ir'

    args:
        0: exp (pointer to start of address range)
        1: len-exp (number of bytes that should be initialized)
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_length(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_initialized_range(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',len:' + str(self.get_length()) + ')')



class CPOCast(CPOPredicate):
    '''
    tags:
        0: 'c'

    args:
        0: typ (tfrom, current)
        1: typ (tto, target)
        2: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_from_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_tgt_type(self): return self.cd.dictionary.get_typ(self.args[1])

    def is_cast(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp()) + ',from:'
                    + str(self.get_from_type())
                    + ',to:' + str(self.get_tgt_type()) + ')')

class CPOFormatCast(CPOPredicate):
    '''
    tags:
        0: 'c'

    args:
        0: typ (tfrom, current)
        1: typ (tto, target)
        2: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_from_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_tgt_type(self): return self.cd.dictionary.get_typ(self.args[1])

    def is_format_cast(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp()) + ',from:'
                    + str(self.get_from_type())
                    + ',to:' + str(self.get_tgt_type()) + ')')


class CPOPointerCast(CPOPredicate):
    '''
    tags:
        0: 'pc'

    args:
        0: typ (tfrom, current)
        1: typ (tto, target)
        2: exp  (pointed-to expression)
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_from_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_tgt_type(self): return self.cd.dictionary.get_typ(self.args[1])

    def is_pointer_cast(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def has_argument(self,vid):
        if self.get_exp().is_lval():
            lhost = self.get_exp().get_lval().get_lhost()
            return  lhost.is_var() and lhost.get_vid() == vid
        else:
            return False

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp()) + ',from:'
                    + str(self.get_from_type())
                    + ',to:' + str(self.get_tgt_type()) + ')')



class CPOSignedToUnsignedCastLB(CPOPredicate):
    '''
    tags:
        0: 'csul'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_signed_to_unsigned_cast_lb(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')

class CPOSignedToUnsignedCastUB(CPOPredicate):
    '''
    tags:
        0: 'csuu'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_signed_to_unsigned_cast_ub(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')


class CPOUnsignedToSignedCast(CPOPredicate):
    '''
    tags:
        0: 'cus'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_unsigned_to_signed_cast(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')

class CPOUnsignedToUnsignedCast(CPOPredicate):
    '''
    tags:
        0: 'cuu'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_unsigned_to_unsigned_cast(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')

class CPOSignedToSignedCastLB(CPOPredicate):
    '''
    tags:
        0: 'cssl'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_signed_to_signed_cast_lb(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')

class CPOSignedToSignedCastUB(CPOPredicate):
    '''
    tags:
        0: 'cssu'
        1: from ikind
        2: tgt ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_from_kind(self): return self.tags[1]

    def get_tgt_kind(self): return self.tags[2]

    def is_signed_to_signed_cast_ub(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp())
                    + ',from:' + self.get_from_kind()
                    + ',to:' + self.get_tgt_kind() + ')')

class CPONotZero(CPOPredicate):
    '''
    tags:
        0: 'z'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_not_zero(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'



class CPONonNegative(CPOPredicate):
    '''
    tags:
        0: 'nneg'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_non_negative(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'



class CPONullTerminated(CPOPredicate):
    '''
    tags:
        0: 'nt'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def is_null_terminated(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'



class CPOIntUnderflow(CPOPredicate):
    '''
    tags:
        0: 'iu'
        1: binop
        2: ikind

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_binop(self): return self.tags[1]

    def get_ikind(self): return self.tags[2]

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_int_underflow(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1())
                    + ',' + str(self.get_exp2())
                    + ',op:' + self.get_binop()
                    + ',ikind:' + self.get_ikind() + ')')



class CPOIntOverflow(CPOPredicate):
    '''
    tags:
        0: 'io'
        1: binop
        2: ikind

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_binop(self): return self.tags[1]

    def get_ikind(self): return self.tags[2]

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_int_overflow(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1())
                    + ',' + str(self.get_exp2())
                    + ',op:' + self.get_binop()
                    + ',ikind:' + self.get_ikind() + ')')

class CPOUIntUnderflow(CPOPredicate):
    '''
    tags:
        0: 'uiu'
        1: binop
        2: ikind

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_binop(self): return self.tags[1]

    def get_ikind(self): return self.tags[2]

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_int_underflow(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1())
                    + ',' + str(self.get_exp2())
                    + ',op:' + self.get_binop()
                    + ',ikind:' + self.get_ikind() + ')')



class CPOUIntOverflow(CPOPredicate):
    '''
    tags:
        0: 'uio'
        1: binop
        2: ikind

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_binop(self): return self.tags[1]

    def get_ikind(self): return self.tags[2]

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_int_overflow(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1())
                    + ',' + str(self.get_exp2())
                    + ',op:' + self.get_binop()
                    + ',ikind:' + self.get_ikind() + ')')


class CPOWidthOverflow(CPOPredicate):
    '''
    tags:
        0: 'w'
        1: ikind

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_ikind(self): return self.tags[1]

    def is_width_overflow(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp()) + ',kind:'
                    + self.get_ikind() + ')')



class CPOPtrLowerBound(CPOPredicate):
    '''
    tags:
        0: 'plb'
        1: binop

    args:
        0: typ
        1: exp1
        2: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[1])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_binop(self): return self.tags[1]

    def is_ptr_lower_bound(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1()) + ','
                    + str(self.get_exp2()) + ',op:' + self.get_binop()
                    + ',typ:' + str(self.get_type()) + ')' )


    
class CPOPtrUpperBound(CPOPredicate):
    '''
    tags:
        0: 'pl=ub'
        1: binop

    args:
        0: typ
        1: exp1
        2: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[1])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_binop(self): return self.tags[1]

    def is_ptr_upper_bound(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def has_variable_op(self,vid,op):
        return (self.get_exp1().has_variable_op(vid,op)
                    or self.get_exp2().has_variable_op(vid,op))

    def __str__(self):
        return (self.get_tag() + '(typ:' + str(self.get_type())
                    + ',op:' + self.get_binop() + ','
                    + str(self.get_exp1()) + ',' + str(self.get_exp2())
                    + ')')

class CPOPtrUpperBoundDeref(CPOPredicate):
    '''
    tags:
        0: 'pubd'
        1: binop

    args:
        0: typ
        1: exp1
        2: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.dictionary.get_typ(self.args[0])

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[1])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[2])

    def get_binop(self): return self.tags[1]

    def is_ptr_upper_bound_deref(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(typ:' + str(self.get_type())
                    + ',op:' + self.get_binop() + ','
                    + str(self.get_exp1()) + ',' + str(self.get_exp2())
                    + ')')


class CPOCommonBase(CPOPredicate):
    '''
    tags:
        0: 'cb'

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_common_base(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1()) + ','
                    + str(self.get_exp2()) + ')')


class CPOCommonBaseType(CPOPredicate):
    '''
    tags:
        0: 'cbt'

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1()) + ','
                    + str(self.get_exp2()) + ')')


class CPOFormatString(CPOPredicate):
    '''
    tags:
        0: 'ft'
    
    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(int(self.args[0]))

    def is_format_string(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return self.get_tag() + '(' + str(self.get_exp()) + ')'


class CPOVarArgs(CPOPredicate):
    '''
    tags:
       0: 'va'

    args:
       0: exp (format string)
       1: int (expected number of arguments)
       r: exps (actual arguments)
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_formatstring(self):
        return self.cd.dictionary.get_exp(int(self.args[1]))

    def get_argcount(self): return int(self.args[0])

    def get_arguments(self):
        return [ self.cd.dictionary.get_exp(int(x)) for x in self.args[2:] ]

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_formatstring())
                    + ',' + str(self.get_argcount()) + ','
                    + str(len(self.get_arguments())) + ')')

class CPONoOverlap(CPOPredicate):
    '''
    tags:
        0: 'no'

    args:
        0: exp1
        1: exp2
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp1(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_exp2(self): return self.cd.dictionary.get_exp(self.args[1])

    def is_no_overlap(self): return True

    def has_variable(self,vid):
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def __str__(self):
        return (self.get_tag() + '(' + str(self.get_exp1()) + ','
                    + str(self.get_exp2()) + ')')



class CPOValueConstraint(CPOPredicate):
    '''
    tags:
        0: 'vc'

    args:
        0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def get_tag(self): return CPOPredicate.get_tag(self)  # + ':' + str(self.get_exp())

    def is_value_constraint(self): return True

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return str(self.get_exp())


class CPOPreservedAllMemory(CPOPredicate):
    '''
    tags:
       0: 'prm'
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def is_preserved_all_memory(self): return True

    def __str__(self): return self.get_tag()


class CPOPreservedValue(CPOPredicate):
    '''
    tags:
       0: 'pv'

    args:
       0: exp
    '''
    def __init__(self,cd,index,tags,args):
        CPOPredicate.__init__(self,cd,index,tags,args)

    def get_exp(self): return self.cd.dictionary.get_exp(self.args[0])

    def has_variable(self,vid): return self.get_exp().has_variable(vid)

    def __str__(self): return 'preserves-value(' + str(self.get_exp()) + ')'
