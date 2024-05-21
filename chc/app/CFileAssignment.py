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
"""Object representation of sum type assignment_t."""

import xml.etree.ElementTree as ET

from typing import cast, List, Optional, TYPE_CHECKING

from chc.app.AssignDictionaryRecord import AssignDictionaryRecord, adregistry
import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

if TYPE_CHECKING:
    from chc.app.CExp import CExp
    from chc.app.CFileAssignmentDictionary import CFileAssignmentDictionary
    from chc.app.CInitInfo import CInitInfo
    from chc.app.CLval import CLval
    from chc.app.CVarInfo import CVarInfo


class CFileAssignment(AssignDictionaryRecord):
    """Base class for all assignment objects."""

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        AssignDictionaryRecord.__init__(self, ad, ixval)

    @property
    def is_init_assignment(self) -> bool:
        return False

    @property
    def is_global_assignment(self) -> bool:
        return False

    @property
    def is_global_index_assignment(self) -> bool:
        return False

    @property
    def is_static_assignment(self) -> bool:
        return False

    @property
    def is_static_index_assignment(self) -> bool:
        return False

    @property
    def is_field_assignment(self) -> bool:
        return False

    @property
    def is_unknown_assignment(self) -> bool:
        return False


class GlobalAssignmentFunctionName(AssignDictionaryRecord):

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        AssignDictionaryRecord.__init__(self, ad, ixval)

    @property
    def name(self) -> str:
        return self.tags[0]

    def __str__(self) -> str:
        return self.name


@adregistry.register_tag("init", CFileAssignment)
class InitAssignment(CFileAssignment):
    """Static initializer assignment.

    - tags[1]: vname
    - args[0]: vid of lhs
    - args[1]: index of init_info in cdeclarations dictionary
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_init_assignment(self) -> bool:
        return True

    @property
    def vname(self) -> str:
        """Name of lhs variable."""

        return self.tags[1]

    @property
    def vid(self) -> int:
        """Variable id of lhs variable."""

        return self.args[0]

    def lhs(self) -> "CVarInfo":
        return self.cfile.get_global_varinfo(self.vid)

    def rhs(self) -> "CInitInfo":
        return self.cdecls.get_initinfo(self.args[1])

    def __str__(self) -> str:
        return "I:" + str(self.lhs) + " := " + str(self.rhs)


@adregistry.register_tag("g", CFileAssignment)
class GlobalAssignment(CFileAssignment):
    """Global assignment within a function.

    - tags[1]: variable name
    - args[0]: vid of lhs
    - args[1]: index of enclosing function name in function-name table
    - args[2]: index of rhs expression in cdictionary
    - args[3]: index of location in cdecls dictionary
    - args[4]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_global_assignment(self) -> bool:
        return True

    @property
    def vname(self) -> str:
        return self.tags[1]

    @property
    def vid(self) -> int:
        return self.args[0]

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[1])

    @property
    def lhs(self) -> "CVarInfo":
        return self.cfile.get_global_varinfo(self.args[0])

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    def __str__(self) -> str:
        return "G:" + str(self.lhs) + " := " + str(self.rhs)


@adregistry.register_tag("gi", CFileAssignment)
class GlobalIndexAssignment(CFileAssignment):
    """Assignment to an array element of a global array.

    - tags[1]: vname (variable name)
    - args[0]: vid (variable id)
    - args[1]: index of function name in assign dictionary
    - args[2]: array index value
    - args[3]: index of rhs expression in cdictionary
    - args[4]: index of location in cdecls dictionary
    - args[5]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_global_index_assignment(self) -> bool:
        return True

    @property
    def vname(self) -> str:
        return self.tags[1]

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[1])

    @property
    def lhs(self) -> "CVarInfo":
        return self.cfile.get_global_varinfo(self.args[0])

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[3])

    @property
    def index(self) -> int:
        return self.args[2]

    def __str__(self) -> str:
        return (
            "G:"
            + str(self.lhs)
            + "["
            + str(self.index)
            + "] "
            + " := "
            + str(self.rhs)
        )


@adregistry.register_tag("s", CFileAssignment)
class StaticAssignment(CFileAssignment):
    """Assignment to a static variable.

    - tags[1]: vname
    - args[0]: vid
    - args[1]: index of function name in function-name table
    - args[2]: index of lhs in cdeclarations dictionary
    - args[3]: index of rhs in cdictionary
    - args[4]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def vname(self) -> str:
        return self.tags[1]

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[1])

    @property
    def vid(self) -> int:
        return self.args[0]

    @property
    def is_static_assignment(self) -> bool:
        return True

    @property
    def lhs(self) -> "CVarInfo":
        return self.cfile.get_global_varinfo(self.args[0])

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    def __str__(self) -> str:
        return "S:" + str(self.lhs) + " := " + str(self.rhs)


@adregistry.register_tag("si", CFileAssignment)
class StaticIndexAssignment(CFileAssignment):
    """Assignment to an element of a static array.

    - tags[1]: vname
    - args[0]: vid
    - args[1]: index of function name in function-name table
    - args[2]: index
    - args[3]: index of rhs in cdictionary
    - args[4]: index of location in cdeclarations
    - args[5]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_static_index_assignment(self) -> bool:
        return True

    @property
    def vname(self) -> str:
        return self.tags[1]

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[1])

    @property
    def vid(self) -> int:
        return self.args[0]

    @property
    def lhs(self) -> "CVarInfo":
        return self.cfile.get_global_varinfo(self.args[0])

    @property
    def index(self) -> int:
        return self.args[2]

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[3])

    def __str__(self) -> str:
        return (
            "S:"
            + str(self.lhs)
            + "["
            + str(self.index)
            + "] "
            + " := "
            + str(self.rhs)
        )


@adregistry.register_tag("f", CFileAssignment)
class FieldAssignment(CFileAssignment):
    """Assignment to a global struct field.

    - tags[1]: fieldname
    - args[0]: ckey (key that identifies the struct)
    - args[1]: index of function name in function name table
    - args[2]: index of lval in cdictionary
    - args[3]: index of rhs expression in cdictionary
    - args[4]: index of location in location table
    - args[5]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_field_assignment(self) -> bool:
        return True

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[1])

    @property
    def field(self) -> str:
        return self.tags[1]

    @property
    def lhs(self) -> "CLval":
        return self.cd.get_lval(self.args[2])

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[3])

    def __str__(self) -> str:
        return "F:" + str(self.field) + " := " + str(self.rhs)


@adregistry.register_tag("u", CFileAssignment)
class UnknownAssignment(CFileAssignment):
    """Assignment to unknown lval

    - args[0]: index of function name in function name table
    - args[1]: index of lval in cdictionary
    - args[2]: index of rhs in cdictionary
    - args[3]: index of location in cdeclarations dictionary
    - args[4]: index of context in context table
    """

    def __init__(
            self, ad: "CFileAssignmentDictionary", ixval: IT.IndexedTableValue
    ) -> None:
        CFileAssignment.__init__(self, ad, ixval)

    @property
    def is_unknown_assignment(self) -> bool:
        return True

    @property
    def fname(self) -> str:
        return self.ad.get_function_name(self.args[0])

    @property
    def lhs(self) -> "CLval":
        return self.cd.get_lval(self.args[1])

    @property
    def rhs(self) -> "CExp":
        return self.cd.get_exp(self.args[2])

    def __str__(self) -> str:
        return "U:" + str(self.lhs) + " := " + str(self.rhs)
