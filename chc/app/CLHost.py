# ------------------------------------------------------------------------------
# CodeHaw C Analyzer
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
    import chc.app.CExp as CE


class CLHostBase(CD.CDictionaryRecord):
    """Base class for variable and dereference."""

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def is_var(self) -> bool:
        return False

    def is_mem(self) -> bool:
        return False

    def is_tmpvar(self) -> bool:
        return False

    def get_strings(self) -> List[str]:
        return []

    def has_variable(self, vid: int) -> bool:
        return False

    def has_variable_deref(self, vid: int) -> bool:
        return False

    def has_ref_type(self) -> bool:
        return self.is_mem()

    def get_variable_uses(self, vid: int) -> int:
        raise NotImplementedError("Subclass needs to override get_variable_uses")

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "lhost"}

    def __str__(self) -> str:
        return "lhostbase:" + self.tags[0]


class CLHostVar(CLHostBase):
    """
    tags:
        0: 'var'
        1: vname

    args:
        0: vid
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CLHostBase.__init__(self, cd, index, tags, args)

    def get_name(self) -> str:
        return self.tags[1]

    def get_vid(self) -> int:
        return self.args[0]

    def is_var(self) -> bool:
        return True

    def is_tmpvar(self) -> bool:
        return self.get_name().startswith("tmp___")

    def has_variable(self, vid: int) -> bool:
        return self.get_vid() == vid

    def get_variable_uses(self, vid: int) -> int:
        return 1 if self.has_variable(vid) else 0

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "var", "var": self.get_name()}

    def __str__(self) -> str:
        # return self.get_name() +  ' (vid:' + str(self.get_vid()) + ')'
        return self.get_name()


class CLHostMem(CLHostBase):
    """
    tags:
        0: 'mem'

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
        CLHostBase.__init__(self, cd, index, tags, args)

    def get_exp(self) -> "CE.CExpBase":
        return self.cd.get_exp(self.args[0])

    def is_mem(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.get_exp().has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.get_exp().get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.get_exp().get_variable_uses(vid)

    def has_variable_deref(self, vid: int) -> bool:
        return self.get_exp().has_variable(vid)

    def to_dict(self) -> Dict[str, Any]:
        return {"base": "mem", "exp": self.get_exp().to_dict()}

    def __str__(self) -> str:
        return "(*" + str(self.get_exp()) + ")"
