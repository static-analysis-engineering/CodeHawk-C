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

import logging

import xml.etree.ElementTree as ET

import chc.util.fileutil as UF

class CGlobalContract(object):
    """Holds assumptions that transcend the file level.

    The global contract is held by two files at the top directory of
    the contractpath:
    - globaldefs.json: 
      - directions to the linker about hidden data structures and hidden fields

    - globaldefs.xml:
      - assumptions relevant to the CodeHawk analyzer
      - library function summaries that override the standard library function 
        summaries

    Examples: 
      - abstraction of interfile data structures by hiding fields
      - abstraction of interfile data structures by complete hiding
    """

    def __init__(self,capp):
        self.capp = capp
        self.contractpath = self.capp.contractpath
        self.globalassumptions = []
        self.hiddenstructs = {}
        self.hiddenfields = {}
        if not self.contractpath is None:
            self._initialize()

    def is_hidden_struct(self,filename,compname):
        return filename in self.hiddenstructs and compname in self.hiddenstructs[filename]

    def is_hidden_field(self,compname,fieldname):
        return compname in self.hiddenfields and fieldname in self.hiddenfields[compname]

    def add_no_free(self):
        if 'no-free' in self.globalassumptions: return
        self.globalassumptions.append('no-free')
        self.save_global_xml_contract()

    def save_global_xml_contract(self):
        cnode = ET.Element('global-definitions')
        anode = ET.Element('global-assumptions')
        for a in self.globalassumptions:
            gnode = ET.Element('ga')
            gnode.set('name',a)
            anode.append(gnode)
        cnode.append(anode)
        UF.save_global_xml_contract(self.contractpath,cnode)

    def _initialize(self):
        globalcontract = None
        if UF.has_global_contract(self.contractpath):
            logging.info('Load globaldefs.json contract file')
            globalcontract = UF.get_global_contract(self.contractpath)
        if globalcontract is not None:
            if 'hidden-structs' in globalcontract:
                self.hiddenstructs = globalcontract['hidden-structs']
            if 'hidden-fields' in globalcontract:
                self.hiddenfields = globalcontract['hidden-fields']
        if UF.has_global_xml_contract(self.contractpath):
            logging.info('Load globaldefs.xml contract file')
            globalxmlcontract = UF.get_global_xml_contract(self.contractpath)
            if 'global-assumptions' in globalxmlcontract:
                for a in globalxmlcontract.find('global-assumptions').findall('ga'):
                    self.globalassumptions.append(a.get('name'))
