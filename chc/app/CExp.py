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

from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import chc.app.CDictionaryRecord as CD

if TYPE_CHECKING:
    import chc.app.CDictionary
    import chc.app.CConstExp as CC
    import chc.app.CTyp as CT
    import chc.app.CLval as CV

binoperatorstrings = {
    "band": "&",
    "bor": "|",
    "bxor": "^",
    "div": "/",
    "eq": "==",
    "ge": ">=",
    "gt": ">",
    "indexpi": "+",
    "land": "&&",
    "le": "<=",
    "lor": "||",
    "lt": "<",
    "minusa": "-",
    "minuspi": "-",
    "minuspp": "-",
    "mod": "%",
    "mult": "*",
    "ne": "!=",
    "plusa": "+",
    "pluspi": "+",
    "shiftlt": "<<",
    "shiftrt": ">>",
}

unoperatorstrings = {"neg": "-", "bnot": "~", "lnot": "!"}


class CExpBase(CD.CDictionaryRecord):
    """Base class for all expressions."""

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def is_binop(self) -> bool:
        return False

    def is_caste(self) -> bool:
        return False

    def is_constant(self) -> bool:
        return False

    def is_lval(self) -> bool:
        return False

    def is_sizeof(self) -> bool:
        return False

    def is_sizeofe(self) -> bool:
        return False

    def is_sizeofstr(self) -> bool:
        return False

    def is_addrof(self) -> bool:
        return False

    def is_startof(self) -> bool:
        return False

    def is_unop(self) -> bool:
        return False

    def is_alignof(self) -> bool:
        return False

    def is_alignofe(self) -> bool:
        return False

    def is_fn_app(self) -> bool:
        return False

    def is_cn_app(self) -> bool:
        return False

    def has_variable(self, vid: int) -> bool:
        return False

    def has_variable_op(self, vid: int, op: str) -> bool:
        return False

    def get_strings(self) -> List[str]:
        return []

    def get_variable_uses(self, vid: int) -> int:
        return 0

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "exp"}

    def to_idict(self) -> Dict[str, Any]:
        return {"t": self.tags, "a": self.args}

    def __str__(self) -> str:
        return "baseexp:" + self.tags[0]


@CD.c_dictionary_record_tag("const")
class CExpConst(CExpBase):
    """
    tags:
        0: 'const'

    args:
        0: constant
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def is_constant(self) -> bool:
        return True

    def get_constant(self) -> 'CC.CConstBase':
        return self.cd.get_constant(self.args[0])

    def get_strings(self) -> List[str]:
        return self.get_constant().get_strings()

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "const", "value": str(self.get_constant())}

    def __str__(self) -> str:
        return str(self.get_constant())


@CD.c_dictionary_record_tag("lval")
class CExpLval(CExpBase):
    """
    tags:
        0: 'lval'

    args:
        0: lval
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_lval(self) -> "CV.CLval":
        return self.cd.get_lval(self.args[0])

    def is_lval(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_lval().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_lval().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_lval().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "lval", "lval": self.get_lval().to_dict()}

    def __str__(self) -> str:
        return str(self.get_lval())


@CD.c_dictionary_record_tag("sizeof")
class CExpSizeOf(CExpBase):
    """
    tags:
        0: 'sizeof'

    args:
        0: typ
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[0])

    def is_sizeof(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeof", "type": self.get_type().to_dict()}

    def __str__(self) -> str:
        return "sizeof(" + str(self.get_type()) + ")"


@CD.c_dictionary_record_tag("sizeofe")
class CExpSizeOfE(CExpBase):
    """
    tags:
        0: 'sizeofe'

    args:
        0: exp
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[0])

    def is_sizeofe(self) -> bool:
        return True

    def get_strings(self) -> List[str]:
        return self.get_exp().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_exp().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeofe", "exp": self.get_exp().to_dict()}

    def __str__(self) -> str:
        return "sizeofe(" + str(self.get_exp()) + ")"


@CD.c_dictionary_record_tag("sizeofstr")
class CExpSizeOfStr(CExpBase):
    """
    tags:
        0: 'sizeofstr'

    args:
        0: string index
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_string(self) -> str:
        return self.cd.get_string(self.args[0])

    def get_strings(self) -> List[str]:
        return [self.get_string()]

    def is_sizeofstr(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeofstr", "string": self.get_string()}

    def __str__(self) -> str:
        return "sizeofstr(" + str(self.get_string()) + ")"


@CD.c_dictionary_record_tag("alignof")
class CExpAlignOf(CExpBase):
    """
    tags:
        0: 'alignof'

    args:
        0: typ
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[0])

    def is_alignof(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "alignof", "type": self.get_type().to_dict()}

    def __str__(self) -> str:
        return "alignof(" + str(self.get_type()) + ")"


@CD.c_dictionary_record_tag("alignofe")
class CExpAlignOfE(CExpBase):
    """
    tags:
        0: 'alignofe'

    args:
        0: exp
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def is_alignofe(self) -> bool:
        return True

    def get_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[0])

    def has_variable(self, vid: int) -> bool:
        return self.get_exp().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_exp().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_exp().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "alignofe", "exp": self.get_exp().to_dict()}

    def __str__(self) -> str:
        return "alignofe(" + str(self.get_exp()) + ")"


@CD.c_dictionary_record_tag("unop")
class CExpUnOp(CExpBase):
    """
    tags:
        0: 'unop'
        1: unop operator

    args:
        0: exp
        1: typ
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[0])

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[1])

    def get_op(self) -> str:
        return self.tags[1]

    def is_unop(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_exp().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_exp().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_exp().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "unop", "op": self.get_op(), "exp": self.get_exp().to_dict()}

    def __str__(self) -> str:
        return "(" + unoperatorstrings[self.get_op()] + " " + str(self.get_exp()) + ")"


@CD.c_dictionary_record_tag("binop")
class CExpBinOp(CExpBase):
    """
    tags:
        0: 'binop'
        1: binop operator

    args:
        0: exp1
        1: exp2
        2 typ
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_exp1(self) -> CExpBase:
        return self.cd.get_exp(self.args[0])

    def get_exp2(self) -> CExpBase:
        return self.cd.get_exp(self.args[1])

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[2])

    def get_op(self) -> str:
        return self.tags[1]

    def is_binop(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)

    def has_variable_op(self, vid: int, op: str) -> bool:
        return (
            self.get_exp1().has_variable(vid) or self.get_exp2().has_variable(vid)
        ) and (op == binoperatorstrings[self.get_op()])

    def get_strings(self) -> List[str]:
        c1 = self.get_exp1().get_strings()
        c2 = self.get_exp2().get_strings()
        return c1 + c2

    def get_variable_uses(self, vid: int) -> int:
        c1 = self.get_exp1().get_variable_uses(vid)
        c2 = self.get_exp2().get_variable_uses(vid)
        return c1 + c2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "binop",
            "op": self.get_op(),
            "exp1": self.get_exp1().to_dict(),
            "exp2": self.get_exp2().to_dict(),
        }

    def __str__(self) -> str:
        return (
            "("
            + str(self.get_exp1())
            + " "
            + binoperatorstrings[self.get_op()]
            + " "
            + str(self.get_exp2())
            + ")"
            + ":"
            + str(self.get_type())
        )


@CD.c_dictionary_record_tag("question")
class CExpQuestion(CExpBase):
    """
    tags:
        0: 'question'

    args:
        0: conditional exp
        1: if-true exp
        2: if-false exp
        3: typ
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_condition(self) -> CExpBase:
        return self.cd.get_exp(self.args[0])

    def get_true_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[1])

    def get_false_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[2])

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[3])

    def has_variable(self, vid: int) -> bool:
        return (
            self.get_condition().has_variable(vid)
            or self.get_true_exp().has_variable(vid)
            or self.get_false_exp().has_variable(vid)
        )

    def get_strings(self) -> List[str]:
        c = self.get_condition().get_strings()
        t = self.get_true_exp().get_strings()
        f = self.get_false_exp().get_strings()
        return c + t + f

    def get_variable_uses(self, vid: int) -> int:
        c = self.get_condition().get_variable_uses(vid)
        t = self.get_true_exp().get_variable_uses(vid)
        f = self.get_false_exp().get_variable_uses(vid)
        return c + t + f

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "question",
            "cond": self.get_condition().to_dict(),
            "true-exp": self.get_true_exp().to_dict(),
            "false-exp": self.get_false_exp().to_dict(),
            "type": self.get_type().to_dict(),
        }

    def __str__(self) -> str:
        return (
            "("
            + str(self.get_condition())
            + " ? "
            + str(self.get_true_exp())
            + " : "
            + str(self.get_false_exp())
            + ")"
        )


@CD.c_dictionary_record_tag("caste")
class CExpCastE(CExpBase):
    """
    tags:
        0: 'caste'

    args:
        0: target typ
        1: exp
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_exp(self) -> CExpBase:
        return self.cd.get_exp(self.args[1])

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[0])

    def is_caste(self) -> bool:
        return True

    def get_strings(self) -> List[str]:
        return self.get_exp().get_strings()

    def has_variable(self, vid: int) -> bool:
        return self.get_exp().has_variable(vid)

    def get_variable_uses(self, vid: int) -> int:
        return self.get_exp().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "caste",
            "exp": self.get_exp().to_dict(),
            "type": self.get_type().to_dict(),
        }

    def __str__(self) -> str:
        return "caste(" + str(self.get_type()) + "," + str(self.get_exp()) + ")"


@CD.c_dictionary_record_tag("addrof")
class CExpAddrOf(CExpBase):
    """
    tags:
        0: 'addrof'

    args:
        0: lval
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_lval(self) -> "CV.CLval":
        return self.cd.get_lval(self.args[0])

    def is_addrof(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_lval().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_lval().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_lval().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "addrof", "lval": self.get_lval().to_dict()}

    def __str__(self) -> str:
        return "&(" + str(self.get_lval()) + ")"


@CD.c_dictionary_record_tag("addroflabel")
class CExpAddrOfLabel(CExpBase):
    """
    tags:
        0: 'addoflabel'

    args:
        0: statement sid
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_label(self) -> int:
        return self.args[0]

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "addroflabel", "label": self.get_label()}

    def __str__(self) -> str:
        return "addroflabel(" + str(self.get_label()) + ")"


@CD.c_dictionary_record_tag("startof")
class CExpStartOf(CExpBase):
    """
    tags:
        0: 'startof'

    args:
        0: lval
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_lval(self) -> "CV.CLval":
        return self.cd.get_lval(self.args[0])

    def is_startof(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_lval().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_lval().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_lval().get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "startof", "lval": self.get_lval().to_dict()}

    def __str__(self) -> str:
        return "&(" + str(self.get_lval()) + ")"


@CD.c_dictionary_record_tag("fnapp")
class CExpFnApp(CExpBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def is_fn_app(self) -> bool:
        return True


@CD.c_dictionary_record_tag("cnapp")
class CExpCnApp(CExpBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CExpBase.__init__(self, cd, index, tags, args)

    def get_name(self) -> str:
        return self.tags[1]

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(int(self.args[0]))

    def get_args(self) -> List[CExpBase]:
        return [self.cd.get_exp(int(i)) for i in self.args[1:]]

    def has_variable(self, vid: int) -> bool:
        return any([a.has_variable(vid) for a in self.get_args()])

    def is_cn_app(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.get_name() + "(" + ",".join([str(a) for a in self.get_args()]) + ")"
