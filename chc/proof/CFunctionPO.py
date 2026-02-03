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
"""Super class of all (primary and supporting) proof obligations."""

import xml.etree.ElementTree as ET

from typing import cast, Dict, List, Optional, TYPE_CHECKING

from chc.proof.CFunPODictionaryRecord import CFunPOType
from chc.proof.PPOType import PPOType

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CLocation import CLocation
    from chc.app.CContext import (CfgContext, ProgramContext)
    from chc.proof.AssumptionType import AssumptionType
    from chc.proof.CFunctionProofs import CFunctionProofs
    from chc.proof.CFunPODictionary import CFunPODictionary
    from chc.proof.CPOPredicate import CPOPredicate
    from chc.proof.CProofDependencies import CProofDependencies
    from chc.proof.CProofDiagnostic import CProofDiagnostic, SituatedMsg
    from chc.proof.SPOType import SPOType


po_status = {
    "g": "safe",
    "o": "open",
    "r": "violation",
    "x": "dead-code",
    "p": "implementation-defined",
    "b": "value-wrap-around",
}

po_status_indicators = {v: k for (k, v) in po_status.items()}


class CFunctionPO:
    """Super class of primary and supporting proof obligations."""

    def __init__(
            self,
            cproofs: "CFunctionProofs",
            potype: CFunPOType,
            status: str = "open",
            deps: Optional["CProofDependencies"] = None,
            expl: Optional["SituatedMsg"] = None,
            diag: Optional["CProofDiagnostic"] = None) -> None:
        self._cproofs = cproofs
        self._potype = potype
        self._status = status
        self._dependencies = deps
        self._explanation = expl
        self._diagnostic = diag

    @property
    def predicate_name(self) -> str:
        return self.predicate.predicate_name

    @property
    def cproofs(self) -> "CFunctionProofs":
        return self._cproofs

    @property
    def cfun(self) -> "CFunction":
        return self.cproofs.cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def potype(self) -> CFunPOType:
        return self._potype

    @property
    def po_index(self) -> int:
        return self.potype.po_index

    @property
    def pod(self) -> "CFunPODictionary":
        return self.potype.pod

    @property
    def location(self) -> "CLocation":
        return self.potype.location

    @property
    def line(self) -> int:
        return self.location.line

    @property
    def context(self) -> "ProgramContext":
        return self.potype.context

    @property
    def context_strings(self) -> str:
        return str(self.context)

    @property
    def cfg_context(self) -> "CfgContext":
        return self.context.cfg_context

    @property
    def predicate(self) -> "CPOPredicate":
        return self.potype.predicate

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def is_closed(self) -> bool:
        return not self.is_open

    @property
    def is_violated(self) -> bool:
        return self.status == "violation"

    @property
    def is_safe(self) -> bool:
        return self.status == "safe"

    @property
    def is_implementation_defined(self) -> bool:
        return self.status == "implementation-defined"

    @property
    def is_value_wrap_around(self) -> bool:
        return self.status == "value-wrap-around"

    @property
    def is_deadcode(self) -> bool:
        return self.status == "deadcode"

    @property
    def is_delegated(self) -> bool:
        if self.is_safe and self.dependencies is not None:
            return self.dependencies.has_external_dependencies()
        return False

    @property
    def dependencies(self) -> "CProofDependencies":
        if self._dependencies is not None:
            return self._dependencies
        else:
            raise UF.CHCError("Proof obligation has no dependencies")

    def has_dependencies(self) -> bool:
        return self._dependencies is not None

    @property
    def explanation(self) -> Optional["SituatedMsg"]:
        return self._explanation

    def has_explanation(self) -> bool:
        return self._explanation is not None

    @property
    def diagnostic(self) -> "CProofDiagnostic":
        if self._diagnostic is not None:
            return self._diagnostic
        else:
            raise UF.CHCError("Proof obligation does not have diagnostic")

    def has_diagnostic(self) -> bool:
        return self._diagnostic is not None

    def has_referral_diagnostic(self) -> bool:
        if self.diagnostic is not None:
            for k in self.diagnostic.keyword_msgs:
                if k.startswith("DomainRef"):
                    return True
        return False

    def get_referral_diagnostics(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        if self.has_referral_diagnostic() and self.diagnostic is not None:
            for k in self.diagnostic.keyword_msgs:
                if k .startswith("DomainRef"):
                    key = k[10]
                    result.setdefault(key, [])
                    result[key].extend(self.diagnostic.keyword_msgs[k])
        return result

    @property
    def is_ppo(self) -> bool:
        return False

    @property
    def is_spo(self) -> bool:
        return False

    def has_argument_name(self, vname: str) -> bool:
        vid = self.cfun.get_variable_vid(vname)
        if vid is not None:
            return self.has_argument(vid)
        else:
            return False

    def has_variable_name(self, vname: str) -> bool:
        if self.cfun.has_variable_vid(vname):
            vid = self.cfun.get_variable_vid(vname)
            return self.has_variable(vid)
        else:
            return False

    def has_variable_name_op(self, vname: str, op: str) -> bool:
        if self.cfun.has_variable_vid(vname):
            vid = self.cfun.get_variable_vid(vname)
            return self.has_variable_op(vid, op)
        else:
            return False

    def has_variable_name_deref(self, vname: str) -> bool:
        vid = self.cfun.get_variable_vid(vname)
        if vid is not None:
            return self.has_variable_deref(vid)
        else:
            return False

    def get_assumptions(self) -> List["AssumptionType"]:
        if self.has_dependencies():
            depids = self.dependencies.ids
            return [self.pod.get_assumption_type(id) for id in depids]
        else:
            return []

    def has_api_dependencies(self) -> bool:
        if self.has_dependencies():
            atypes = self.get_assumptions()
            return any([t.is_api_assumption for t in atypes])
        return False

    def get_assumptions_type(self) -> str:
        atypes = self.get_assumptions()
        if len(atypes) == 1:
            t = atypes[0]
            if t.is_local_assumption:
                return "local"
            if t.is_api_assumption:
                return "api"
            if t.is_global_api_assumption:
                return "contract"
            if t.is_global_assumption:
                return "contract"
            if t.is_contract_assumption:
                return "contract"
            else:
                print("assumption not recognized: " + str(t))
                exit(1)
        elif len(atypes) == 0:
            return "local"
        else:
            if any(
                [
                    t.is_global_api_assumption or t.is_contract_assumption
                    for t in atypes
                ]
            ):
                return "contract"
            else:
                print("assumptions not recognized: ")
                for t in atypes:
                    print("  " + str(t))
                return "api"

    def get_global_assumptions(self) -> List["AssumptionType"]:
        return [t for t in self.get_assumptions() if t.is_global_assumption]

    def get_postcondition_assumptions(self) -> List["AssumptionType"]:
        return [t for t in self.get_assumptions() if t.is_contract_assumption]

    def has_argument(self, vid: int) -> bool:
        return self.predicate.has_argument(vid)

    def has_variable(self, vid: int) -> bool:
        return self.predicate.has_variable(vid)

    def has_variable_op(self, vid: int, op: str) -> bool:
        return self.predicate.has_variable_op(vid, op)

    def has_variable_deref(self, vid: int) -> bool:
        return self.predicate.has_variable_deref(vid)

    '''
    def has_target_type(self, targettype):
        return self.predicate.has_target_type()

    def has_referral_diagnostic(self):
        if self.has_diagnostic():
            for k in self.diagnostic.kmsgs:
                if k.startswith("DomainRef"):
                    return True
        return False

    def get_referral_diagnostics(self):
        result = {}
        if self.has_referral_diagnostic():
            for k in self.diagnostic.kmsgs:
                if k.startswith("DomainRef"):
                    key = k[10:]
                    if key not in result:
                        result[key] = []
                    result[key].extend(self.diagnostic.kmsgs[k])
        return result
    '''

    def get_display_prefix(self) -> str:
        if self.is_violated:
            return "<*>"
        if self.is_implementation_defined:
            return "<!>"
        if self.is_value_wrap_around:
            return "<o>"
        if self.is_open:
            return "<?>"
        if self.is_deadcode:
            return "<X>"
        if self.has_dependencies():
            if self.dependencies.is_stmt:
                return "<S>"
            if self.dependencies.is_local:
                return "<L>"
        return "<A>"

    def write_xml(self, cnode: ET.Element) -> None:
        self.pod.write_xml_spo_type(cnode, cast("SPOType", self.potype))
        cnode.set("s", po_status_indicators[self.status])
        cnode.set("id", str(self.po_index))
        if self.has_dependencies():
            self.dependencies.write_xml(cnode)
        if self.explanation is not None:
            enode = ET.Element("e")
            enode.set("txt", self.explanation.msg)
            cnode.append(enode)
        if self.has_diagnostic():
            dnode = ET.Element("d")
            self.diagnostic.write_xml(dnode)
            cnode.append(dnode)

    def __str__(self) -> str:
        return (
            str(self.po_index).rjust(4)
            + "  "
            + str(self.line).rjust(5)
            + "  "
            + str(self.predicate).ljust(20)
            + " ("
            + self.status
            + ")"
        )
