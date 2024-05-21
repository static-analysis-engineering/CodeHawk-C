# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
# Copyright (c) 2020-2023 Henny B. Sipma
# Copyright (c) 2024      Aarno Labs LLC
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

import itertools

import xml.etree.ElementTree as ET

from typing import Dict, List, Tuple, TYPE_CHECKING

from chc.app.CCompInfo import CCompInfo
from chc.app.IndexManager import FileKeyReference, FileVarReference
from chc.app.CGlobalDictionary import CGlobalDictionary

from chc.linker.CompCompatibility import CompCompatibility

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger
from chc.util.UnionFind import UnionFind
import chc.util.xmlutil as UX

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CGlobalDeclarations import CGlobalDeclarations
    from chc.app.IndexManager import IndexManager

"""
Starting point: a list of (fileindex,compinfo key) pairs that identify the
   locally declared structs

Goal: produce equivalence classes of (fileindex,compinfo key) pairs that
   are associated with (structurally) equivalent structs, assign a
   global id to each distinct struct, and create a mapping between the
   (fileindex,compinfo key) pairs and the global id (xrefs) and a
   mapping between the global id and an instance of a struct from the
   corresponding equivalence class. All nested field struct types must
   be renamed with global ids.

"""


class CLinker:
    def __init__(self, capp: "CApplication") -> None:
        self._capp = capp
        self._compinfos: List["CCompInfo"] = []
        self._compinfoxrefs: Dict[Tuple[int, int], int] = {}
        self._varinfoxrefs: Dict[Tuple[int, int], int] = {}

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def indexmanager(self) -> "IndexManager":
        return self.capp.indexmanager

    @property
    def declarations(self) -> "CGlobalDeclarations":
        return self.capp.declarations

    @property
    def compinfos(self) -> List["CCompInfo"]:
        return self._compinfos

    @property
    def compinfoxrefs(self) -> Dict[Tuple[int, int], int]:
        return self._compinfoxrefs

    @property
    def varinfoxrefs(self) -> Dict[Tuple[int, int], int]:
        return self._varinfoxrefs

    def get_file_compinfo_xrefs(self, fileindex: int) -> Dict[int, int]:
        result: Dict[int, int] = {}
        for (fidx, ckey) in self.compinfoxrefs:
            if fidx == fileindex:
                result[ckey] = self.compinfoxrefs[(fidx, ckey)]
        return result

    def get_file_varinfo_xrefs(self, fileindex: int) -> Dict[int, int]:
        result: Dict[int, int] = {}
        for (fidx, vid) in self.varinfoxrefs:
            if fidx == fileindex:
                result[vid] = self.varinfoxrefs[(fidx, vid)]
        return result

    """
    def get_global_compinfos(self):
        return self.compinfoinstances

    def get_shared_instances(self):
        return self.sharedinstances
    """

    def link_compinfos(self) -> None:

        chklogger.logger.info("Link compinfos")

        # index and connect the compinfos from the individual files
        for cfile in self.capp.cfiles:
            compinfos = cfile.get_compinfos()
            self.declarations.index_file_compinfos(cfile.index, compinfos)

        # register the relationships found with the index manager
        ckey2gckey = self.declarations.ckey2gckey
        for fid in ckey2gckey:
            for ckey in ckey2gckey[fid]:
                gckey = ckey2gckey[fid][ckey]
                filekey = FileKeyReference(fid, ckey)
                self.capp.indexmanager.add_ckey2gckey(filekey, gckey)

    """
    def linkcompinfos(self) -> None:
        self._checkcompinfopairs()

        print('Found ' + str(len(self.possiblycompatiblestructs)) +
              ' compatible combinations')

        ppcount = len(self.possiblycompatiblestructs) + len(self.notcompatiblestructs)
        pcount = len(self.possiblycompatiblestructs)

        while pcount < ppcount:
            ppcount = pcount
            self._checkcompinfopairs()
            pcount = len(self.possiblycompatiblestructs)
            print('Found ' + str(pcount) + ' compatible combinations')

        gcomps = UnionFind()

        for c in self.compinfos:
            gcomps[ c.getid() ]

        for (c1,c2) in self.possiblycompatiblestructs: gcomps.union(c1,c2)

        eqclasses = set([])
        for c in self.compinfos:
            eqclasses.add(gcomps[c.id])

        print('Created ' + str(len(eqclasses)) + ' globally unique struct ids')

        gckey = 1
        for c in sorted(eqclasses):
            self.globalcompinfos[c] = gckey
            gckey += 1

        for c in self.compinfos:
            id = c.id
            gckey = self.globalcompinfos[gcomps[id]]
            self.compinfoxrefs[id] = gckey
            self.capp.indexmanager.addckey2gckey(id[0],id[1],gckey)

        for c in self.compinfos:
            id = c.id
            gckey = self.globalcompinfos[gcomps[id]]
            if not gckey in self.compinfoinstances:
                fidx = id[0]
                xrefs = self.getfilecompinfoxrefs(fidx)
                self.compinfoinstances[gckey] = CCompInfo(c.cfile,c.xnode)
                filename = self.capp.getfilebyindex(id[0]).getfilename()
                self.sharedinstances[gckey] = [ (filename,c) ]
            else:
                filename = self.capp.getfilebyindex(id[0]).getfilename()
                self.sharedinstances[gckey].append((filename,c))

    """

    def link_varinfos(self) -> None:
        def f(cfile: "CFile") -> None:
            varinfos = cfile.declarations.get_global_varinfos()
            self.declarations.index_file_varinfos(cfile.index, varinfos)

        self.capp.iter_files(f)
        self.declarations.resolve_default_function_prototypes()
        vid2gvid = self.declarations.vid2gvid
        for fid in vid2gvid:
            for vid in vid2gvid[fid]:
                gvid = vid2gvid[fid][vid]
                filevar = FileVarReference(fid, vid)
                self.indexmanager.add_vid2gvid(filevar, gvid)

    def save_global_compinfos(self) -> None:
        path = self.capp.targetpath
        xroot = UX.get_xml_header("globals", "globals")
        xnode = ET.Element("globals")
        xroot.append(xnode)
        self.declarations.write_xml(xnode)
        filename = UF.get_global_definitions_filename(path, self.capp.projectname)
        chklogger.logger.info("Saving global compinfos to %s", filename)
        with open(filename, "w") as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))
