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

import itertools

import xml.etree.ElementTree as ET


from chc.linker.CompCompatibility import CompCompatibility
from chc.app.CCompInfo import CCompInfo

from chc.util.UnionFind import UnionFind
from chc.app.CGlobalDictionary import CGlobalDictionary

import chc.util.fileutil as UF
import chc.util.xmlutil as UX

'''
Starting point: a list of (fileindex,compinfo key) pairs that identify the
   locally declared structs

Goal: produce equivalence classes of (fileindex,compinfo key) pairs that
   are associated with (structurally) equivalent structs, assign a
   global id to each distinct struct, and create a mapping between the
   (fileindex,compinfo key) pairs and the global id (xrefs) and a
   mapping between the global id and an instance of a struct from the
   corresponding equivalence class. All nested field struct types must
   be renamed with global ids.

'''

class CLinker(object):

    def __init__(self,capp):
        self.capp = capp                              # CApplication
        self.declarations = self.capp.declarations

    def get_file_compinfo_xrefs(self,fileindex):
        result = {}
        for (fidx,ckey) in self.compinfoxrefs:
            if fidx == fileindex: result[ckey] = self.compinfoxrefs[(fidx,ckey)]
        return result

    def get_file_varinfo_xrefs(self,fileindex):
        result = {}
        for (fidx,vid) in self.varinfoxrefs:
            if fidx == fileindex: result[vid] = self.varinfoxrefs[(fidx,vid)]
        return result

    def get_global_compinfos(self): return self.compinfoinstances

    def get_shared_instances(self): return self.sharedinstances

    def link_compinfos(self):
        def f(cfile):
            print('Linking ' + cfile.name)
            compinfos = cfile.declarations.get_compinfos()
            self.declarations.index_file_compinfos(cfile.index,compinfos)
        self.capp.iter_files(f)
        ckey2gckey = self.declarations.ckey2gckey
        for fid in ckey2gckey:
            for ckey in ckey2gckey[fid]:
                gckey = ckey2gckey[fid][ckey]
                self.capp.indexmanager.add_ckey2gckey(fid,ckey,gckey)
    '''
    def linkcompinfos(self):
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
    '''

    def link_varinfos(self):
        def f(cfile):
            varinfos = cfile.declarations.get_global_varinfos()
            self.declarations.index_file_varinfos(cfile.index,varinfos)
        self.capp.iter_files(f)
        self.declarations.resolve_default_function_prototypes()
        vid2gvid = self.declarations.vid2gvid
        for fid in vid2gvid:
            for vid in vid2gvid[fid]:
                gvid = vid2gvid[fid][vid]
                self.capp.indexmanager.add_vid2gvid(fid,vid,gvid)
    '''
    def linkvarinfos(self): 
        globalvarinfos = {}       
        for vinfo in self.varinfos:
            name = vinfo.getname()
            if vinfo.getstorage() == 'static': 
                fileindex = vinfo.getfile().getindex()
                name = name + '__file__' + str(fileindex) + '__'
            if not name in globalvarinfos: globalvarinfos[name] = []
            globalvarinfos[name].append(vinfo)

        gvid = 1
        for name in sorted(globalvarinfos):
            for vinfo in globalvarinfos[name]:
                id = vinfo.getid()
                self.varinfoxrefs[id] = gvid
                self.capp.indexmanager.addvid2gvid(id[0],id[1],gvid)
            gvid += 1
    '''
    def save_global_compinfos(self):
        path = self.capp.path
        xroot = UX.get_xml_header('globals','globals')
        xnode = ET.Element('globals')
        xroot.append(xnode)
        self.declarations.write_xml(xnode)
        filename = UF.get_global_definitions_filename(path)
        with open(filename,'w') as fp:
            fp.write(UX.doc_to_pretty(ET.ElementTree(xroot)))


    def _checkcompinfopairs(self):
        self.possiblycompatiblestructs = []
        compinfos = sorted(self.compinfos,key=lambda c:c.getid())
        print('Checking all combinations of ' + str(len(compinfos)) + ' struct definitions')
        for (c1,c2) in itertools.combinations(compinfos,2):
            if c1.getid() == c2.getid(): continue
            pair = (c1.getid(),c2.getid())
            if c1.getfieldcount() == c2.getfieldcount():
                if pair in self.notcompatiblestructs: continue
                cc = CompCompatibility(c1,c2)
                if cc.are_shallow_compatible(self.notcompatiblestructs):
                    self.possiblycompatiblestructs.append(pair)
                else:
                    self.notcompatiblestructs.add(pair)

