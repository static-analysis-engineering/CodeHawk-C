# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2026 Aarno Labs LLC
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
"""Contracts of external functions as used by the analysis.

The analyzer writes, per c file, the contract of every external function
(declared, not defined in the file) that has one, with its origin: the
attributes on the declaration (from the source headers and the companions;
CIL merges them, so the two cannot be told apart), each with the conditions it
generates, and/or the contract file (<file>_xc.xml).

A specification is judged on two axes:

- effects (frame): missing means havoc (sound, imprecise). Declared by a side
  effect (e.g., GCC pure/const, chkc_preserves_all_memory, a contract file) or
  explicitly left unknown by chkc_effects_unknown.
- preconditions: missing means the callers' obligations are implicitly true,
  which is unsound. Declared by a CodeHawk specification only: a precondition
  from a chkc_ attribute (chkc_nonnull, chkc_format, chkc_access, ...) or from
  a contract file, or explicitly absent by chkc_requires_none. Preconditions
  from gcc attributes in source headers (nonnull, format, access) are used by
  the analysis, but do not declare the axis: they are written for the
  compiler and do not claim to be all the preconditions.

Postconditions are optional: missing ones lose precision only.

A specification is complete if both axes are declared, partial otherwise. A
library summary of the analyzer takes precedence over the contract at call
sites and is complete by construction (it is part of the model).
"""

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, TYPE_CHECKING

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CFile import CFile


# CIL renames the GCC function attribute const to aconst, to distinguish it
# from the type qualifier
DISPLAY_NAMES = {"aconst": "const"}

EFFECTS_UNKNOWN = "chkc_effects_unknown"
REQUIRES_NONE = "chkc_requires_none"


class CExternalAttribute:
    """An attribute on the declaration of an external function, with the
    conditions it generates."""

    def __init__(self, xnode: ET.Element) -> None:
        self.xnode = xnode

    @property
    def name(self) -> str:
        name = self.xnode.get("name", "")
        return DISPLAY_NAMES.get(name, name)

    @property
    def text(self) -> str:
        return self.xnode.get("a", self.name)

    @property
    def is_recognized(self) -> bool:
        return self.xnode.get("recognized", "yes") == "yes"

    @property
    def is_marker(self) -> bool:
        return self.xnode.get("marker", "no") == "yes"

    def _conditions(self, tag: str) -> List[str]:
        return [x.get("p", "") for x in self.xnode.findall(tag)]

    @property
    def preconditions(self) -> List[str]:
        return self._conditions("pre")

    @property
    def postconditions(self) -> List[str]:
        return self._conditions("post")

    @property
    def sideeffects(self) -> List[str]:
        return self._conditions("side")


class CExternalContract:
    """Contract of one external function as used by the analysis of a file."""

    def __init__(self, xnode: ET.Element) -> None:
        self.xnode = xnode

    @property
    def name(self) -> str:
        return self.xnode.get("name", "")

    @property
    def has_library_summary(self) -> bool:
        return self.xnode.get("summary", "no") == "yes"

    @property
    def from_contract_file(self) -> bool:
        return self.xnode.get("contract-file", "no") == "yes"

    @property
    def attributes(self) -> List[CExternalAttribute]:
        return [CExternalAttribute(x) for x in self.xnode.findall("attribute")]

    def _contract_conditions(self, tag: str) -> List[str]:
        c = self.xnode.find("contract")
        if c is None:
            return []
        return [x.get("p", "") for x in c.findall(tag)]

    @property
    def preconditions(self) -> List[str]:
        return self._contract_conditions("pre")

    @property
    def postconditions(self) -> List[str]:
        return self._contract_conditions("post")

    @property
    def sideeffects(self) -> List[str]:
        return self._contract_conditions("side")

    def _has_marker(self, name: str) -> bool:
        return any(a.is_marker and a.name == name for a in self.attributes)

    def _basis(self, conditions: List[str], kind: str) -> Optional[str]:
        """Names of the sources of the conditions of a kind (pre, side)."""
        if len(conditions) == 0:
            return None
        names: List[str] = []
        for a in self.attributes:
            conds = a.preconditions if kind == "pre" else a.sideeffects
            if len(conds) > 0 and a.name not in names:
                names.append(a.name)
        if self.from_contract_file:
            names.append("contract file")
        return ", ".join(names) if names else "contract"

    @property
    def effects_basis(self) -> Optional[str]:
        """How the effects are declared; None if they are not."""
        if self._has_marker(EFFECTS_UNKNOWN):
            return "declared unknown (" + EFFECTS_UNKNOWN + ")"
        return self._basis(self.sideeffects, "side")

    @property
    def preconditions_basis(self) -> Optional[str]:
        """How the preconditions are declared; None if they are not (only
        CodeHawk specifications declare them, see above)."""
        if self._has_marker(REQUIRES_NONE):
            return "declared none (" + REQUIRES_NONE + ")"
        names: List[str] = []
        for a in self.attributes:
            if (
                    a.name.startswith("chkc_")
                    and len(a.preconditions) > 0
                    and a.name not in names):
                names.append(a.name)
        if self.from_contract_file and len(self.preconditions) > 0:
            names.append("contract file")
        return ", ".join(names) if names else None

    @property
    def compiler_preconditions(self) -> List[str]:
        """Names of the gcc attributes that generate preconditions (used by
        the analysis, but not declaring the axis)."""
        names: List[str] = []
        for a in self.attributes:
            if (
                    not a.name.startswith("chkc_")
                    and len(a.preconditions) > 0
                    and a.name not in names):
                names.append(a.name)
        return names

    @property
    def status(self) -> str:
        if self.has_library_summary:
            return "summary"
        if (
                self.effects_basis is not None
                and self.preconditions_basis is not None):
            return "complete"
        return "partial"

    def to_dict(self) -> Dict[str, Optional[str]]:
        compiler = self.compiler_preconditions
        return {
            "status": self.status,
            "effects": self.effects_basis,
            "preconditions": self.preconditions_basis,
            "compiler-preconditions": (
                ", ".join(compiler) if compiler else None)}


# order of completeness, least complete first (used to combine the
# specifications of a function seen by different files)
STATUS_ORDER = ["not-recorded", "partial", "complete", "summary"]


class CExternalContracts:
    """External function contracts of a c file."""

    def __init__(self, cfile: "CFile") -> None:
        self.cfile = cfile
        self._contracts: Optional[Dict[str, CExternalContract]] = None
        self._exported: Optional[Dict[str, Dict[str, List[str]]]] = None
        self._recorded = False

    def _initialize(self) -> None:
        if self._contracts is not None:
            return
        self._contracts = {}
        xnode = UF.get_cfile_external_contracts_xnode(
            self.cfile.targetpath,
            self.cfile.projectname,
            self.cfile.cfilepath,
            self.cfile.cfilename)
        if xnode is None:
            return
        self._recorded = True
        for x in xnode.findall("function"):
            c = CExternalContract(x)
            self._contracts[c.name] = c

    @property
    def is_recorded(self) -> bool:
        """False for the results of an analyzer that does not write the
        external contracts."""
        self._initialize()
        return self._recorded

    @property
    def exported_functions(self) -> Dict[str, Dict[str, List[str]]]:
        """Functions defined in this file and declared chkc_exported, with
        their declared preconditions (assumed here, checked at the callers
        in other modules), postconditions (guarantees, checked by primary
        proof obligations at the return sites) and side effects (declared,
        not checked)."""
        if self._exported is not None:
            return self._exported
        xnode = UF.get_cfile_external_contracts_xnode(
            self.cfile.targetpath,
            self.cfile.projectname,
            self.cfile.cfilepath,
            self.cfile.cfilename,
            rootnode="exported-functions")
        result: Dict[str, Dict[str, List[str]]] = {}
        if xnode is not None:
            for x in xnode.findall("function"):
                result[x.get("name", "")] = {
                    tag: [p.get("p", "") for p in x.findall(tag)]
                    for tag in ["pre", "post", "side"]}
        self._exported = result
        return result

    @property
    def contracts(self) -> Dict[str, CExternalContract]:
        self._initialize()
        if self._contracts is None:
            return {}
        return self._contracts

    def specification(self, name: str) -> Dict[str, Optional[str]]:
        """Classification of the specification of an external function that
        is called in this file and is not reported missing by the analyzer
        (it has a library summary or a contract)."""
        if not self.is_recorded:
            return {
                "status": "not-recorded",
                "effects": None,
                "preconditions": None,
                "compiler-preconditions": None}
        if name in self.contracts:
            return self.contracts[name].to_dict()
        # no contract recorded: the analyzer used a library summary
        return {
            "status": "summary",
            "effects": "library summary",
            "preconditions": "library summary",
            "compiler-preconditions": None}
