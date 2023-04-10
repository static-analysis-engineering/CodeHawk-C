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
    import chc.app.CAttributes as CA
    import chc.app.CTyp as CT


class CTypsigTSBase(CDictionaryRecord):

    def __init__(
        self,
        cd: "CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CDictionaryRecord.__init__(self, cd, ixval)
        self._cd = cd
        self._cfile = self.cd.cfile

    @property
    def cd(self) -> "CDictionary":
        return self._cd

    @property
    def cfile(self) -> "CFile":
        return self._cfile


@cdregistry.register_tag("tsarray", CTypsigTSBase)
class CTypsigArray(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_len_opt(self) -> Optional[int]:
        return None if self.tags[1] == "" else int(self.tags[1])

    def get_typsig(self) -> CTypsigTSBase:
        return self.cd.get_typsig(self.args[0])

    def get_attributes(self) -> "CA.CAttributes":
        return self.cd.get_attributes(self.args[1])

    def __str__(self) -> str:
        return "tsarray(" + str(self.get_typsig()) + "," + str(self.get_len_opt)


@cdregistry.register_tag("tsptr", CTypsigTSBase)
class CTypsigPtr(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_typsig(self) -> CTypsigTSBase:
        return self.cd.get_typsig(self.args[0])

    def __str__(self) -> str:
        return "tsptr(" + str(self.get_typsig()) + ")"


@cdregistry.register_tag("tscomp", CTypsigTSBase)
class CTypsigComp(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_name(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "tscomp(" + str(self.get_name()) + ")"


@cdregistry.register_tag("tsfun", CTypsigTSBase)
class CTypsigFun(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_typsig(self) -> CTypsigTSBase:
        return self.cd.get_typsig(self.args[0])

    def get_typsig_list_opt(self) -> Optional["CTypsigList"]:
        ix = self.args[1]
        return self.cd.get_typesig_list(ix) if ix >= 0 else None

    def __str__(self) -> str:
        return "(" + str(self.get_typsig_list_opt) + "):" + str(self.get_typsig()) + ")"


@cdregistry.register_tag("tsenum", CTypsigTSBase)
class CTypsigEnum(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_name(self) -> str:
        return self.tags[1]

    def __str__(self) -> str:
        return "tsenum(" + self.get_name() + ")"


@cdregistry.register_tag("tsbase", CTypsigTSBase)
class CTypsigBase(CTypsigTSBase):
    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        CTypsigTSBase.__init__(self, cd, ixval)

    def get_type(self) -> "CT.CTypBase":
        return self.cd.get_typ(self.args[0])

    def __str__(self) -> str:
        return "tsbase(" + str(self.get_type()) + ")"


class CTypsigList(IT.IndexedTableValue):
    def __init__(
        self,
        cd: "CDictionary",
        ixval: IT.IndexedTableValue,
    ) -> None:
        self.cd = cd
        self.cfile = self.cd.cfile

    def get_typsig_list(self) -> List[CTypsigTSBase]:
        return [self.cd.get_typsig(ix) for ix in self.args]

    def __str__(self) -> str:
        return ",".join([str(x) for x in self.get_typsig_list()])
