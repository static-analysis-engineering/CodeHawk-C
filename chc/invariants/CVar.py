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

class VDictionaryRecord(object):
    """Base class for all objects kept in the VarDictionary."""

    def __init__(self,vd,index,tags,args):
        self.vd = vd
        self.xd = vd.xd
        self.cdecls = vd.fdecls.cfun.cfile.declarations
        self.cd = self.cdecls.dictionary
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))


class AllocatedRegionData(VDictionaryRecord):

    def __init__(self,vd,index,tags,args):
        VDictionaryRecord.__init__(self,vd,index,tags,args)

    def get_allocation_type(self): return self.tags[0]

    def get_creator(self): return self.tags[1]

    def get_allocation_site(self):
        return self.cdecls.get_location(int(self.args[0]))

    def get_size(self): return self.xd.get_xpr(int(self.args[1]))

    def __str__(self):
        return (self.get_allocation_type() + ':' + self.creator()
                    + '@' + str(get_allocation_site())
                    + '(' + str(self.get_size()) + ')')


class MemoryBase(VDictionaryRecord):
    '''Base record for different types of memory base address.'''

    def __init__(self,vd,index,tags,args):
        VDictionaryRecord.__init__(self,vd,index,tags,args)

    def is_null(self): return False
    def is_stack_address(self): return False
    def is_alloc_stack_address(self): return False
    def is_heap_address(self): return False
    def is_global_address(self): return False
    def is_basevar(self): return False
    def is_string_literal(self): return False
    def is_freed(self): return False
    def is_uninterpreted(self): return False

    def __str__(self): return 'memory-base ' + self.tags[0]

class MemoryBaseNull(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_null(self): return True

    def has_associated_region(self): return (not (self.args[0] == -1))

    def get_associated_region(self):
        if self.args[0] > 0:
            return self.vd.get_memory_base(self.args[0])

    def __str__(self):
        if self.has_associated_region():
            a = ' (' + str(self.get_associated_region()) + ')'
        else:
            a = ''
        return ( 'null' + a )


class MemoryBaseStackAddress(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_stack_address(self): return True

    def get_variable(self): return self.xd.get_variable (int(self.args[0]))

    def __str__(self): return '&' + str(self.get_variable())

class MemoryBaseGlobalAddress(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_global_address(self): return True

    def get_variable(self): return self.xd.get_variable(int(self.args[0]))

    def __str__(self): return '&' + str(self.get_variable())

class MemoryBaseAllocStackAddress(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_alloc_stackaddress(self): return True

    def get_region_id(self): return int(self.args[0])

    def __str__(self): return 'alloca-' + str(self.get_region_id())

class MemoryBaseHeapAddress(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_heap_address(self): return True

    def is_valid(self): return (int(self.args[1]) == 1)

    def get_region_id(self): return int(self.args[0])

    def __str__(self): return 'heap-' + str(self.get_region_id())

class MemoryBaseBaseVar(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_basevar(self): return True

    def get_variable(self): return self.xd.get_variable(int(self.args[0]))

    def __str__(self): return str(self.get_variable())

class MemoryBaseStringLiteral(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_string_literal(self): return True

    def get_string(self): return self.cd.get_string(int(self.args[0]))

    def __str__(self): return '&("' + str(self.get_string()) + '")'

class MemoryBaseUninterpreted(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_uninterpreted(self): return True

    def get_name(self): return self.tags[1]

    def __str__(self): return 'uninterpreted_memory_base_' + self.get_name()


class MemoryBaseFreed(MemoryBase):

    def __init__(self,vd,index,tags,args):
        MemoryBase.__init__(self,vd,index,tags,args)

    def is_freed(self): return True

    def get_region(self): return self.vd.get_memory_base(int(self.args[1]))

    def __str__(self): return 'freed(' + str(self.get_region()) + ')'


class MemoryReferenceData(VDictionaryRecord):

    def __init__(self,vd,index,tags,args):
        VDictionaryRecord.__init__(self,vd,index,tags,args)

    def get_base(self): return self.vd.get_memory_base (int(self.args[0]))

    def get_type(self): return self.cd.get_typ(int(self.args[1]))

    def __str__(self): return (str(self.get_base()))

class ConstantValueVariable(VDictionaryRecord):

    def __init__(self,vd,index,tags,args):
        VDictionaryRecord.__init__(self,vd,index,tags,args)

    def is_initial_value(self): return False
    def is_function_return_value(self): return False
    def is_exp_function_return_value(self): return False
    def is_sideeffect_value(self): return False
    def is_exp_sideeffect_value(self): return False
    def is_symbolic_value(self): return False
    def is_tainted_value(self): return False
    def is_memory_address(self): return False

    def __str__(self): return 'cvv ' + self.tags[0]

class CVVInitialValue(ConstantValueVariable):
 
    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_initial_value(self): return True

    def get_variable(self): return self.xd.get_variable(int(self.args[0]))

    def get_type(self): return self.cd.get_typ(int(self.args[1]))

    def __str__(self): return str(self.get_variable()) + '_init'



class CVVFunctionReturnValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_function_return_value(self): return True

    def get_location(self): return self.cdecls.getlocation(int(self.args[0]))

    def get_callee(self): return self.vd.fdecls.get_varinfo(int(self.args[2]))

    def get_args(self):
        result = []
        for a in self.args[3:]:
            if int(a) == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(int(a)))
        return result

    def __str__(self):
        return (str(self.get_callee().vname) + '('
                    + ','.join([ str(a) for a in self.get_args() ])
                    + ')')

class CVVExpFunctionReturnValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_exp_function_return_value(self): return True

    def get_location(self): return self.cdecls.getlocation(int(self.args[0]))

    def get_callee(self): return self.xd.get_xpr(int(self.args[2]))

    def get_args(self):
        result = []
        for a in self.args[3:]:
            if int(a) == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(int(a)))
        return result

    def __str__(self):
        return (str(self.get_callee()) + '('
                    + ','.join([ str(a) for a in self.get_args() ])
                    + ')')


class CVVSideEffectValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_sideeffect_value(self): return True

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_callee(self): return self.vd.fdecls.get_varinfo(int(self.args[2]))

    def get_argnr(self): return int(self.args[3])

    def get_type(self): return self.cd.get_typ(int(self.args[4]))

    def get_args(self):
        result = []
        for a in self.args[5:]:
            if int(a) == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(int(a)))
        return result

    def __str__(self):
        return (str(self.get_callee()) + '('
                    + ','.join([ str(a) for a in self.get_args() ])
                    + ')')

class CVVExpSideEffectValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,cd,index,tags,args)

    def is_exp_sideeffect_value(self): return True

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_callee(self): return self.vd.fdecls.get_varinfo(int(self.args[2]))

    def get_argnr(self): return int(self.args[3])

    def get_type(self): return self.cd.get_typ(int(self.args[4]))

    def get_args(self):
        result = []
        for a in self.args[5:]:
            if int(a) == -1:
                result.append(None)
            else:
                result.append(self.xd.get_xpr(int(a)))
        return result

    def __str__(self):
        return (str(self.get_callee()) + '('
                    + ','.join([ str(a) for a in self.get_args() ])
                    + ')')


class CVVSymbolicValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_symbolic_value(self): return True

    def get_xpr(self): return self.xd.get_xpr(int(self.args[0]))

    def get_type(self): return self.cd.get_typ(int(self.args[1]))

    def __string__(self): return str(self.get_xpr())


class CVVTaintedValue(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_tainted_value(self): return True

    def has_lower_bound(self): return (int(self.args[1]) >= 0)

    def has_upper_bound(self): return (int(self.args[2]) >= 0)

    def get_lower_bound(self):
        if self.has_lower_bound():
            return self.xd.get_xpr(int(self.args[1]))

    def get_upper_bound(self):
        if self.has_upper_bound():
            return self.xd.get_xpr(int(self.args[2]))

    def get_origin(self): return self.xd.get_variable(int(self.args[0]))

    def get_type(self): return self.cd.get_typ(int(self.args[3]))

    def __str__(self):
        return ("taint-from-" + str(self.get_origin()))

class CVVByteSequence(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_byte_sequence(self): return True

    def get_origin(self): return self.xd.get_variable(int(self.args[0]))

    def has_length(self): return (int(self.args[1]) >= 0)

    def get_length(self):
        if self.has_length():
            return self.xd.get_xpr(int(self.args[1]))
    
class CVVMemoryAddress(ConstantValueVariable):

    def __init__(self,vd,index,tags,args):
        ConstantValueVariable.__init__(self,vd,index,tags,args)

    def is_memory_address(self): return True

    def get_memory_reference(self):
        return self.vd.get_memory_reference_data(int(self.args[0]))

    def get_offset(self): return self.cd.get_offset(int(self.args[1]))

    def __str__(self):
        return ('memory-address:' + str(self.get_memory_reference())
                    + ':' + str(self.get_offset()))




class CVariableDenotation(VDictionaryRecord):

    def __init__(self,vd,index,tags,args):
        VDictionaryRecord.__init__(self,vd,index,tags,args)

    def is_library_variable(self): return False
    def is_local_variable(self): return False
    def is_global_variable(self): return False
    def is_memory_variable(self): return False
    def is_memory_region_variable(self): return False
    def is_return_variable(self): return False
    def is_field_variable(self): return False
    def is_check_variable(self): return False
    def is_auxiliary_variable(self): return False

    def __str__(self): return 'c-variable-denotation ' + self.tags[0]

class CVLibraryVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_library_variable(self): return True

    def get_varinfo(self): return self.vd.fdecls.get(varinfo(self.args[0]))

    def get_library_variable(self):
        return self.vd.cfile.interfacedictionary.get_library_variable(self.args[1])

    def __str__(self): return 'libv:' + str(self.get_varinfo())


class LocalVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_local_variable(self): return True

    def get_varinfo(self): return self.vd.fdecls.get_varinfo(int(self.args[0]))

    def get_offset(self): return self.vd.fdecls.dictionary.get_offset(int(self.args[1]))

    def __str__(self): return 'lv:' + str(self.get_varinfo()) + str(self.get_offset())

class GlobalVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_global_variable(self): return True

    def get_varinfo(self): return self.vd.fdecls.get_varinfo(int(self.args[0]))

    def __str__(self): return 'gv:' + str(self.get_varinfo())

class MemoryVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_memory_variable(self): return True

    def get_memory_reference_id(self): return int(self.args[0])

    def get_memory_reference_data(self):
        return self.vd.get_memory_reference_data(self.get_memory_reference_id())

    def get_offset(self): return self.cd.get_offset(int(self.args[1]))

    def has_offset(self): return self.get_offset().has_offset()

    def __str__(self):
        offset = str(self.get_offset())
        return ('memvar-' + str(self.get_memory_reference_id())
                    + '{' + str(self.get_memory_reference_data()) + '}'
                    + offset )

class MemoryRegionVariable(CVariableDenotation):

    def __init__(self,cd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_memory_region_variable(self): return True

    def get_memory_region_id(self): return int(self.args[0])

    def get_memory_base(self):
        return vd.get_memory_base(self.get_memory_region_id())

    def __str__(self):
        return ('memreg-' + str(self.get_memory_region_id())
            + '{' + str(self.get_memory_base()) + '}')


class ReturnVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_return_variable(self): return True

    def get_type(self): return self.cd.get_typ(int(self.args[0]))

    def __str__(self): return 'returnval'

class FieldVariable(CVariableDenotation):
    '''Represents the joined values of a field for all struct instances.'''

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_field_variable(self): return True

    def get_fieldname(self): return self.tags[1]

    def get_ckey(self): return int(self.args[0])

    def __str__(self):
        return 'field-' + self.get_field_name() + '(' + str(self.get_ckey()) + ')'

class CheckVariable(CVariableDenotation):
    '''Represents the value of an expression that appears in proof obligations.'''

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_check_variable(self): return True

    def get_po_isppo_expnr_ids(self):
        return zip(self.args[1::3],self.args[2::3],self.args[3::3])

    def get_po_ids(self): return [ x for (_,x,_) in self.get_po_isppo_expnr_ids() ]

    def get_type(self): return self.cd.get_typ(int(self.args[0]))

    def __str__(self):
        return ('check('
                    + ';'.join([ (('ppo:' if x[0] == 1 else 'spo:') + str(x[1]) + ','
                                      + str(x[2])) for x in self.get_po_isppo_expnr_ids() ])
                    + ')')

class AugmentationVariable(CVariableDenotation):
    '''Represents an additional variable that does not interact with the  rest of the system.'''

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_augmentation_variable(self): return True

    def get_name(self): return self.tags[1]

    def __str__(self): return 'augv:' + str(self.get_name())

class AuxiliaryVariable(CVariableDenotation):

    def __init__(self,vd,index,tags,args):
        CVariableDenotation.__init__(self,vd,index,tags,args)

    def is_auxiliary_variable(self): return True

    def get_cvv(self): return self.vd.get_constant_value_variable(int(self.args[0]))

    def __str__(self): return 'aux-' + str(self.get_cvv())
                                    
