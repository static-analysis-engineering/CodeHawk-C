# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny B. Sipma
# Copyright (c) 2023-2025 Aarno Labs LLC
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
"""Left-hand side value."""

from typing import Dict, List, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CLHost import CLHost
    from chc.app.COffset import COffset
    from chc.app.CVisitor import CVisitor


class CLval(CDictionaryRecord):
    """Left-hand side value.

    * args[0]: index of lhost in cdictionary
    * args[1]: index of offset in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def lhost(self) -> "CLHost":
        return self.cd.get_lhost(self.args[0])

    @property
    def offset(self) -> "COffset":
        return self.cd.get_offset(self.args[1])

    def has_variable(self, vid: int) -> bool:
        return self.lhost.has_variable(vid)

    def get_strings(self) -> List[str]:
        hostresult = self.lhost.get_strings()
        offsetresult = self.offset.get_strings()
        return hostresult + offsetresult

    def get_variable_uses(self, vid: int) -> int:
        hostresult = self.lhost.get_variable_uses(vid)
        offsetresult = self.offset.get_variable_uses(vid)
        return hostresult + offsetresult

    def has_variable_deref(self, vid: int) -> bool:
        return self.lhost.has_variable_deref(vid)

    def has_ref_type(self) -> bool:
        return self.lhost.has_ref_type()

    def is_var(self) -> bool:
        return self.lhost.is_var

    def to_dict(self) -> Dict[str, object]:
        return {
            "lhost": self.lhost.to_dict(),
            "offset": self.offset.to_dict(),
        }

    def to_idict(self) -> Dict[str, object]:
        return {"t": self.tags, "a": self.args}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_lval(self)

    def __str__(self) -> str:
        return str(self.lhost) + str(self.offset)
