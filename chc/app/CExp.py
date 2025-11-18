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
"""Object representation of CIL expression sum type."""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CConst import CConst
    from chc.app.CTyp import CTyp
    from chc.app.CLval import CLval
    from chc.app.CVisitor import CVisitor


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


class CExp(CDictionaryRecord):
    """Base class for all expressions."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def is_binop(self) -> bool:
        return False

    @property
    def is_caste(self) -> bool:
        return False

    @property
    def is_constant(self) -> bool:
        return False

    @property
    def is_lval(self) -> bool:
        return False

    @property
    def is_question(self) -> bool:
        return False

    @property
    def is_sizeof(self) -> bool:
        return False

    @property
    def is_sizeofe(self) -> bool:
        return False

    @property
    def is_sizeofstr(self) -> bool:
        return False

    @property
    def is_addrof(self) -> bool:
        return False

    @property
    def is_startof(self) -> bool:
        return False

    @property
    def is_unop(self) -> bool:
        return False

    @property
    def is_alignof(self) -> bool:
        return False

    @property
    def is_alignofe(self) -> bool:
        return False

    @property
    def is_fn_app(self) -> bool:
        return False

    @property
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

    def accept(self, visitor: "CVisitor") -> None:
        raise UF.CHCError("visitor not yet implemented for: " + str(self))

    def __str__(self) -> str:
        return "baseexp:" + self.tags[0]


@cdregistry.register_tag("const", CExp)
class CExpConst(CExp):
    """
    Constant expression

    - args[0]: constant
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def is_constant(self) -> bool:
        return True

    @property
    def constant(self) -> "CConst":
        return self.cd.get_constant(self.args[0])

    def get_strings(self) -> List[str]:
        return self.constant.get_strings()

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_constexp(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "const", "value": str(self.constant)}

    def __str__(self) -> str:
        return str(self.constant)


@cdregistry.register_tag("lval", CExp)
class CExpLval(CExp):
    """ Lvalue expression.

    - args[0]: index of lval in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(self.args[0])

    @property
    def is_lval(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.lval.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.lval.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.lval.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "lval", "lval": self.lval.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_explval(self)

    def __str__(self) -> str:
        return str(self.lval)


@cdregistry.register_tag("sizeof", CExp)
class CExpSizeOf(CExp):
    """ Sizeof type expression.

    - args[0]: index of target type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def is_sizeof(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeof", "type": self.typ.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_sizeof(self)

    def __str__(self) -> str:
        return "sizeof(" + str(self.typ) + ")"


@cdregistry.register_tag("sizeofe", CExp)
class CExpSizeOfE(CExp):
    """ Sizeof expression expression

    - args[0]: exp
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def exp(self) -> CExp:
        return self.cd.get_exp(self.args[0])

    @property
    def is_sizeofe(self) -> bool:
        return True

    def get_strings(self) -> List[str]:
        return self.exp.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.exp.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeofe", "exp": self.exp.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_sizeofe(self)

    def __str__(self) -> str:
        return "sizeofe(" + str(self.exp) + ")"


@cdregistry.register_tag("sizeofstr", CExp)
class CExpSizeOfStr(CExp):
    """ Sizeof string expression

    - args[0]:index of  string in the string table
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def stringvalue(self) -> str:
        return self.cd.get_string(self.args[0])

    def get_strings(self) -> List[str]:
        return [self.stringvalue]

    @property
    def is_sizeofstr(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "sizeofstr", "string": self.stringvalue}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_size_of_str(self)

    def __str__(self) -> str:
        return "sizeofstr(" + str(self.stringvalue) + ")"


@cdregistry.register_tag("alignof", CExp)
class CExpAlignOf(CExp):
    """ Alignof type expression

    - args[0]: index of type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def is_alignof(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "alignof", "type": self.typ.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_alignof(self)

    def __str__(self) -> str:
        return "alignof(" + str(self.typ) + ")"


@cdregistry.register_tag("alignofe", CExp)
class CExpAlignOfE(CExp):
    """ Align of expression expression

    - args[0]: index of expression in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def is_alignofe(self) -> bool:
        return True

    @property
    def exp(self) -> CExp:
        return self.cd.get_exp(self.args[0])

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.exp.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.exp.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "alignofe", "exp": self.exp.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_alignofe(self)

    def __str__(self) -> str:
        return "alignofe(" + str(self.exp) + ")"


@cdregistry.register_tag("unop", CExp)
class CExpUnOp(CExp):
    """ Unary expression

    - tags[1]: unary operator

    - args[0]: index of subexpression in cdictionary
    - args[1]: index of result type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def exp(self) -> CExp:
        return self.cd.get_exp(self.args[0])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[1])

    @property
    def op(self) -> str:
        return self.tags[1]

    @property
    def is_unop(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.exp.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.exp.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "unop", "op": self.op, "exp": self.exp.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_unop(self)

    def __str__(self) -> str:
        return "(" + unoperatorstrings[self.op] + " " + str(self.exp) + ")"


@cdregistry.register_tag("binop", CExp)
class CExpBinOp(CExp):
    """ Binary expression

    - tags[1]: binary operator
    - args[0]: index of exp1 in cdictionary
    - args[1]: index of exp2 in cdictionary
    - args[2]: index of typ in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def exp1(self) -> CExp:
        return self.cd.get_exp(self.args[0])

    @property
    def exp2(self) -> CExp:
        return self.cd.get_exp(self.args[1])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[2])

    @property
    def op(self) -> str:
        return self.tags[1]

    @property
    def is_binop(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp1.has_variable(vid) or self.exp2.has_variable(vid)

    def has_variable_op(self, vid: int, op: str) -> bool:
        return (
            self.exp1.has_variable(vid) or self.exp2.has_variable(vid)
        ) and (op == binoperatorstrings[self.op])

    def get_strings(self) -> List[str]:
        c1 = self.exp1.get_strings()
        c2 = self.exp2.get_strings()
        return c1 + c2

    def get_variable_uses(self, vid: int) -> int:
        c1 = self.exp1.get_variable_uses(vid)
        c2 = self.exp2.get_variable_uses(vid)
        return c1 + c2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": "binop",
            "op": self.op,
            "exp1": self.exp1.to_dict(),
            "exp2": self.exp2.to_dict(),
        }

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_binop(self)

    def __str__(self) -> str:
        return (
            "("
            + str(self.exp1)
            + " "
            + binoperatorstrings[self.op]
            + " "
            + str(self.exp2)
            + ")"
            + ":"
            + str(self.typ)
        )


@cdregistry.register_tag("question", CExp)
class CExpQuestion(CExp):
    """Question expression.

    - args[0]: index of conditional expression in cdictionary
    - args[1]: index of if-true expression in cdictionary
    - args[2]: index of if-false expression in cdictionary
    - args[3]: index of result type in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def is_question(self) -> bool:
        return True

    @property
    def condition(self) -> CExp:
        return self.cd.get_exp(self.args[0])

    @property
    def true_exp(self) -> CExp:
        return self.cd.get_exp(self.args[1])

    @property
    def false_exp(self) -> CExp:
        return self.cd.get_exp(self.args[2])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[3])

    def has_variable(self, vid: int) -> bool:
        return (
            self.condition.has_variable(vid)
            or self.true_exp.has_variable(vid)
            or self.false_exp.has_variable(vid)
        )

    def get_strings(self) -> List[str]:
        c = self.condition.get_strings()
        t = self.true_exp.get_strings()
        f = self.false_exp.get_strings()
        return c + t + f

    def get_variable_uses(self, vid: int) -> int:
        c = self.condition.get_variable_uses(vid)
        t = self.true_exp.get_variable_uses(vid)
        f = self.false_exp.get_variable_uses(vid)
        return c + t + f

    def to_dict(self) -> Dict[str, object]:
        return {
            "base": "question",
            "cond": self.condition.to_dict(),
            "true-exp": self.true_exp.to_dict(),
            "false-exp": self.false_exp.to_dict(),
            "type": self.typ.to_dict(),
        }

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_question(self)

    def __str__(self) -> str:
        return (
            "("
            + str(self.condition)
            + " ? "
            + str(self.true_exp)
            + " : "
            + str(self.false_exp)
            + ")"
        )


@cdregistry.register_tag("caste", CExp)
class CExpCastE(CExp):
    """Cast expression.

    - args[0]: index of target type in cdictionary
    - args[1]: index of expression to be cast in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def exp(self) -> CExp:
        return self.cd.get_exp(self.args[1])

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    @property
    def is_caste(self) -> bool:
        return True

    def get_strings(self) -> List[str]:
        return self.exp.get_strings()

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def get_variable_uses(self, vid: int) -> int:
        return self.exp.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, object]:
        return {
            "base": "caste",
            "exp": self.exp.to_dict(),
            "type": self.typ.to_dict(),
        }

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_cast(self)

    def __str__(self) -> str:
        return "caste(" + str(self.typ) + "," + str(self.exp) + ")"


@cdregistry.register_tag("addrof", CExp)
class CExpAddrOf(CExp):
    """Address-of expression

    - args[0]: index of lval in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(self.args[0])

    @property
    def is_addrof(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.lval.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.lval.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.lval.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, object]:
        return {"base": "addrof", "lval": self.lval.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_addrof(self)

    def __str__(self) -> str:
        return "&(" + str(self.lval) + ")"


@cdregistry.register_tag("addroflabel", CExp)
class CExpAddrOfLabel(CExp):
    """Address-of label expression

    - args[0]: statement sid
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def label_sid(self) -> int:
        return self.args[0]

    def to_dict(self) -> Dict[str, object]:
        return {"base": "addroflabel", "label": self.label_sid}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_addr_of_label(self)

    def __str__(self) -> str:
        return "addroflabel(" + str(self.label_sid) + ")"


@cdregistry.register_tag("startof", CExp)
class CExpStartOf(CExp):
    """Start-of expression

    - args[0]: index of lval in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def lval(self) -> "CLval":
        return self.cd.get_lval(self.args[0])

    @property
    def is_startof(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.lval.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.lval.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.lval.get_variable_uses(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "startof", "lval": self.lval.to_dict()}

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_startof(self)

    def __str__(self) -> str:
        return "&(" + str(self.lval) + ")"


@cdregistry.register_tag("fnapp", CExp)
class CExpFnApp(CExp):
    """Function application.

    - tags[1]: filename
    - args[0]: line number
    - args[1]: byte number
    - args[2]: index of target function expression in cdictionary
    - args[3..]: indices of arguments (optional) in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def is_fn_app(self) -> bool:
        return True

    @property
    def exp(self) -> CExp:
        return self.cd.get_exp(self.args[2])

    @property
    def arguments(self) -> List[Optional[CExp]]:
        return [self.cd.get_exp_opt(int(i)) for i in self.args[3:]]

    def has_variable(self, vid: int) -> bool:
        return any([a.has_variable(vid) for a in self.arguments if a])

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_fn_app(self)

    def __str__(self) -> str:
        return (
            "fnapp("
            + str(self.exp)
            + "("
            + ", ".join(str(a) for a in self.arguments)
            + "))")


@cdregistry.register_tag("cnapp", CExp)
class CExpCnApp(CExp):
    """Constant function application.

    - tags[0]: name
    - args[0]: index of result type in cdictionary
    - args[1..]: indices of arguments (optional) in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CExp.__init__(self, cd, ixval)

    @property
    def is_cn_app(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return self.tags[1]

    @property
    def typ(self) -> "CTyp":
        return self.cd.get_typ(int(self.args[0]))

    @property
    def arguments(self) -> List[Optional[CExp]]:
        return [self.cd.get_exp_opt(int(i)) for i in self.args[1:]]

    def has_variable(self, vid: int) -> bool:
        return any([a.has_variable(vid) for a in self.arguments if a])

    def accept(self, visitor: "CVisitor") -> None:
        visitor.visit_cn_app(self)

    def __str__(self) -> str:
        return (
            "cnapp("
            + self.name
            + "("
            + ",".join([str(a) for a in self.arguments])
            + ")")
