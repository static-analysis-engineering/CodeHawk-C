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

from chc.util.IndexedTable import IndexedTableError

class POTypeDictionaryRecord(object):
    """Base class for proof obligation types in the PODictionary."""

    def __init__(self,pod,index,tags,args):
        self.pod = pod
        self.cfun = pod.cfun
        self.cfile = self.cfun.cfile
        self.pd = self.cfile.predicatedictionary
        self.id = self.cfile.interfacedictionary
        self.contexts = self.cfile.contexttable
        self.cdecls = self.cfile.declarations
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))


class PPOType(POTypeDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        POTypeDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_context(self): return self.contexts.get_program_context(int(self.args[1]))

    def get_predicate(self):
        try:
            return self.pd.get_predicate(int(self.args[2]))
        except IndexedTableError as e:
            print(str(e))
            raise

    def __str__(self):
        return ('ppo(' + str(self.get_location()) + ',' + str(self.get_context())
                    + ',' + str(self.get_predicate()) + ')')

class PPOLibType(POTypeDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        POTypeDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_context(self): return self.contexts.get_program_context(int(self.args[1]))

    def get_predicate(self): return self.pd.get_predicate(int(self.args[2]))

    def get_precondition(self): return self.id.get_xpredicate(int(self.args[3]))

    def get_lib_function_name(self): return self.tags[1]

    def __str__(self):
        return ('ppolib(' + str(self.get_location()) + ',' + str(self.get_context())
                    + ',' + str(self.get_predicate()) + ','
                    + self.get_lib_function_name() + ',' + str(self.get_precondition())
                    + ')' )

class LocalSPOType(POTypeDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        POTypeDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_context(self): return self.contexts.get_program_context(int(self.args[1]))

    def get_predicate(self): return self.pd.get_predicate(int(self.args[2]))

    def __str__(self):
        return ('local-spo(' + str(self.get_location()) + ',' + str(self.get_context())
                + ',' + str(self.get_predicate()) + ')' )

class CallsiteSPOType(POTypeDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        POTypeDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_context(self): return self.contexts.get_program_context(int(self.args[1]))

    def get_predicate(self): return self.pd.get_predicate(int(self.args[2]))

    def get_external_id(self): return int(self.args[3])

    def __str__(self):
        return ('cs-spo(' + str(self.get_location()) + ',' + str(self.get_context())
                    + ',' + str(self.get_predicate()) + ','
                    + str(self.get_external_id()) + ')' )


class ReturnsiteSPOType(POTypeDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        POTypeDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_location(self): return self.cdecls.get_location(int(self.args[0]))

    def get_context(self): return self.contexts.get_program_context(int(self.args[1]))

    def get_predicate(self): return self.pd.get_predicate(int(self.args[2]))

    def get_postcondition(self): return self.id.get_xpredicate(int(self.args[3]))

    def get_external_id(self): return int(self.args[3])

    def __str__(self):
        return ('rs-spo(' + str(self.get_location()) + ',' + str(self.get_context())
                    + ',' + str(self.get_predicate()) + ','
                    + str(self.get_postcondition()) + ')')
