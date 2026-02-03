# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023-2024  Aarno Labs LLC
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
"""Base class for objects in the function-level proof obligation dictionary."""

from typing import Callable, cast, Dict, List, Tuple, Type, TypeVar, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary
    from chc.app.CApplication import CApplication
    from chc.app.CContext import ProgramContext
    from chc.app.CContextDictionary import CContextDictionary
    from chc.app.CDictionary import CDictionary
    from chc.app.CFile import CFile
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation
    from chc.proof.CFilePredicateDictionary import CFilePredicateDictionary
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.CPOPredicate import CPOPredicate


class CFunPODictionaryRecord(IndexedTableValue):

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue) -> None:
        IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._pod = pod

    @property
    def pod(self) -> "CFunPODictionary":
        return self._pod

    @property
    def pd(self) -> "CFilePredicateDictionary":
        return self.pod.pd

    @property
    def ifd(self) -> "InterfaceDictionary":
        return self.pod.interfacedictionary

    @property
    def cfun(self) -> "CFunction":
        return self.pod.cfun

    @property
    def cfile(self) -> "CFile":
        return self.pd.cfile

    @property
    def cdecls(self) -> "CFileDeclarations":
        return self.cfile.declarations

    @property
    def cdictionary(self) -> "CDictionary":
        return self.cfile.dictionary

    @property
    def cxd(self) -> "CContextDictionary":
        return self.cfile.contextdictionary

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    def __str__(self) -> str:
        return "po-dictionary-record: " + str(self.key)


class CFunPOType(CFunPODictionaryRecord):

    def __init__(self, pod: "CFunPODictionary", ixval: IndexedTableValue) -> None:
        CFunPODictionaryRecord.__init__(self, pod, ixval)

    @property
    def location(self) -> "CLocation":
        return self.cdecls.get_location(self.args[0])

    @property
    def context(self) -> "ProgramContext":
        return self.cxd.get_program_context(self.args[1])

    @property
    def predicate(self) -> "CPOPredicate":
        return self.pd.get_predicate(self.args[2])

    @property
    def external_id(self) -> int:
        raise UF.CHCError("POType does not have an external id")

    @property
    def po_index(self) -> int:
        return self.index


PodR = TypeVar("PodR", bound=CFunPODictionaryRecord, covariant=True)


class CFunPODictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CFunPODictionaryRecord]] = {}

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
            pod: "CFunPODictionary",
            ixval: IndexedTableValue,
            anchor: Type[PodR]) -> PodR:
        tag = ixval.tags[0]
        if (anchor, tag) not in self.register:
            raise UF.CHCError(
                "Unknown cfun-po-dictionary type: "
                + tag
                + " with type "
                + str(anchor))
        instance = self.register[(anchor, tag)](pod, ixval)
        return cast(PodR, instance)


podregistry: CFunPODictionaryRegistry = CFunPODictionaryRegistry()
