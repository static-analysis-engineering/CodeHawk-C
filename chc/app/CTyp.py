# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
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

import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import xml.etree.ElementTree as ET

import chc.app.CDictionaryRecord as CD

if TYPE_CHECKING:
    import chc.app.CDictionary
    import chc.app.CExp as CE
    import chc.app.CAttributes as CA

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


class CTypBase(CD.CDictionaryRecord):
    """Variable type. """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def expand(self) -> "CTypBase":
        return self

    def strip_attributes(self) -> "CTypBase":
        aindex = attribute_index[self.tags[0]]
        if aindex >= len(self.args):
            return self
        elif self.args[aindex] == 1:
            return self
        else:
            newargs = self.args[:-1]
            newtypix = self.cd.mk_typ(self.tags, newargs)
            if newtypix != self.index:
                newtyp = self.cd.get_typ(newtypix)
                logging.info(
                    "Stripping attributes "
                    + self.get_attributes_string()
                    + " ; changing type from "
                    + str(self)
                    + " to "
                    + str(newtyp)
                )
            return newtyp

    def get_typ(self, ix: int) -> "CTypBase":
        return self.cd.get_typ(ix)

    def get_exp(self, ix: int) -> "CE.CExpBase":
        return self.cd.get_exp(ix)

    def get_exp_opt(self, ix: int) -> Optional["CE.CExpBase"]:
        return self.cd.get_exp_opt(ix)

    def get_size(self) -> int:
        return -1000

    def get_attributes(self) -> "CA.CAttributes":
        aindex = attribute_index[self.tags[0]]
        if len(self.args) > aindex:
            return self.cd.get_attributes(int(self.args[aindex]))
        else:
            return self.cd.get_attributes(1)

    def get_attributes_string(self) -> str:
        attrs = self.get_attributes()
        if attrs.length() > 0:
            return "[" + str(attrs) + "]"
        else:
            return ""

    def equal(self, other: "CTypBase") -> bool:
        return self.expand().index == other.expand().index

    def is_array(self) -> bool:
        return False

    def is_builtin_vaargs(self) -> bool:
        return False

    def is_comp(self) -> bool:
        return False

    def is_enum(self) -> bool:
        return False

    def is_float(self) -> bool:
        return False

    def is_function(self) -> bool:
        return False

    def is_int(self) -> bool:
        return False

    def is_named_type(self) -> bool:
        return False

    def is_pointer(self) -> bool:
        return False

    def is_struct(self) -> bool:
        return False

    def is_void(self) -> bool:
        return False

    def is_default_function_prototype(self) -> bool:
        return False

    def writexml(self, cnode: ET.Element) -> None:
        cnode.set("ix", str(self.index))
        cnode.set("tags", ",".join(self.tags))
        cnode.set("args", ",".join([str(int(x)) for x in self.args]))

    def __str__(self) -> str:
        return "typebase:" + self.tags[0]

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "type"}

    def to_idict(self) -> Dict[str, Any]:
        return {"t": self.tags, "a": self.args}


class CTypVoid(CTypBase):
    """
    tags:
        0: 'tvoid'

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def is_void(self) -> bool:
        return True

    def get_opaque_type(self) -> CTypBase:
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "void"}

    def __str__(self) -> str:
        return "void" + "[" + str(self.get_attributes()) + "]"


class CTypInt(CTypBase):
    """
    tags:
        0: 'tint'
        1: ikind

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def is_int(self) -> bool:
        return True

    def get_size(self) -> int:
        k = self.get_kind()
        if "char" in integernames[k]:
            return 1
        else:
            return 4  # TBD: adjust for other kinds

    def get_kind(self) -> str:
        return self.tags[1]

    def get_opaque_type(self) -> CTypBase:
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "int", "kind": self.get_kind()}

    def __str__(self) -> str:
        return integernames[self.get_kind()] + str(self.get_attributes_string())


class CTypFloat(CTypBase):
    """
    tags:
        0: 'tfloat'
        1: fkind

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def is_float(self) -> bool:
        return True

    def get_kind(self) -> str:
        return self.tags[1]

    def get_size(self) -> int:
        return 4  # TBD: adjust for kind

    def get_opaque_type(self) -> CTypBase:
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "float", "kind": self.get_kind()}

    def __str__(self) -> str:
        return floatnames[self.get_kind()]


class CTypNamed(CTypBase):
    """
    tags:
        0: 'tnamed'
        1: tname

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_name(self) -> str:
        return self.tags[1]

    def expand(self):
        return self.cd.decls.expand(self.get_name())

    def get_size(self) -> int:
        return self.expand().get_size()

    def is_named_type(self) -> bool:
        return True

    def get_opaque_type(self):
        return self.expand().get_opaque_type()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "named",
            "name": self.get_name(),
            "expand": self.expand().to_dict(),
        }

    def __str__(self) -> str:
        return self.get_name() + str(self.get_attributes_string())


class CTypComp(CTypBase):
    """
    tags:
        0: 'tcomp'

    args:
        0: ckey
        1: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_ckey(self) -> int:
        return self.args[0]

    def get_struct(self):
        return self.cd.decls.get_struct(self.get_ckey())

    def get_name(self):
        return self.cd.decls.get_structname(self.get_ckey())

    def is_struct(self):
        return self.cd.decls.is_struct(self.get_ckey())

    def get_size(self) -> int:
        return self.get_struct().get_size()

    def is_comp(self) -> bool:
        return True

    def get_opaque_type(self):
        tags = ["tvoid"]
        args = []
        return self.cd.get_typ(self.cd.mk_typ(tags, args))

    def to_dict(self):
        return {
            "base": "struct",
            "kind": "struct" if self.is_struct() else "union",
            "name": self.get_name(),
            "key": self.get_ckey(),
        }

    def __str__(self) -> str:
        if self.is_struct():
            return "struct " + self.get_name() + "(" + str(self.get_ckey()) + ")"
        else:
            return "union " + self.get_name() + "(" + str(self.get_ckey()) + ")"


class CTypEnum(CTypBase):
    """
    tags:
        0: 'tenum'
        1: ename

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_name(self):
        return self.tags[1]

    def get_size(self):
        return 4

    def is_enum(self):
        return True

    def get_opaque_type(self):
        tags = ["tint", "iint"]
        args = []
        return self.cd.get_typ(self.cd.mk_typ(tags, args))

    def to_dict(self):
        return {"base": "enum", "name": self.get_name()}

    def __str__(self) -> str:
        return "enum " + self.get_name()


class CTypBuiltinVaargs(CTypBase):
    """
    tags:
        0: 'tbuiltinvaargs'

    args:
        0: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def is_builtin_vaargs(self) -> bool:
        return True

    def get_opaque_type(self):
        return self

    def to_dict(self):
        return {"base": "builtin_vaargs"}

    def __str__(self) -> str:
        return "tbuiltin_va_args"


class CTypPtr(CTypBase):
    """
    tags:
        0: 'tptr'

    args:
        0: pointed-to type
        1: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_pointedto_type(self):
        return self.get_typ(self.args[0])

    def get_size(self) -> int:
        return 4

    def is_pointer(self) -> bool:
        return True

    def get_opaque_type(self):
        tgttype = self.get_pointedto_type().get_opaque_type()
        tags = ["tptr"]
        args = [self.cd.index_typ(tgttype)]
        return self.cd.get_typ(self.cd.mk_typ(tags, args))

    def to_dict(self):
        return {"base": "ptr", "tgt": self.get_pointedto_type().to_dict()}

    def __str__(self) -> str:
        return "(" + str(self.get_pointedto_type()) + " *)"


class CTypArray(CTypBase):
    """
    tags:
        0: 'tarray'

    args:
        0: base type
        1: size expression (optional)
        2: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_array_basetype(self):
        return self.get_typ(self.args[0])

    def get_array_size_expr(self):
        return self.get_exp_opt(self.args[1])

    def has_array_size_expr(self):
        return self.args[1] >= 0

    def get_size(self) -> int:
        try:
            if self.has_array_size_expr():
                return (
                    self.get_array_basetype().get_size()
                    * self.get_array_size_expr().get_constant().get_int()
                )
        except BaseException:
            return -1000
        else:
            return -1000

    def is_array(self) -> bool:
        return True

    def get_opaque_type(self):
        tags = ["tvoid"]
        args = []
        return self.cd.get_typ(self.cd.mk_typ(tags, args))

    def to_dict(self):
        result = {"base": "array", "elem": self.get_array_basetype().to_dict()}
        if self.has_array_size_expr() and self.get_array_size_expr().is_constant():
            result["size"] = str(self.get_array_size_expr())
        return result

    def __str__(self) -> str:
        size = self.get_array_size_expr()
        ssize = str(size) if size is not None else "?"
        return str(self.get_array_basetype()) + "[" + ssize + "]"


class CTypFun(CTypBase):
    """
    tags:
        0: 'tfun'

    args:
        0: return type
        1: argument types list (optional)
        2: varargs
        3: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CTypBase.__init__(self, cd, index, tags, args)

    def get_return_type(self):
        return self.get_typ(self.args[0])

    def get_args(self) -> Optional["CFunArgs"]:
        return self.cd.get_funargs_opt(self.args[1])

    def get_size(self) -> int:
        return 4

    def is_function(self) -> bool:
        return True

    def get_opaque_type(self) -> CTypBase:
        tags = ["tvoid"]
        args: List[int] = []
        return self.cd.get_typ(self.cd.mk_typ(tags, args))

    def is_default_function_prototype(self):
        args = self.get_args()
        if args is None:
            return True
        else:
            args = args.get_args()
            return len(args) > 0 and all(
                [x.get_name().startswith("$par$") for x in args]
            )

    def is_vararg(self) -> bool:
        return self.args[2] == 1

    def strip_attributes(self) -> CTypBase:
        rtype = self.get_return_type().strip_attributes()
        if rtype.index != self.get_return_type().index:
            newargs = self.args[:]
            newargs[0] = rtype.index
            newtypix = self.cd.mk_typ(self.tags, newargs)
            newtyp = self.cd.get_typ(newtypix)
            logging.info(
                "Change function type from " + str(self) + " to " + str(newtyp)
            )
            return newtyp
        else:
            return self

    def to_dict(self):
        result = {"base": "fun", "rvtype": self.get_return_type().to_dict()}
        if self.is_default_function_prototype():
            result["default"] = "true"
        else:
            result["args"] = self.get_args().to_dict()
        return result

    def __str__(self) -> str:
        rtyp = self.get_return_type()
        args = self.get_args()
        return "(" + str(args) + "):" + str(rtyp)


class CFunArg(CD.CDictionaryRecord):
    """
    tags:
        0: argument name

    args:
        0: argument type
        1: attributes
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def get_name(self):
        if len(self.tags) > 0:
            return self.tags[0]
        else:
            return "__"

    def get_type(self):
        return self.cd.get_typ(self.args[0])

    def to_dict(self):
        return self.get_type().to_dict()

    def __str__(self) -> str:
        return str(self.get_type()) + " " + self.get_name()


class CFunArgs(CD.CDictionaryRecord):
    """
    tags: -

    args: function arguments
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def get_args(self):
        return [self.cd.get_funarg(i) for i in self.args]

    def to_dict(self):
        return [a.to_dict() for a in self.get_args()]

    def __str__(self) -> str:
        return ", ".join([str(x) for x in self.get_args()])
