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
"""Object representation of api_parameter_t"""

from typing import List, TYPE_CHECKING

from chc.api.InterfaceDictionaryRecord import (
    InterfaceDictionaryRecord, ifdregistry)

import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.api.InterfaceDictionary import InterfaceDictionary


class ApiParameter(InterfaceDictionaryRecord):
    """Base class of formal parameter of a function.

    Args:
        cd (InterfaceDictionary): The parent dictionary to resolve
            subexpressions
        ixval (IndexedTableValue): The backing record of the value
    """

    def __init__(
        self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        InterfaceDictionaryRecord.__init__(self, cd, ixval)

    @property
    def is_formal(self) -> bool:
        return False

    @property
    def is_global(self) -> bool:
        return False

    def __str__(self) -> str:
        return "api-parameter " + self.tags[0]


@ifdregistry.register_tag("pf", ApiParameter)
class APFormal(ApiParameter):
    """Formal parameter of a function.

    * args[0]: parameter index (starting at 1)
    """

    def __init__(
        self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        ApiParameter.__init__(self, cd, ixval)

    @property
    def index(self) -> int:
        return int(self.args[0])

    @property
    def is_formal(self) -> bool:
        return True

    def __str__(self) -> str:
        return "par-" + str(self.index)


@ifdregistry.register_tag("pg", ApiParameter)
class APGlobal(ApiParameter):
    """Global variable used in a function; treated as a formal parameter."""

    def __init__(
        self, cd: "InterfaceDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        ApiParameter.__init__(self, cd, ixval)

    @property
    def name(self) -> str:
        return self.tags[1]

    @property
    def is_global(self) -> bool:
        return True

    def __str__(self) -> str:
        return "par-" + self.name
