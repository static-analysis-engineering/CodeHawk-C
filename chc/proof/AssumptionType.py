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

class ATDictionaryRecord(object):
    """Base class for assumption types."""

    def __init__(self,pod,index,tags,args):
        self.pod = pod
        self.pd = self.pod.cfun.cfile.predicatedictionary
        self.id = self.pod.cfun.cfile.interfacedictionary
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def is_local_assumption(self): return False
    def is_api_assumption(self): return False
    def is_global_api_assumption(self): return False
    def is_contract_assumption(self): return False
    def is_global_assumption(self): return False

    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))


class ATLocalAssumptionType(ATDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        ATDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_predicate(self): return self.pd.get_predicate(int(self.args[0]))

    def is_local_assumption(self): return True

    def __str__(self): return 'api:' + str(self.get_predicate())

class ATApiAssumptionType(ATDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        ATDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_apiid(self): return self.args[0]

    def get_predid(self): return int(self.args[0])

    def get_predicate(self): return self.pd.get_predicate(int(self.args[0]))

    def is_api_assumption(self): return True

    def __str__(self): return 'api:' + str(self.get_predicate())

class ATGlobalApiAssumptionType(ATDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        ATDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_predid(self): return int(self.args[0])

    def get_predicate(self): return self.pd.get_predicate(int(self.args[0]))

    def is_global_api_assumption(self): return True

    def __str__(self): return 'contract:' + str(self.get_predicate())

class ATPostconditionType(ATDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        ATDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_xpredid(self): return self.args[1]

    def get_callee(self): return self.args[0]

    def is_contract_assumption(self): return True

    def get_postrequest(self): return self.id.get_postrequest(int(self.args[0]))

    def __str__(self): return 'pc:' + str(self.get_postrequest())


class ATGlobalAssumptionType(ATDictionaryRecord):

    def __init__(self,pod,index,tags,args):
        ATDictionaryRecord.__init__(self,pod,index,tags,args)

    def get_predicate(self): return self.pd.get_predicate(int(self.args[0]))

    def is_global_assumption(self): return True

    def __str__(self): return 'ga:' + str(self.get_predicate())
