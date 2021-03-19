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
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    import chc.app.CDictionary

class CDictionaryRecord(object):
    """Base class for all objects kept in the CDictionary."""

    def __init__(self, cd: 'chc.app.CDictionary.CDictionary', index: int, tags: List[str], args: List[int]) -> None:
        self.cd = cd
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self) -> Tuple[str, str]: return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def write_xml(self, node: ET.Element) -> None:
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))
    
class CDeclarationsRecord(object):
    '''Base class for all objects kept in the CFileDeclarations.'''

    def __init__(self,decls,index,tags,args):
        self.decls = decls
        self.index = index
        self.tags = tags
        self.args = args

    def get_key(self): return (','.join(self.tags), ','.join([str(x) for x in self.args]))

    def get_dictionary(self): return self.decls.dictionary
    
    def write_xml(self,node):
        (tagstr,argstr) = self.get_key()
        if len(tagstr) > 0: node.set('t',tagstr)
        if len(argstr) > 0: node.set('a',argstr)
        node.set('ix',str(self.index))
