# ------------------------------------------------------------------------------
# CodeHaw C Analyzer
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
"""Left-hand side base (storage location for variable)."""

from typing import Dict, List, Tuple, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CExp import CExp


class CLHost(CDictionaryRecord):
    """Base class for variable and dereference."""

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)

    @property
    def is_var(self) -> bool:
        return False

    @property
    def is_mem(self) -> bool:
        return False

    @property
    def is_tmpvar(self) -> bool:
        return False

    def get_strings(self) -> List[str]:
        return []

    def has_variable(self, vid: int) -> bool:
        return False

    def has_variable_deref(self, vid: int) -> bool:
        return False

    def has_ref_type(self) -> bool:
        return self.is_mem

    def get_variable_uses(self, vid: int) -> int:
        raise NotImplementedError("Subclass needs to override get_variable_uses")

    def to_dict(self) -> Dict[str, object]:
        return {"base": "lhost"}

    def __str__(self) -> str:
        return "lhostbase:" + self.tags[0]


@cdregistry.register_tag("var", CLHost)
class CLHostVar(CLHost):
    """ Variable.

    - tags[1]: vname (name of variable)
    - args[0]: vid (variable id)
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CLHost.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    @property
    def vid(self) -> int:
        return self.args[0]

    @property
    def is_var(self) -> bool:
        return True

    @property
    def is_tmpvar(self) -> bool:
        return self.name.startswith("tmp___")

    def has_variable(self, vid: int) -> bool:
        return self.vid == vid

    def get_variable_uses(self, vid: int) -> int:
        return 1 if self.has_variable(vid) else 0

    def to_dict(self) -> Dict[str, object]:
        return {"base": "var", "var": self.name}

    def __str__(self) -> str:
        return self.name


@cdregistry.register_tag("mem", CLHost)
class CLHostMem(CLHost):
    """ Memory reference.

    - args[0]: index of address expression in cdictionary
    """

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CLHost.__init__(self, cd, ixval)

    @property
    def exp(self) -> "CExp":
        return self.cd.get_exp(self.args[0])

    @property
    def is_mem(self) -> bool:
        return True

    def has_variable(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def get_strings(self) -> List[str]:
        return self.exp.get_strings()

    def get_variable_uses(self, vid: int) -> int:
        return self.exp.get_variable_uses(vid)

    def has_variable_deref(self, vid: int) -> bool:
        return self.exp.has_variable(vid)

    def to_dict(self) -> Dict[str, object]:
        return {"base": "mem", "exp": self.exp.to_dict()}

    def __str__(self) -> str:
        return "(*" + str(self.exp) + ")"
