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
"""Base object value for the entries in the interface dictionary."""

from typing import Callable, cast, Dict, List, Tuple, Type, TypeVar, TYPE_CHECKING
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT


if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary


class InterfaceDictionaryRecord(IT.IndexedTableValue):
    """Base class for all objects kept in the InterfaceDictionary."""

    def __init__(
        self,
        dictionary: "InterfaceDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        IT.IndexedTableValue.__init__(self, ixval.index, ixval.tags, ixval.args)
        self._ifd = dictionary

    @property
    def ifd(self) -> "InterfaceDictionary":
        return self._ifd


IdR = TypeVar("IdR", bound=InterfaceDictionaryRecord, covariant=True)


class InterfaceDictionaryRegistry:

    def __init__(self) -> None:
        self.register: Dict[
            Tuple[type, str], Type[InterfaceDictionaryRecord]] = {}

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
            ifd: "InterfaceDictionary",
            ixval: IT.IndexedTableValue,
            anchor: Type[IdR]) -> IdR:
        tag = ixval.tags[0]
        if (anchor, tag) not in self.register:
            raise UF.CHCError("Unknown bdictionary type: " + tag)
        instance = self.register[(anchor, tag)](ifd, ixval)
        return cast(IdR, instance)


ifdregistry: InterfaceDictionaryRegistry = InterfaceDictionaryRegistry()
