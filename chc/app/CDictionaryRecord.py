# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2024 Aarno Labs LLC
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
"""Base class for items in CDictionary and CDeclarations."""

import xml.etree.ElementTree as ET

from typing import cast, Callable, Dict, List, Tuple, Type, TypeVar, TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CDeclarations import CDeclarations
    from chc.app.CDictionary import CDictionary


class CDictionaryRecord(IT.IndexedTableValue):
    """Base class for all objects kept in the CDictionary."""

    def __init__(
        self,
        cd: "CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        IT.IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._cd = cd

    @property
    def cd(self) -> "CDictionary":
        return self._cd

    @property
    def decls(self) -> "CDeclarations":
        return self.cd.decls


class CDeclarationsRecord(IT.IndexedTableValue):
    """Base class for all objects kept in the CFileDeclarations."""

    def __init__(
        self,
        decls: "CDeclarations",
        ixval: IT.IndexedTableValue
    ) -> None:
        IT.IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._decls = decls

    @property
    def decls(self) -> "CDeclarations":
        return self._decls

    @property
    def dictionary(self) -> "CDictionary":
        return self.decls.dictionary


# __c_dictionary_record_types: Dict[Tuple[type, str], Type[CDictionaryRecord]] = {}
CDiR = TypeVar("CDiR", bound=CDictionaryRecord, covariant=True)


class CDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CDictionaryRecord]] = {}

    def register_tag(
            self,
            tag: str,
            anchor: type) -> Callable[[type], type]:
        def handler(t: type) -> type:
            self.register[(anchor, tag)] = t
            return t
        return handler

    def mk_instance(
            self,
            cd: "CDictionary",
            ixval: IT.IndexedTableValue,
            anchor: Type[CDiR]) -> CDiR:
        tag = ixval.tags[0]
        if (anchor, tag) not in self.register:
            raise UF.CHCError("Unknown cdictionary type: " + tag)
        instance = self.register[(anchor, tag)](cd, ixval)
        return cast(CDiR, instance)


cdregistry: CDictionaryRegistry = CDictionaryRegistry()


CDecR = TypeVar("CDecR", bound=CDeclarationsRecord, covariant=True)


class CDeclarationsRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CDeclarationsRecord]] = {}

    def register_tag(
            self,
            tag: str,
            anchor: type) -> Callable[[type], type]:
        def handler(t: type) -> type:
            self.register[(anchor, tag)] = t
            return t
        return handler

    def mk_instance(
            self,
            cd: "CDeclarations",
            ixval: IT.IndexedTableValue,
            anchor: Type[CDecR]) -> CDecR:
        tag = ixval.tags[0]
        if (anchor, tag) not in self.register:
            raise UF.CHCError("Unknown cdeclarations type: " + tag)
        instance = self.register[(anchor, tag)](cd, ixval)
        return cast(CDecR, instance)


cdecregistry: CDeclarationsRegistry = CDeclarationsRegistry()
