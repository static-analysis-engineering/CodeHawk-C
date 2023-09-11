# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2022 Henny Sipma
# Copyright (c) 2023      Aarno Labs LLC
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

from typing import cast, Any, List, Tuple, Optional, TYPE_CHECKING

from chc.app.CDictionaryRecord import CDictionaryRecord, cdregistry

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CDictionary import CDictionary
    from chc.app.CFile import CFile
    import chc.app.CFileDictionary
    from chc.app.CAttributes import CAttributes
    from chc.app.CTyp import CTyp


class CTypsig(CDictionaryRecord):

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)
        self._cd = cd
        self._cfile = self.cd.cfile

    @property
    def cd(self) -> "CDictionary":
        return self._cd

    @property
    def cfile(self) -> "CFile":
        return self._cfile


@cdregistry.register_tag("tsarray", CTypsig)
class CTypsigArray(CTypsig):
    """Array type signature.

    tags[1]: length of array (optional)
    args[0]: index of type signature of array base in cdictionary
    args[1]: index of attributes in cdictionary
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def opt_length(self) -> Optional[int]:
        return None if self.tags[1] == "" else int(self.tags[1])

    @property
    def typsig(self) -> CTypsig:
        return self.cd.get_typsig(self.args[0])

    @property
    def attributes(self) -> "CAttributes":
        return self.cd.get_attributes(self.args[1])

    def __str__(self) -> str:
        return "tsarray(" + str(self.typsig) + "," + str(self.opt_length)


@cdregistry.register_tag("tsptr", CTypsig)
class CTypsigPtr(CTypsig):
    """Pointer type signature.

    args[0]: index of target type signature in cdictionary
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def typsig(self) -> CTypsig:
        return self.cd.get_typsig(self.args[0])

    def __str__(self) -> str:
        return "tsptr(" + str(self.typsig) + ")"


@cdregistry.register_tag("tscomp", CTypsig)
class CTypsigComp(CTypsig):
    """Struct type signature.

    tags[1]: name of struct
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "tscomp(" + str(self.name) + ")"


@cdregistry.register_tag("tsfun", CTypsig)
class CTypsigFun(CTypsig):
    """Function type signature.

    args[0]: index of return value type signature in cdictionary
    args[1]: index of list of argument type signatures in cdictionary
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def returnval_typsig(self) -> CTypsig:
        return self.cd.get_typsig(self.args[0])

    def opt_arg_typsigs_list(self) -> Optional["CTypsigList"]:
        ix = self.args[1]
        return self.cd.get_typsig_list(ix) if ix >= 0 else None

    def __str__(self) -> str:
        return (
            "("
            + str(self.opt_arg_typsigs_list)
            + "):"
            + str(self.returnval_typsig)
            + ")")


@cdregistry.register_tag("tsenum", CTypsig)
class CTypsigEnum(CTypsig):
    """Enum type signature.

    tags[1]: enum name
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "tsenum(" + self.name + ")"


@cdregistry.register_tag("tsbase", CTypsig)
class CTypsigBase(CTypsig):
    """Base type signature.

    args[1]: index of type of base type signature in cdictionary.
    """
    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        CTypsig.__init__(self, cd, ixval)

    @property
    def base_type(self) -> "CTyp":
        return self.cd.get_typ(self.args[0])

    def __str__(self) -> str:
        return "tsbase(" + str(self.base_type) + ")"


class CTypsigList(IT.IndexedTableValue):

    def __init__(self, cd: "CDictionary", ixval: IT.IndexedTableValue) -> None:
        self.cd = cd
        self.cfile = self.cd.cfile

    @property
    def typsig_list(self) -> List[CTypsig]:
        return [self.cd.get_typsig(ix) for ix in self.args]

    def __str__(self) -> str:
        return ",".join([str(x) for x in self.typsig_list])
