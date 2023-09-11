# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: A. Cody Schuffelen
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2021 Google LLC
# Copyright (c) 2022 Henny Sipma
# Copyright (c) 2023 Aarno Labs LLC
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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from chc.app.CDictionary import CDictionary

if TYPE_CHECKING:
    from chc.app.CFieldInfo import CFieldInfo
    from chc.app.CFile import CFile
    from chc.app.CInitInfo import CInitInfo, COffsetInitInfo
    from chc.app.CLocation import CLocation


class CDeclarations(ABC):

    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def dictionary(self) -> CDictionary:
        ...

    @property
    @abstractmethod
    def cfile(self) -> "CFile":
        ...

    @abstractmethod
    def get_initinfo(self, ix: int) -> "CInitInfo":
        ...

    @abstractmethod
    def get_fieldinfo(self, ix: int) -> "CFieldInfo":
        ...

    @abstractmethod
    def get_offset_init(self, ix: int) -> "COffsetInitInfo":
        ...

    @abstractmethod
    def is_struct(self, ckey: int) -> bool:
        ...

    @abstractmethod
    def get_location(self, ix: int) -> "CLocation":
        ...
