# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs
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
"""Object representation of CIL attrparam sum type


cchlib/CCHBasicTypes.attrparam =                  predicate     properties
                                                  ------------------------------
| AInt of int                                     is_int        intvalue: int
| AStr of string                                  is_str        stringvalue: str
| ACons of string * attrparam list                is_cons       name: str
                                                                params: List[CAttr]
| ASizeOf of typ                                  is_sizeof     typ: CTyp  
| ASizeOfE of attrparam                           is_sizeofe    param: CAttr
| ASizeOfS of typsig                              is_sizeofs    typsig: CTypsig
| AAlignOf of typ                                 is_alignof    typ: CTyp
| AAlignOfE of attrparam                          is_alignofe   param: CAttr
| AAlignOfS of typsig                             is_alignofs   typsig: CTypsig
| AUnOp of unop * attrparam                       is_unop       op: str
                                                                param: CAttr
| ABinOp of binop * attrparam * attrparam         is_binop      binop: str
                                                                param1: CAttr
                                                                param2: CAttr
| ADot of attrparam * string                      is_dot        suffix: str
                                                                param: CAttr
| AStar of attrparam                              is_star       param: CAttr
| AAddrOf of attrparam                            is_addrof     param: CAttr
| AIndex of attrparam * attrparam                 is_index      param1: CAttr
                                                                param2: CAttr
| AQuestion of attrparam * attrparam * attrparam  is_question   param1: CAttr
                                                                param2: CAttr
                                                                param3: CAttr

"""

from typing import List, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CTyp import CTyp
    from chc.app.CTypsig import CTypsig


class CAttr(CDictionaryRecord):
    """Attribute that comes with a C type."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_str(self) -> bool:
        return False

    @property
    def is_cons(self) -> bool:
        return False

    @property
    def is_sizeof(self) -> bool:
        return False

    @property
    def is_sizeofe(self) -> bool:
        return False

    @property
    def is_sizeofs(self) -> bool:
        return False

    @property
    def is_alignof(self) -> bool:
        return False

    @property
    def is_alignofe(self) -> bool:
        return False

    @property
    def is_alignofs(self) -> bool:
        return False

    @property
    def is_unop(self) -> bool:
        return False

    @property
    def is_binop(self) -> bool:
        return False

    @property
    def is_dot(self) -> bool:
        return False

    @property
    def is_star(self) -> bool:
        return False

    @property
    def is_addrof(self) -> bool:
        return False

    @property
    def is_index(self) -> bool:
        return False

    @property
    def is_question(self) -> bool:
        return False

    def __str__(self) -> str:
        return "attrparam:" + self.tags[0]


@cdregistry.register_tag("aint", CAttr)
class CAttrInt(CAttr):
    """Integer attribute.

    args[0]: integer value
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def intvalue(self) -> int:
        return int(self.args[0])

    @property
    def is_int(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aint(" + str(self.intvalue) + ")"


@cdregistry.register_tag("astr", CAttr)
class CAttrStr(CAttr):
    """String attribute.

    args[0]: index in string table of string attribute
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def stringvalue(self) -> str:
        return self.cd.get_string(self.args[0])

    @property
    def is_str(self) -> bool:
        return True

    def __str__(self) -> str:
        return "astr(" + str(self.stringvalue) + ")"


@cdregistry.register_tag("acons", CAttr)
class CAttrCons(CAttr):
    """Constructed attributes.

    tags[1]: name
    args[0..]: indices of attribute parameters in cdictionary.
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    @property
    def params(self) -> List[CAttr]:
        return [self.cd.get_attrparam(int(i)) for i in self.args]

    @property
    def is_cons(self) -> bool:
        return True

    def __str__(self) -> str:
        return "acons(" + str(self.name) + ")"


@cdregistry.register_tag("asizeof", CAttr)
class CAttrSizeOf(CAttr):
    """Attribute that describes the size of a type.

    args[0]: index of target type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(int(self.args[0]))

    @property
    def is_sizeof(self) -> bool:
        return True

    def __str__(self) -> str:
        return "asizeof(" + str(self.typ) + ")"


@cdregistry.register_tag("asizeofe", CAttr)
class CAttrSizeOfE(CAttr):
    """Size of an attribute parameter.

    args[0]: index of argument parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_sizeofe(self) -> bool:
        return True

    def __str__(self) -> str:
        return "asizeofe(" + str(self.param) + ")"


@cdregistry.register_tag("asizeofs", CAttr)
class CAttrSizeOfS(CAttr):
    """Replacement ASizeOf in type signatures.

    args[0]: index of target typsig in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def typsig(self) -> "CTypsig":
        return self.cd.get_typsig(int(self.args[0]))

    @property
    def is_sizeofs(self) -> bool:
        return True

    def __str__(self) -> str:
        return "asizeofs(" + str(self.typsig) + ")"


@cdregistry.register_tag("aalignof", CAttr)
class CAttrAlignOf(CAttr):
    """Alignment of a type.

    args[0]: index of target type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(int(self.args[0]))

    @property
    def is_alignof(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aalignof(" + str(self.typ) + ")"


@cdregistry.register_tag("aalignofe", CAttr)
class CAttrAlignOfE(CAttr):
    """Alignment of an attribute parameter.

    args[0]: index of attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_alignofe(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aalignofe(" + str(self.param) + ")"


@cdregistry.register_tag("aalignofs", CAttr)
class CAttrAlignOfS(CAttr):
    """Alignment of a type signature.

    args[0]: target type signature
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def typsig(self) -> "CTypsig":
        return self.cd.get_typsig(int(self.args[0]))

    @property
    def is_alignofs(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aalignofs(" + str(self.typsig) + ")"


@cdregistry.register_tag("aunop", CAttr)
class CAttrUnOp(CAttr):
    """Unary attribute parameter operation.

    tags[1]: operator
    args[0]: index of attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def op(self) -> str:
        return self.tags[1]

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_unop(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aunop(" + self.op + "," + str(self.param) + ")"


@cdregistry.register_tag("abinop", CAttr)
class CAttrBinOp(CAttr):
    """Binary attribute parameter operation.

    tags[1]: operator
    args[0]: index of first attribute parameter in cdictionary
    args[1]: index of second attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def op(self) -> str:
        return self.tags[1]

    @property
    def param1(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def param2(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[1]))

    @property
    def is_binop(self) -> bool:
        return True

    def __str__(self) -> str:
        return (
            "abinop("
            + str(self.param1)
            + " "
            + self.op
            + " "
            + str(self.param2)
            + ")"
        )


@cdregistry.register_tag("adot", CAttr)
class CAttrDot(CAttr):
    """Dot operator on attributes.

    tags[1]: string suffix
    args[0]: index of attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def suffix(self) -> str:
        return self.tags[1]

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_dot(self) -> bool:
        return True

    def __str__(self) -> str:
        return "adot(" + str(self.param) + "." + self.suffix + ")"


@cdregistry.register_tag("astr", CAttr)
class CAttrStar(CAttr):
    """Star operation on attribute.

    args[0]: index of attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_star(self) -> bool:
        return True

    def __str__(self) -> str:
        return "astar(" + str(self.param) + ")"


@cdregistry.register_tag("aaddrof", CAttr)
class CAttrAddrOf(CAttr):
    """Addressof operator on attribute.

    args[0]: index of attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def is_addrof(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aaddrof(" + str(self.param) + ")"


@cdregistry.register_tag("aindex", CAttr)
class CAttrIndex(CAttr):
    """Index operation on attributes

    args[0]: index of first attribute parameter in cdictionary
    args[1]: index of second attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param1(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def param2(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[1]))

    @property
    def is_index(self) -> bool:
        return True

    def __str__(self) -> str:
        return "aindex(" + str(self.param1) + "," + str(self.param2) + ")"


@cdregistry.register_tag("aquestion", CAttr)
class CAttrQuestion(CAttr):
    """Question operator on attributes

    args[0]: index of first attribute paramter in cdictionary
    args[1]: index of second attribute parameter in cdictionary
    args[2]: index of third attribute parameter in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CAttr.__init__(self, cd, ixval)

    @property
    def param1(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[0]))

    @property
    def param2(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[1]))

    @property
    def param3(self) -> CAttr:
        return self.cd.get_attrparam(int(self.args[2]))

    def __str__(self) -> str:
        return (
            "aquestion("
            + str(self.param1)
            + ","
            + str(self.param2)
            + ","
            + str(self.param3)
            + ")"
        )


class CAttribute(CDictionaryRecord):

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[0]

    @property
    def params(self) -> List[CAttr]:
        return [self.cd.get_attrparam(int(i)) for i in self.args]

    def __str__(self) -> str:
        return self.name + ": " + ",".join([str(p) for p in self.params])


class CAttributes(CDictionaryRecord):

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def attributes(self) -> List[CAttribute]:
        return [self.cd.get_attribute(int(i)) for i in self.args]

    @property
    def length(self) -> int:
        return len(self.attributes)

    def __str__(self) -> str:
        return ",".join([str(p) for p in self.attributes])
