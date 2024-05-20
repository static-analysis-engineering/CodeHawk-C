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
"""Object representation for CIL offset sum type."""

from typing import Dict, List, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExp


class COffset(CDictionaryRecord):
    """Base class for an expression offset."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    def has_offset(self) -> bool:
        return True

    @property
    def is_no_offset(self) -> bool:
        return False

    @property
    def is_field(self) -> bool:
        return False

    @property
    def is_index(self) -> bool:
        return False

    def get_strings(self) -> List[str]:
        return []

    def get_variable_uses(self, vid: int) -> int:
        return 0

    def to_dict(self) -> Dict[str, object]:
        return {"base": "offset"}

    def __str__(self) -> str:
        return "offsetbase:" + self.tags[0]


@cdregistry.register_tag("n", COffset)
class CNoOffset(COffset):

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        COffset.__init__(self, cd, ixval)

    def has_offset(self) -> bool:
        return False

    @property
    def is_no_offset(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, object]:
        return {"base": "no-offset"}

    def __str__(self) -> str:
        return ""


@cdregistry.register_tag("f", COffset)
class CFieldOffset(COffset):
    """Field offset

    * tags[1]: fieldname

    * args[0]: ckey of the containing struct
    * args[1]: index of sub-offset in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        COffset.__init__(self, cd, ixval)

    @property
    def fieldname(self) -> str:
        return self.tags[1]

    @property
    def ckey(self) -> int:
        return self.args[0]

    @property
    def offset(self) -> COffset:
        return self.cd.get_offset(self.args[1])

    @property
    def is_field(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, object]:
        result: Dict[str, object] = {
            "base": "field-offset", "field": self.fieldname}
        if self.offset.has_offset():
            result["offset"] = self.offset.to_dict()
        return result

    def __str__(self) -> str:
        offset = str(self.offset) if self.has_offset() else ""
        return "." + self.fieldname + offset


@cdregistry.register_tag("i", COffset)
class CIndexOffset(COffset):
    """Index offset into an array.

    * args[0]: index of base of index expression in cdictionary
    * args[1]: index of sub-offset in cdictionary
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        COffset.__init__(self, cd, ixval)

    @property
    def index_exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def offset(self) -> COffset:
        return self.cd.get_offset(self.args[1])

    def get_strings(self) -> List[str]:
        return self.index_exp.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.index_exp.get_variable_uses(vid)

    @property
    def is_index(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, object]:
        result: Dict[str, object] = {
            "base": "index-offset", "exp": self.index_exp.to_dict()}
        if self.offset.has_offset():
            result["offset"] = self.offset.to_dict()
        return result

    def __str__(self) -> str:
        offset = str(self.offset) if self.has_offset() else ""
        return "[" + str(self.index_exp) + "]" + offset
