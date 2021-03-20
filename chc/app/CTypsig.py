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

from typing import List, Tuple, TYPE_CHECKING

import chc.app.CDictionaryRecord as CD
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    import chc.app.CDictionary

class CTypsigTSBase(CD.CDictionaryRecord):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)
 

class CTypsigArray(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_len_opt(self):
        return (None if self.tags[1] == "" else int(self.tags[1]))

    def get_typsig(self): return self.cd.get_typsig(self.args[0])

    def get_attributes(self): return self.cd.get_attributes(self.args[1])

    def __str__(self) -> str: return ('tsarray(' + str(self.get_typsig())
                                   + ',' + str(self.get_len_opt))

class CTypsigPtr(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_typsig(self): return self.cd.get_typsig(self.args[0])

    def __str__(self) -> str: return ('tsptr(' + str(self.get_typsig()) + ')')

class CTypsigComp(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_name(self): return self.tags[1]

    def __str__(self) -> str: return ('tscomp(' + str(self.get_name()) + ')')

class CTypsigFun(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_typsig(self): return self.cd.get_typsig(self.args[0])

    def get_typsig_list_opt(self):
        ix = self.args[1]
        return (self.cd.get_typsig_list(ix) if ix >= 0 else None)

    def __str__(self) -> str:
        return ('(' + str(self.get_typsig_list_opt) + '):'
                    + str(self.get_typsig()) + ')')

class CTypsigEnum(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_name(self): return self.tags[1]

    def __str__(self) -> str: return 'tsenum(' + self.get_name() + ')'

class CTypsigBase(CTypsigTSBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CTypsigTSBase.__init__(self,cd,index,tags,args)

    def get_type(self): return self.cd.get_typ(self.args[0])

    def __str__(self) -> str: return 'tsbase(' + str(self.get_type()) + ')'
        

class CTypsigList(IT.IndexedTableValue):

    def __init__(self,cd,index,tags,args):
        self.cd = cd
        self.cfile = cd.cfile
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def get_typsig_list(self): return [ self.cd.get_typsig(ix) for ix in args ]

    def __str__(self) -> str:
        return ','.join([str(x) for x in self.get_typsig_list()])


    
