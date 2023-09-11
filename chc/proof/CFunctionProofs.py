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

import xml.etree.ElementTree as ET

from typing import List, Optional, TYPE_CHECKING

from chc.proof.CFunctionPO import CFunctionPO
from chc.proof.CFunctionPPO import CFunctionPPO
from chc.proof.CFunctionPPOs import CFunctionPPOs
from chc.proof.CFunctionSPOs import CFunctionSPOs

import chc.util.fileutil as UF

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction


class CFunctionProofs:
    """

    CFunctionProofs is the root of a data structure that provides access to
    all proof obligations and associated evidence. Relationships between
    proof obligation and evidence are established through the CFunctionProofs
    object.

    - CFunctionProofs
      - ppos: CFunctionPPOs
      - id -> CFunctionPPO

      - spos: CFunctionSPOs
      - callsitespos: context -> CFunctionCallsiteSPOs
      - id -> CFunctionCallsiteSPO
      - returnsitespos: context -> CFunctionReturnsiteSPOs
      - id -> CFunctionReturnsiteSPO
"""

    def __init__(
            self,
            cfun: "CFunction",
            xpponode: ET.Element,
            xsponode: ET.Element) -> None:
        self._cfun = cfun
        self.xpponode = xpponode
        self.xsponode = xsponode
        # self.cfile.predicatedictionary.initialize()
        self._ppos: Optional[CFunctionPPOs] = None
        self._spos: Optional[CFunctionSPOs] = None

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def cfile(self) -> "CFile":
        return self.cfun.cfile

    @property
    def capp(self) -> "CApplication":
        return self.cfile.capp

    @property
    def ppos(self) -> CFunctionPPOs:
        if self._ppos is None:
            self._ppos = CFunctionPPOs(self, self.xpponode)
        return self._ppos

    @property
    def ppolist(self) -> List[CFunctionPPO]:
        return list(self.ppos.ppos.values())

    @property
    def open_ppos(self) -> List[CFunctionPPO]:
        return [ppo for ppo in self.ppolist if not ppo.is_closed]

    @property
    def ppo_violations(self) -> List[CFunctionPPO]:
        return [ppo for ppo in self.ppolist if ppo.is_violated]

    @property
    def delegated_ppos(self) -> List[CFunctionPPO]:
        return [ppo for ppo in self.ppolist if ppo.is_delegated]

    @property
    def spos(self) -> CFunctionSPOs:
        if self._spos is None:
            self._spos = CFunctionSPOs(self, self.xsponode)
        return self._spos

    @property
    def spolist(self) -> List[CFunctionPO]:
        return self.spos.spos

    @property
    def open_spos(self) -> List[CFunctionPO]:
        return [spo for spo in self.spolist if not spo.is_closed]

    @property
    def spo_violations(self) -> List[CFunctionPPO]:
        return [spo for spo in self.spolist if spo.is_violated]

    def add_returnsite_postcondition(self, postcondition):
        # self._get_spos()
        self.spos.add_returnsite_postcondition(postcondition)

    def update_spos(self) -> None:
        # self._get_spos()
        self.spos.update()

    def distribute_post_guarantees(self) -> None:
        # self._get_spos()
        self.spos.distribute_post_guarantees()

    def collect_post_assumes(self) -> None:
        """For all call sites collect postconditions from callee's contracts and add as assume."""
        '''
        # self._get_spos()
        if self.spos is None:
            raise UF.CHCError(
                "No supporting proof obligations found for "
                + str(self.cfun.name)
                + " in file "
                + str(self.cfile.name)
            )
        '''
        self.spos.collect_post_assumes()

    def reset_ppos(self) -> None:
        self._ppos = None

    def reset_spos(self) -> None:
        self._spos = None

    def save_spos(self) -> None:
        cnode = ET.Element("function")
        cnode.set("name", self.cfun.name)
        self.spos.write_xml(cnode)
        self._save_spos(cnode)

    def get_ppo(self, id: int) -> CFunctionPPO:
        # self._get_ppos()
        return self.ppos.get_ppo(id)

    def get_spo(self, id: int) -> CFunctionPO:
        # self._get_spos()
        return self.spos.get_spo(id)

    '''
    def iter_ppos(self, f):
        # self._get_ppos()
        self.ppos.iter(f)

    def iter_spos(self, f):
        # self._get_spos()
        self.spos.iter(f)

    def iter_callsites(self, f):
        # self._get_spos()
        self.spos.iter_callsites(f)
    '''

    def reload_ppos(self) -> None:
        self.reset_ppos()
        # self._get_ppos(force=True)

    def reload_spos(self) -> None:
        self.reset_spos()
        # self._get_spos(force=True)

    '''
    def get_ppos(self) -> List[CFunctionPPO]:
        result: List[CFunctionPPO] = []

        def f(ppo):
            result.append(ppo)

        self.iter_ppos(f)
        return result

    def get_spos(self):
        # self._get_spos()
        result = []

        def f(spo):
            result.append(spo)

        self.iter_spos(f)
        return result

    def get_open_ppos(self):
        result = []

        def f(ppo):
            if not ppo.is_closed():
                result.append(ppo)

        self.iter_ppos(f)
        return result

    def get_open_spos(self):
        result = []

        def f(spo):
            if not spo.is_closed():
                result.append(spo)

        self.iter_spos(f)
        return result

    def get_violations(self):
        result = []

        def f(ppo):
            if ppo.is_violated():
                result.append(ppo)

        self.iter_ppos(f)
        return result

    def get_spo_violations(self):
        result = []

        def f(spo):
            if spo.is_violated():
                result.append(spo)

        self.iter_spos(f)
        return result

    def get_delegated(self):
        result = []

        def f(ppo):
            if ppo.is_delegated():
                result.append(ppo)

        self.iter_ppos(f)
        return result

    def _get_ppos(self, force=False):
        if self.ppos is None or force:
            xnode = UF.get_ppo_xnode(self.capp.path, self.cfile.name, self.cfun.name)
            if xnode is not None:
                self.ppos = CFunctionPPOs(self, xnode)
            else:
                print(
                    "Unable to load ppos for "
                    + self.cfun.name
                    + " in file "
                    + self.cfile.name
                )

    def _get_spos(self, force=False):
        if self.spos is None or force:
            xnode = UF.get_spo_xnode(self.capp.path, self.cfile.name, self.cfun.name)
            if xnode is not None:
                self.spos = CFunctionSPOs(self, xnode)
            else:
                raise UF.CHCError(
                    "Unable to load spos for "
                    + self.cfun.name
                    + " in file "
                    + self.cfile.name
                )
    '''

    def _save_spos(self, cnode: ET.Element) -> None:
        UF.save_spo_file(self.capp.path, self.cfile.name, self.cfun.name, cnode)
