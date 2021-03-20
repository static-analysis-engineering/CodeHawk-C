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

if TYPE_CHECKING:
    import chc.app.CDictionary

class COffsetBase(CD.CDictionaryRecord):
    """Base class for an expression offset."""

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def has_offset(self) -> bool: return True
    def is_field(self) -> bool: return False
    def is_index(self) -> bool: return False

    def get_strings(self): return []
    def get_variable_uses(self,vid): return 0

    def to_dict(self): return { 'base': 'offset' }

    def __str__(self) -> str: return 'offsetbase:' + self.tags[0]

class CNoOffset(COffsetBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        COffsetBase.__init__(self,cd,index,tags,args)

    def has_offset(self) -> bool: return False

    def to_dict(self): return { 'base': 'no-offset' }

    def __str__(self) -> str: return ""

class CFieldOffset(COffsetBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        COffsetBase.__init__(self,cd,index,tags,args)

    def get_fieldname(self): return self.tags[1]

    def get_ckey(self): return self.args[0]

    def get_offset(self): return self.cd.get_offset(self.args[1])

    def is_field(self) -> bool: return True

    def to_dict(self):
        result = { 'base': 'field-offset',
                       'field': self.get_fieldname() }
        if self.get_offset().has_offset():
            result['offset'] = self.get_offset().to_dict()

    def __str__(self) -> str:
        offset = str(self.get_offset()) if self.has_offset() else ''
        return '.' + self.get_fieldname() + offset

class CIndexOffset(COffsetBase):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        COffsetBase.__init__(self,cd,index,tags,args)

    def get_index_exp(self): return self.cd.get_exp(self.args[0])

    def get_offset(self): return self.cd.get_offset(self.args[1])

    def get_strings(self): return self.get_index_exp().get_strings()

    def get_variable_uses(self,vid):
        return self.get_index_exp().get_variable_uses(vid)

    def is_index(self) -> bool: return True

    def to_dict(self):
        result = { 'base': 'index-offset',
                     'exp': self.get_index_exp().to_dict() }
        if self.get_offset().has_offset():
            result['offset'] = self.get_offset().to_dict()
        return result

    def __str__(self) -> str:
        offset = str(self.get_offset()) if self.has_offset() else ''
        return '[' + str(self.get_index_exp()) + ']' + offset
