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
    import chc.app.CLHost as CH
    import chc.app.COffsetExp as CO


class CLval(CD.CDictionaryRecord):
    """
    tags: -

    args:
        0: lhost
        1: offset
    """

    def __init__(
        self,
        cd: "chc.app.CDictionary.CDictionary",
        index: int,
        tags: List[str],
        args: List[int],
    ) -> None:
        CD.CDictionaryRecord.__init__(self, cd, index, tags, args)

    def get_lhost(self) -> "CH.CLHostBase":
        return self.cd.get_lhost(self.args[0])

    def get_offset(self) -> "CO.COffsetBase":
        return self.cd.get_offset(self.args[1])

    def has_variable(self, vid: int) -> bool:
        return self.get_lhost().has_variable(vid)

    def get_strings(self) -> List[str]:
        hostresult = self.get_lhost().get_strings()
        offsetresult = self.get_offset().get_strings()
        return hostresult + offsetresult

    def get_variable_uses(self, vid: int) -> int:
        hostresult = self.get_lhost().get_variable_uses(vid)
        offsetresult = self.get_offset().get_variable_uses(vid)
        return hostresult + offsetresult

    def has_variable_deref(self, vid: int) -> bool:
        return self.get_lhost().has_variable_deref(vid)

    def has_ref_type(self) -> bool:
        return self.get_lhost().has_ref_type()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lhost": self.get_lhost().to_dict(),
            "offset": self.get_offset().to_dict(),
        }

    def to_idict(self) -> Dict[str, Any]:
        return {"t": self.tags, "a": self.args}

    def __str__(self) -> str:
        return str(self.get_lhost()) + str(self.get_offset())
