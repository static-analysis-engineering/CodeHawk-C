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
"""Variant type for the CIL **typ** data type."""

import xml.etree.ElementTree as ET

from typing import Any, cast, Dict, List, Optional, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExp, CExpConst
    from chc.app.CAttributes import CAttributes
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CConst import CConst, CConstInt


integernames = {
    "ichar": "char",
    "ischar": "signed char",
    "iuchar": "unsigned char",
    "ibool": "bool",
    "iint": "int",
    "iuint": "unsigned int",
    "ishort": "short",
    "iushort": "unsigned short",
    "ilong": "long",
    "iulong": "unsigned long",
    "ilonglong": "long long",
    "iulonglong": "unsigned long long",
}

floatnames = {"float": "float", "fdouble": "double", "flongdouble": "long double"}

attribute_index = {
    "tvoid": 0,
    "tint": 0,
    "tfloat": 0,
    "tptr": 1,
    "tarray": 2,
    "tfun": 3,
    "tnamed": 0,
    "tcomp": 1,
    "tenum": 0,
    "tbuiltin-va-list": 0,
}


class CTyp(CDictionaryRecord):
    """Base class of all variable types."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    def expand(self) -> "CTyp":
        return self

    def strip_attributes(self) -> "CTyp":
        aindex = attribute_index[self.tags[0]]
        if aindex >= len(self.args):
            return self
        elif self.args[aindex] == 1:
            return self
        else:
            newargs = self.args[:-1]
            newtypix = self.cd.mk_typ_index(self.tags, newargs)
            if newtypix != self.index:
                newtyp = self.cd.get_typ(newtypix)
                chklogger.logger.info(
                    "Stripping attributes %s ; changing type from %s to %s",
                    self.attributes_string,
                    str(self),
                    str(newtyp))
            return newtyp

    def get_typ(self, ix: int) -> "CTyp":
        return self.cd.get_typ(ix)

    def get_exp(self, ix: int) -> "CExp":
        return self.cd.get_exp(ix)

    def get_exp_opt(self, ix: int) -> Optional["CExp"]:
        return self.cd.get_exp_opt(ix)

    @property
    def size(self) -> int:
        return -1000

    @property
    def attributes(self) -> "CAttributes":
        aindex = attribute_index[self.tags[0]]
        if len(self.args) > aindex:
            return self.cd.get_attributes(int(self.args[aindex]))
        else:
            return self.cd.get_attributes(1)

    @property
    def attributes_string(self) -> str:
        attrs = self.attributes
        if attrs.length > 0:
            return "[" + str(attrs) + "]"
        else:
            return ""

    def get_opaque_type(self) -> "CTyp":
        return self

    def equal(self, other: "CTyp") -> bool:
        return self.expand().index == other.expand().index

    @property
    def is_array(self) -> bool:
        return False

    @property
    def is_builtin_vaargs(self) -> bool:
        return False

    @property
    def is_comp(self) -> bool:
        return False

    @property
    def is_enum(self) -> bool:
        return False

    @property
    def is_float(self) -> bool:
        return False

    @property
    def is_function(self) -> bool:
        return False

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_named_type(self) -> bool:
        return False

    @property
    def is_pointer(self) -> bool:
        return False

    @property
    def is_struct(self) -> bool:
        return False

    @property
    def is_void(self) -> bool:
        return False

    @property
    def is_default_function_prototype(self) -> bool:
        return False

    def writexml(self, cnode: ET.Element) -> None:
        cnode.set("ix", str(self.index))
        cnode.set("tags", ",".join(self.tags))
        cnode.set("args", ",".join([str(int(x)) for x in self.args]))

    def __str__(self) -> str:
        return "typebase:" + self.tags[0]

    def to_dict(self) -> Dict[str, object]:
        return {"base": "type"}

    def to_idict(self) -> Dict[str, object]:
        return {"t": self.tags, "a": self.args}


@cdregistry.register_tag("tvoid", CTyp)
class CTypVoid(CTyp):
    """ Void type.

    * args[0]: attributes
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def is_void(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        return self

    def to_dict(self) -> Dict[str, object]:
        return {"base": "void"}

    def __str__(self) -> str:
        return "void" + "[" + str(self.attributes) + "]"


@cdregistry.register_tag("tint", CTyp)
class CTypInt(CTyp):
    """ Integer type.

    * tags[1]: ikind

    * args[0]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def is_int(self) -> bool:
        return True

    @property
    def size(self) -> int:
        k = self.ikind
        if "char" in integernames[k]:
            return 1
        else:
            return 4  # TBD: adjust for other kinds

    @property
    def ikind(self) -> str:
        return self.tags[1]

    def get_opaque_type(self) -> CTyp:
        return self

    def to_dict(self) -> Dict[str, object]:
        return {"base": "int", "kind": self.ikind}

    def __str__(self) -> str:
        return integernames[self.ikind] + str(self.attributes_string)


@cdregistry.register_tag("tfloat", CTyp)
class CTypFloat(CTyp):
    """ Float type.

    * tags[1]: fkind

    * args[0]: attributes
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def is_float(self) -> bool:
        return True

    @property
    def fkind(self) -> str:
        return self.tags[1]

    @property
    def size(self) -> int:
        return 4  # TBD: adjust for kind

    def get_opaque_type(self) -> CTyp:
        return self

    def to_dict(self) -> Dict[str, object]:
        return {"base": "float", "kind": self.fkind}

    def __str__(self) -> str:
        return floatnames[self.fkind]


@cdregistry.register_tag("tnamed", CTyp)
class CTypNamed(CTyp):
    """Type definition

    * tags[1]: tname

    * args[0]: attributes
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    def expand(self) -> CTyp:
        return self.cd.decls.expand(self.name)

    @property
    def size(self) -> int:
        return self.expand().size

    @property
    def is_named_type(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        return self.expand().get_opaque_type()

    def to_dict(self) -> Dict[str, object]:
        return {
            "base": "named",
            "name": self.name,
            "expand": self.expand().to_dict(),
        }

    def __str__(self) -> str:
        return self.name + str(self.attributes_string)


@cdregistry.register_tag("tcomp", CTyp)
class CTypComp(CTyp):
    """Struct type (composite type; also includes union)

    * tags[0]: struct name

    * args[0]: ckey
    * args[1]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def ckey(self) -> int:
        return self.args[0]

    @property
    def compinfo(self) -> "CCompInfo":
        return self.decls.get_compinfo_by_ckey(self.ckey)

    @property
    def name(self) -> str:
        return self.compinfo.name

    @property
    def is_struct(self) -> bool:
        return self.compinfo.is_struct

    @property
    def size(self) -> int:
        return self.compinfo.size

    @property
    def is_comp(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        tags = ["tvoid"]
        args: List[int] = []
        return self.cd.get_typ(self.cd.mk_typ_index(tags, args))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "struct",
            "kind": "struct" if self.is_struct else "union",
            "name": self.name,
            "key": self.ckey,
        }

    def __str__(self) -> str:
        if self.is_struct:
            return "struct " + self.name + "(" + str(self.ckey) + ")"
        else:
            return "union " + self.name + "(" + str(self.ckey) + ")"


@cdregistry.register_tag("tenum", CTyp)
class CTypEnum(CTyp):
    """Enum type.

    * tags[1]: name of enum (ename)
    * args[0]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    @property
    def size(self) -> int:
        return 4

    @property
    def is_enum(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        tags = ["tint", "iint"]
        args: List[int] = []
        return self.cd.get_typ(self.cd.mk_typ_index(tags, args))

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "enum", "name": self.name}

    def __str__(self) -> str:
        return "enum " + self.name


@cdregistry.register_tag("tbuiltinvaargs", CTyp)
@cdregistry.register_tag("tbuiltin-va-list", CTyp)
class CTypBuiltinVaargs(CTyp):
    """Builtin variable arguments

    * args[0]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def is_builtin_vaargs(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "builtin_vaargs"}

    def __str__(self) -> str:
        return "tbuiltin_va_args"


@cdregistry.register_tag("tptr", CTyp)
class CTypPtr(CTyp):
    """ Pointer type

    * args[0]: index of pointed-to type in cdictionary
    * args[1]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def pointedto_type(self) -> CTyp:
        return self.get_typ(self.args[0])

    @property
    def size(self) -> int:
        return 4

    @property
    def is_pointer(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        tgttype = self.pointedto_type.get_opaque_type()
        tags = ["tptr"]
        args = [self.cd.index_typ(tgttype)]
        return self.cd.get_typ(self.cd.mk_typ_index(tags, args))

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "ptr", "tgt": self.pointedto_type.to_dict()}

    def __str__(self) -> str:
        return "(" + str(self.pointedto_type) + " *)"


@cdregistry.register_tag("tarray", CTyp)
class CTypArray(CTyp):
    """ Array type

    * args[0]: index of base type in cdictionary
    * args[1]: index of size expression in cdictionary (optional)
    * args[2]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def array_basetype(self) -> CTyp:
        return self.get_typ(self.args[0])

    @property
    def array_size_expr(self) -> "CExp":
        if self.args[1] >= 0:
            return self.get_exp(self.args[1])
        else:
            raise UF.CHCError("Array type does not have a size")

    def has_array_size_expr(self) -> bool:
        return self.args[1] >= 0

    @property
    def size(self) -> int:
        try:
            if self.has_array_size_expr():
                array_size_const = cast(
                    "CExpConst", self.array_size_expr).constant
                array_size_int = cast(
                    "CConstInt", array_size_const).intvalue
                return self.array_basetype.size * array_size_int
        except BaseException:
            return -1000
        else:
            return -1000

    @property
    def is_array(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        tags = ["tvoid"]
        args: List[int] = []
        return self.cd.get_typ(self.cd.mk_typ_index(tags, args))

    def to_dict(self) -> Dict[str, Any]:
        result = {"base": "array", "elem": self.array_basetype.to_dict()}
        if self.has_array_size_expr() and self.array_size_expr.is_constant:
            result["size"] = str(self.array_size_expr)
        return result

    def __str__(self) -> str:
        size = self.array_size_expr
        ssize = str(size) if size is not None else "?"
        return str(self.array_basetype) + "[" + ssize + "]"


@cdregistry.register_tag("tfun", CTyp)
class CTypFun(CTyp):
    """Function type

    * args[0]: index of return type in cdictionary
    * args[1]: index of argument types list in cdictionary (optional
    * args[2]: 1 = varargs
    * args[3]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTyp.__init__(self, cd, ixval)

    @property
    def return_type(self) -> CTyp:
        return self.get_typ(self.args[0])

    @property
    def funargs(self) -> Optional["CFunArgs"]:
        return self.cd.get_funargs_opt(self.args[1])

    @property
    def size(self) -> int:
        return 4

    @property
    def is_function(self) -> bool:
        return True

    def get_opaque_type(self) -> CTyp:
        tags = ["tvoid"]
        args: List[int] = []
        return self.cd.get_typ(self.cd.mk_typ_index(tags, args))

    @property
    def is_default_function_prototype(self) -> bool:
        funargs = self.funargs
        if funargs is None:
            return True
        else:
            args = funargs.arguments
            return len(args) > 0 and all(
                [x.name.startswith("$par$") for x in args]
            )

    @property
    def is_vararg(self) -> bool:
        return self.args[2] == 1

    def strip_attributes(self) -> CTyp:
        rtype = self.return_type.strip_attributes()
        if rtype.index != self.return_type.index:
            newargs = self.args[:]
            newargs[0] = rtype.index
            newtypix = self.cd.mk_typ_index(self.tags, newargs)
            newtyp = self.cd.get_typ(newtypix)
            chklogger.logger.info(
                "Change function type from %s to %s", str(self), str(newtyp))
            return newtyp
        else:
            return self

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "base": "fun", "rvtype": self.return_type.to_dict()}
        if self.is_default_function_prototype:
            result["default"] = "true"
        elif self.funargs is not None:
            result["args"] = self.funargs.to_dict()
        return result

    def __str__(self) -> str:
        rtyp = self.return_type
        args = self.funargs
        return "(" + str(args) + "):" + str(rtyp)


class CFunArg(CDictionaryRecord):
    """Function argument

    * tags[0]: argument name
    * args[0]: index of argument type in cdictionary
    * args[1]: index of attributes in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        if len(self.tags) > 0:
            return self.tags[0]
        else:
            return "__"

    @property
    def typ(self) -> CTyp:
        return self.cd.get_typ(self.args[0])

    def to_dict(self) -> Dict[str, Any]:
        return self.typ.to_dict()

    def __str__(self) -> str:
        return str(self.typ) + " " + self.name


class CFunArgs(CDictionaryRecord):
    """Function arguments

    * args[0..]: indices of function arguments in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def arguments(self) -> List[CFunArg]:
        return [self.cd.get_funarg(i) for i in self.args]

    def to_dict(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.arguments]

    def __str__(self) -> str:
        return "(" + ", ".join([str(x) for x in self.arguments]) + ")"
