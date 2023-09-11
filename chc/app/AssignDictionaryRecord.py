# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023      Aarno Labs LLC
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

from typing import cast, Callable, Dict, List, Tuple, Type, TypeVar, TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations    
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFileAssignmentDictionary import CFileAssignmentDictionary


class AssignDictionaryRecord(IT.IndexedTableValue):
    """Base class for all objects kep in the CFileAssignmentDictionary."""

    def __init__(
            self,
            ad: "CFileAssignmentDictionary",
            ixval: IT.IndexedTableValue) -> None:
        IT.IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._ad = ad

    @property
    def ad(self) -> "CFileAssignmentDictionary":
        return self._ad

    @property
    def cfile(self) -> "CFile":
        return self.ad.cfile

    @property
    def cd(self) -> "CFileDictionary":
        return self.cfile.dictionary

    @property
    def cdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations


ADiR = TypeVar("ADiR", bound=AssignDictionaryRecord, covariant=True)


class AssignDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[AssignDictionaryRecord]] = {}

    def register_tag(self, tag: str, anchor: type) -> Callable[[type], type]:

        def handler(t: type) -> type:
            self.register[(anchor, tag)] = t
            return t

        return handler

    def mk_instance(
            self,
            ad: "CFileAssignmentDictionary",
            ixval: IT.IndexedTableValue,
            anchor: Type[ADiR]) -> ADiR:
        tag = ixval.tags[0]
        if (anchor, tag) not in self.register:
            raise UF.CHCError("Unknown assign dictionary type: " + tag)
        instance = self.register[(anchor, tag)](ad, ixval)
        return cast(ADiR, instance)


adregistry: AssignDictionaryRegistry = AssignDictionaryRegistry()
