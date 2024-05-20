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
"""Object representation of CIL constant sum type."""

from typing import List, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExp


class CConst(CDictionaryRecord):
    """Constant expression."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    def get_exp(self, ix: int) -> "CExp":
        return self.cd.get_exp(ix)

    def get_strings(self) -> List[str]:
        return []

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_str(self) -> bool:
        return False

    @property
    def is_wstr(self) -> bool:
        return False

    @property
    def is_chr(self) -> bool:
        return False

    @property
    def is_real(self) -> bool:
        return False

    @property
    def is_enum(self) -> bool:
        return False

    def __str__(self) -> str:
        return "constantbase:" + self.tags[0]


@cdregistry.register_tag("int", CConst)
class CConstInt(CConst):
    """
    Constant integer.

    - tags[1]: string representation of value
    - tags[2]: ikind
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def intvalue(self) -> int:
        return int(self.tags[1])

    @property
    def ikind(self) -> str:
        return self.tags[2]

    @property
    def is_int(self) -> bool:
        return True

    def __str__(self) -> str:
        return str(self.intvalue)


@cdregistry.register_tag("str", CConst)
class CConstStr(CConst):
    """
    Constant string.

    - args[0]: string index
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def stringvalue(self) -> str:
        return self.cd.get_string(self.args[0])

    def get_strings(self) -> List[str]:
        return [self.stringvalue]

    @property
    def is_str(self) -> bool:
        return True

    def __str__(self) -> str:
        strg = str(self.stringvalue)
        if len(strg) > 25:
            strg = str(len(strg)) + "-char string"
        return "str(" + strg + ")"


@cdregistry.register_tag("wstr", CConst)
class CConstWStr(CConst):
    """
    Constant wide string (represented as a sequence of int64 integers)

    - tags[1..]: string representation of int64 integers
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def is_wstr(self) -> bool:
        return True

    @property
    def stringvalue(self) -> str:
        return "-".join(self.tags[1:])

    def __str__(self) -> str:
        return "wstr(" + self.stringvalue + ")"


@cdregistry.register_tag("chr", CConst)
class CConstChr(CConst):
    """
    Constant character.

    - args[0]: char code
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def chrvalue(self) -> str:
        return "'" + str(chr(self.args[0])) + "'"

    @property
    def is_chr(self) -> bool:
        return True

    def __str__(self) -> str:
        return "chr(" + self.chrvalue + ")"


@cdregistry.register_tag("real", CConst)
class CConstReal(CConst):
    """
    Constant real number.

    - tags[1]: string representation of real
    - tags[2]: fkind
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def realvalue(self) -> float:
        return float(self.tags[1])

    @property
    def fkind(self) -> str:
        return self.tags[2]

    @property
    def is_real(self) -> bool:
        return True

    def __str__(self) -> str:
        return str(self.realvalue)


@cdregistry.register_tag("enum", CConst)
class CConstEnum(CConst):
    """
    Constant enumeration value.

    - tags[1]: enum name
    - tags[1]: enum item name

    - args[0]: exp
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CConst.__init__(self, cd, ixval)

    @property
    def enum_name(self) -> str:
        return self.tags[1]

    @property
    def item_name(self) -> str:
        return self.tags[2]

    @property
    def exp(self) -> "CExp":
        return CConst.get_exp(self, self.args[0])

    @property
    def is_enum(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.enum_name}: {self.item_name}({self.exp})"


class CStringConstant(CDictionaryRecord):
    """Constant string value

    - tags[0]: string value or hexadecimal representation of string value
    - tags[1]: 'x' (optional) if string value is represented in hexadecimal

    - args[0] length of original string
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def stringvalue(self) -> str:
        if len(self.tags) > 0:
            return self.tags[0]
        else:  # empty string is filtered out
            return ""

    @property
    def string_length(self) -> int:
        return self.args[0]

    @property
    def is_hex(self) -> bool:
        return len(self.tags) > 1

    def __str__(self) -> str:
        if self.is_hex:
            return "(" + str(self.string_length) + "-char string"
        else:
            return self.stringvalue
