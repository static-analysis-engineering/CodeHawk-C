# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2025  Aarno Labs LLC
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

import chc.app.CAttributes as CA
import chc.app.CExp as CE
import chc.app.CTyp as CT
from chc.app.CVarInfo import CVarInfo


class CVisitor(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def visit_voidtyp(self, ctyp: CT.CTypVoid) -> None:
        ...

    @abstractmethod
    def visit_inttyp(self, ctyp: CT.CTypInt) -> None:
        ...

    @abstractmethod
    def visit_floattyp(self, ctyp: CT.CTypFloat) -> None:
        ...

    @abstractmethod
    def visit_namedtyp(self, ctyp: CT.CTypNamed) -> None:
        ...

    @abstractmethod
    def visit_comptyp(self, ctyp: CT.CTypComp) -> None:
        ...

    @abstractmethod
    def visit_enumtyp(self, ctyp: CT.CTypEnum) -> None:
        ...

    @abstractmethod
    def visit_builtinvaargs(self, ctyp: CT.CTypBuiltinVaargs) -> None:
        ...

    @abstractmethod
    def visit_ptrtyp(self, ctyp: CT.CTypPtr) -> None:
        ...

    @abstractmethod
    def visit_arraytyp(self, ctyp: CT.CTypArray) -> None:
        ...

    @abstractmethod
    def visit_funtyp(self, ctyp: CT.CTypFun) -> None:
        ...

    @abstractmethod
    def visit_funarg(self, ctyp: CT.CFunArg) -> None:
        ...

    @abstractmethod
    def visit_funargs(self, ctyp: CT.CFunArgs) -> None:
        ...

    @abstractmethod
    def visit_attributes(self, a: CA.CAttributes) -> None:
        ...

    @abstractmethod
    def visit_constexp(self, a: CE.CExpConst) -> None:
        ...
