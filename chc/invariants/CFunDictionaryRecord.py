# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023  Aarno Labs LLC
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
"""Base class for records in function-specific invariants, variable dictionary."""

from typing import (
    Callable, cast, Dict, Generic, List, Tuple, Type, TypeVar, TYPE_CHECKING)

import chc.util.fileutil as UF
from chc.util.IndexedTable import IndexedTableValue

if TYPE_CHECKING:
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFileDictionary import CFileDictionary
    from chc.app.CFunDeclarations import CFunDeclarations
    from chc.invariants.CFunInvDictionary import CFunInvDictionary
    from chc.invariants.CFunVarDictionary import CFunVarDictionary
    from chc.invariants.CFunXprDictionary import CFunXprDictionary


class CFunXprDictionaryRecord(IndexedTableValue):
    """Base class for all objects kept in the CFunXprDictionary."""

    def __init__(
            self, xd: "CFunXprDictionary", ixval: IndexedTableValue) -> None:
        IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._xd = xd

    @property
    def xd(self) -> "CFunXprDictionary":
        return self._xd

    @property
    def vd(self) -> "CFunVarDictionary":
        return self.xd.vd


class CFunVarDictionaryRecord(IndexedTableValue):
    """Base class for all objects kept in the CFunVarDictionary."""

    def __init__(
            self, vd: "CFunVarDictionary", ixval: IndexedTableValue) -> None:
        IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._vd = vd

    @property
    def vd(self) -> "CFunVarDictionary":
        return self._vd

    @property
    def xd(self) -> "CFunXprDictionary":
        return self.vd.xd

    @property
    def cd(self) -> "CFileDictionary":
        return self.vd.cdictionary

    @property
    def fdecls(self) -> "CFileDeclarations":
        return self.vd.fdecls

    @property
    def fundecls(self) -> "CFunDeclarations":
        return self.vd.fundecls


class CFunInvDictionaryRecord(IndexedTableValue):
    """Base class for all objects kept in the CFunInvDictionary."""

    def __init__(
            self, invd: "CFunInvDictionary", ixval: IndexedTableValue) -> None:
        IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._invd = invd

    @property
    def invd(self) -> "CFunInvDictionary":
        return self._invd

    @property
    def vd(self) -> "CFunVarDictionary":
        return self.invd.vd

    @property
    def xd(self) -> "CFunXprDictionary":
        return self.invd.xd


VdR = TypeVar("VdR", bound=CFunVarDictionaryRecord, covariant=True)


class CFunVarDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CFunVarDictionaryRecord]] = {}

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
            vd: "CFunVarDictionary",
            ixval: IndexedTableValue,
            superclass: type) -> VdR:
        tag = ixval.tags[0]
        if (superclass, tag) not in self.register:
            raise UF.CHCError(
                "Unknown vardictionary type: "
                + tag
                + " with type "
                + str(superclass))
        instance = self.register[(superclass, tag)](vd, ixval)
        return cast(VdR, instance)


varregistry: CFunVarDictionaryRegistry = CFunVarDictionaryRegistry()


XdR = TypeVar("XdR", bound=CFunXprDictionaryRecord, covariant=True)


class CFunXprDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CFunXprDictionaryRecord]] = {}

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
            xd: "CFunXprDictionary",
            ixval: IndexedTableValue,
            superclass: type) -> XdR:
        tag = ixval.tags[0]
        if (superclass, tag) not in self.register:
            raise UF.CHCError(
                "Unknown xprdictionary type: "
                + tag
                + " with type "
                + str(superclass))
        instance = self.register[(superclass, tag)](xd, ixval)
        return cast(XdR, instance)


xprregistry: CFunXprDictionaryRegistry = CFunXprDictionaryRegistry()


IdR = TypeVar("IdR", bound=CFunInvDictionaryRecord, covariant=True)


class CFunInvDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[Tuple[type, str], Type[CFunInvDictionaryRecord]] = {}

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
            invd: "CFunInvDictionary",
            ixval: IndexedTableValue,
            superclass: type) -> IdR:
        tag = ixval.tags[0]
        if (superclass, tag) not in self.register:
            raise UF.CHCError(
                "Unknown invariant dictionary type: "
                + tag
                + " with type "
                + str(superclass))
        instance = self.register[(superclass, tag)](invd, ixval)
        return cast(IdR, instance)


invregistry: CFunInvDictionaryRegistry = CFunInvDictionaryRegistry()
