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

from typing import List, TYPE_CHECKING

import chc.app.CDictionaryRecord as CD

if TYPE_CHECKING:
    import chc.app.CDictionary

class ApiParameter(CD.CDictionaryRecord):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        CD.CDictionaryRecord.__init__(self,cd,index,tags,args)

    def is_formal(self) -> bool: return False
    def is_global(self) -> bool: return False

    def __str__(self) -> str: return 'api-parameter ' + self.tags[0]


class APFormal(ApiParameter):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        ApiParameter.__init__(self,cd,index,tags,args)

    def get_seq_number(self) -> int: return int(self.args[0])

    def is_formal(self) -> bool: return True

    def __str__(self) -> str: return 'par-' + str(self.get_seq_number())


class APGlobal(ApiParameter):

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        ApiParameter.__init__(self,cd,index,tags,args)

    def get_name(self) -> str: return self.tags[1]

    def is_global(self) -> bool: return True

    def __str__(self) -> str: return 'par-' + self.get_name()
