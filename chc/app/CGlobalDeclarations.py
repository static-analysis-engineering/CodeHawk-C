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
import chc.util.IndexedTable as IT
import chc.app.CInitInfo as CI

from chc.app.CGlobalDictionary import CGlobalDictionary
from chc.app.CCompInfo import CCompInfo
from chc.app.CFieldInfo import CFieldInfo
from chc.app.CVarInfo import CVarInfo
from chc.util.IndexedTable import IndexedTable

initinfo_constructors = {
    'single':lambda x:CI.CSingleInitInfo(*x),
    'compound':lambda x:CI.CCompoundInitInfo(*x)
    }

class ConjectureFailure(Exception):
    def __init__(self,ckey,gckey):
        self.ckey = ckey
        self.gckey = gckey
        
    def __str__(self):
        return ('Compinfo ' + str(self.ckey)
                    + ' is not compatible with global compinfo '
                    + str(self.gckey))


class CGlobalDeclarations(object):
    """Dictionary that indexes global variables and struct definitions from all files.

    The indexing of struct definitions may involve backtracking in the case of
    structs that contain pointer references to itself, or circular references that 
    involve multiple structs.

    The backtracking is performed per file. When a struct (represented by a compinfo)
    is indexed its status is set to pending. When a request for a TComp ckey
    conversion for the same compinfo is encountered a new global key is conjectured
    as follows:
    - gckey that has already been reserved for this ckey
    - gckey that has already been conjectured for this ckey
    - gckey for an existing global compinfo that has the same fields, if
           (ckey,gckey) is not in the list of incompatibles
   - reserve a new key from the indexed table and set its status to reserved,
           and remove its pending status


    When the compinfo for ckey has been constructed the state is updated as follows:
    - if ckey had a reserved key the reserved key is now committed
    - if ckey had a conjectured key and the conjectured key is the same as the
          returned gckey, nothing needs to be done
    - if ckey had a conjectured key but the conjectured key is not the same as the
          returned gckey, add (ckey,gckey) to the list of incompatibles, reset
          the indexed table to the file checkpoint, and re-index all compinfos
          in the file.

    """
    

    def __init__(self,capp):
        self.capp = capp
        # Basic types dictionary
        self.dictionary = CGlobalDictionary(self)

        # Global definitions and declarations dictionary
        self.fieldinfo_table = IT.IndexedTable('fieldinfo-table')
        self.compinfo_table = IT.IndexedTable('compinfo-table')
        self.varinfo_table = IT.IndexedTable('varinfo-table')
        self.initinfo_table = IT.IndexedTable ('initinfo-table')
        self.offset_init_table = IT.IndexedTable ('offset-init-table')
        self.tables = [
            (self.fieldinfo_table,self._read_xml_fieldinfo_table),
            (self.compinfo_table,self._read_xml_compinfo_table),
            (self.initinfo_table,self._read_xml_initinfo_table),
            (self.varinfo_table,self._read_xml_varinfo_table),
            (self.offset_init_table,self._read_xml_offset_init_table) ]

        # Collect names for compinfo equivalence classes
        self.compinfo_names = {}                  # gckey -> string set

        # Collect storage classes for varinfo equivalence classes
        self.varinfo_storage_classes = {}         # gvid -> string

        # Support data structures for linker
        self.ckey2gckey = {}                      # fid -> ckey -> gckey
        self.vid2gvid = {}                        # fid -> vid -> gvid
        self.fieldstrings = {}                    # string of joined fields -> gckey list
        self.pending = []
        self.conjectured = {}                     # ckey -> gckey
        self.reserved = {}                        # ckey -> gckey
        self.incompatibles = {}                   # ckey -> gckey set
        self.default_function_prototypes = []     # (fid,varinfo) list

        self.globalcontract = self.capp.globalcontract
        
        self._initialize()
        if self.compinfo_table.size() == 0: self.index_opaque_struct()

    def is_hidden_field (self,compname,fieldname):
        if self.globalcontract is not None:
            return self.globalcontract.is_hidden_field(compname,fieldname)
        return False

    def is_hidden_struct(self,filename,compname):
        if self.globalcontract is not None:
            return self.globalcontract.is_hidden_struct(filename,compname)
        return False

    def get_stats(self):
        lines = []
        lines.append('=' * 80)
        lines.append('Dictionary')
        lines.append('=' * 80)
        lines.append(self.dictionary.get_stats())
        lines.append('=' * 80)
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(t.name.ljust(25) + str(t.size()).rjust(4))
        return '\n'.join(lines)

    # ---------------------- Retrieve items from definitions dictionary --------
    
    def get_fieldinfo(self,ix): return self.fieldinfo_table.retrieve(ix)

    def get_varinfo(self,ix): return self.varinfo_table.retrieve(ix)

    def get_compinfo(self,ix): return self.compinfo_table.retrieve(ix)

    def get_initinfo(self,ix): return self.initinfo_table.retrieve(ix)

    def get_offset_init(self,ix): return self.offset_init_table.retrieve(ix)

    # --------------------- Retrieve derived items -----------------------------

    def has_varinfo_by_name(self,name):
        return any([ v.vname == name for v in self.varinfo_table.values() ])

    def get_varinfo_by_name(self,name):
        for v in self.varinfo_table.values():
            if v.vname == name: return v

    def get_structname(self,ckey):
        if ckey in self.compinfo_names:
            return list(self.compinfo_names[ckey])[0]
        logging.warning('Compinfo name for ' + str(ckey) + ' not found')
        print('Compinfo name for ' + str(ckey) + ' not found ')
        print(str(self.compinfo_names))

    def get_gcompinfo(self,fid,ckey):
        gckey = self.get_gckey(fid,ckey)
        if not gckey is None:
            return self.compinfo_table.retrieve(gckey)
        return None

    def is_struct(self,ckey):
        cinfo = self.get_compinfo(ckey)
        if cinfo is None:
            print('Compinfo ' + str(ckey) + ' not found')
            return False
        return self.get_compinfo(ckey).isstruct

    def convert_ckey(self,ckey,fid=-1):
        if fid >= 0:
            return self.get_gckey(fid,ckey)
        else:
            return ckey

    def get_gckey(self,fid,ckey):
        if fid in self.ckey2gckey:
            if ckey in self.ckey2gckey[fid]:
                return self.ckey2gckey[fid][ckey]
        return None

    def get_gvid(self,fid,vid):
        if fid in self.vid2gvid:
            if vid in self.vid2gvid[fid]:
                return self.vid2gvid[fid][vid]
        return None

    def list_compinfos(self):
        lines = []
        for gckey in self.compinfo_names:
            names = ','.join(list(self.compinfo_names[gckey]))
            lines.append(names)
        return '\n'.join(sorted(lines))

    def show_compinfos(self,name):
        result = []
        gckeys = [ x for x in self.compinfo_names.keys() if name in self.compinfo_names[x] ]
        for k in gckeys:
            result.append((k,self.compinfo_table.retrieve(k)))
        return result


    # -------------------- Linker support services -----------------------------
        
    def reset_conjectures(self):
        self.pending = []
        self.conjectured = {}
        self.reserved = {}

    def cleanup(self,checkpoint,ckey,gckey):
        if not ckey in self.incompatibles: self.incompatibles[ckey] = set([])
        self.incompatibles[ckey].add(gckey)
        self.reset_conjectures()
        for k in self.compinfo_names.keys():
            if k >= checkpoint: self.compinfo_names.pop(k)
        for k in self.fieldstrings.keys():
            for gckey in self.fieldstrings[k]:
               if gckey >= checkpoint:
                   self.fieldstrings[k].remove(gckey)

    def get_state(self):
        lines = []
        lines.append('Pending    : ' + str(self.pending))
        lines.append('Conjectured: ' + str(self.conjectured))
        lines.append('Reserved   : ' + str(self.reserved))
        return '\n'.join(lines)

    def get_field_strings_conjecture(self,cname,fields,ckey):
        if fields in self.fieldstrings:
            for gckey in self.fieldstrings[fields]:
                conjecturedkey = gckey
                if ckey in self.incompatibles and conjecturedkey in self.incompatibles[ckey]:
                    pass
                else: break
            else:
                return None
            return conjecturedkey
        return None

    def conjecture_key(self,fid,compinfo):
        ckey = compinfo.get_ckey()
        if ckey in self.reserved:
            return self.reserved[ckey]
        if ckey in self.conjectured:
            return self.conjectured[ckey]
        conjecturedkey = self.get_field_strings_conjecture(compinfo.get_name(),compinfo.get_field_strings(),ckey)
        if conjecturedkey is None:
            reservedkey = self.compinfo_table.reserve()
            self.reserved[ckey] = reservedkey
            self.pending.remove(ckey)
            return reservedkey
        else:   
            self.conjectured[ckey] = conjecturedkey
            self.pending.remove(ckey)
            return conjecturedkey

    def register_gcompinfo(self,fid,ckey,gcompinfo):
        gckey = gcompinfo.get_ckey()
        fields = gcompinfo.get_field_strings()
        if not fields in self.fieldstrings: self.fieldstrings[fields] = []
        if not gckey in self.fieldstrings[fields]: self.fieldstrings[fields].append(gckey)
        self.ckey2gckey[fid][ckey] = gckey

    # ------------------- Indexing compinfos -----------------------------------
    
    def index_fieldinfo(self,fieldinfo,compinfoname):
        tags = [ fieldinfo.fname ]
        if self.is_hidden_field(compinfoname, fieldinfo.fname):
            gftype = self.index_opaque_struct_pointer()
        else:
            gftype = self.dictionary.index_typ(fieldinfo.ftype.expand().strip_attributes())
        args = [ -1, gftype, fieldinfo.bitfield, -1, -1  ]
        def f(index,key): return CFieldInfo(self,index,tags,args)
        gfieldinfo = self.fieldinfo_table.add(IT.get_key(tags,args),f)
        return gfieldinfo

    def index_compinfo_key(self,compinfo,fid):    # only compinfo's from files should be indexed
        ckey = compinfo.get_ckey()
        gckey = self.get_gckey(fid,ckey)
        logmsg = ('Compinfo ' + compinfo.get_name() + ' (fid,ckey: ' + str(fid)
                      + ',' + str(ckey) + '): ')
        if not gckey is None: return gckey
        if ckey in self.conjectured:
            logging.info(logmsg +  'conjectured key: ' + str(self.conjectured[ckey]))
            return self.conjectured[ckey]
        if ckey in self.reserved:
            logging.info(logmsg + ' reserved key: ' + str(self.reserved[ckey]))
            return self.reserved[ckey]
        if ckey in self.pending:
            pendingkey = self.conjecture_key(fid,compinfo)
            logging.info(logmsg + 'new pending key: ' + str(pendingkey))
            return pendingkey
        return self.index_compinfo(fid,compinfo).get_ckey()

    def index_opaque_struct(self):
        tags = ['?']
        args = [ -1, 1, -1 ]
        def f(index,key):
            if not index in self.compinfo_names: self.compinfo_names[index] = set([])
            self.compinfo_names[index].add('opaque-struct')
            return CCompInfo(self,index,tags,args)
        return self.compinfo_table.add(IT.get_key(tags,args),f)

    def get_opaque_struct(self):
        return self.compinfo_table.retrieve(1)

    def index_opaque_struct_pointer(self):
        tags = ['tcomp']
        args = [ 1 ]
        comptypix = self.dictionary.mk_typ(tags,args)
        tags = [ 'tptr' ]
        args = [ comptypix ]
        return self.dictionary.mk_typ(tags,args)

    def index_compinfo(self,fid,compinfo):
        filename = self.capp.get_file_by_index(fid).name
        ckey = compinfo.get_ckey()
        cname = compinfo.get_name()
        if self.is_hidden_struct(filename,cname):
            logging.info('Hide struct ' + cname + ' in file ' + filename)
            return self.get_opaque_struct()
        gcompinfo = self.get_gcompinfo(fid,ckey)
        if not gcompinfo is None:
            return gcompinfo
        self.pending.append(compinfo.get_ckey())
        tags = ['?']
        fields = [ self.index_fieldinfo(f,cname) for f in compinfo.fields ]
        args = [ -1, 1 if compinfo.isstruct else 0, -1 ] + fields
        key = (','.join(tags),','.join([str(x) for x in args]))
        if ckey in self.reserved:
            gckey = self.reserved[ckey]
            gcompinfo = CCompInfo(self,gckey,tags,args)
            self.compinfo_table.commit_reserved(gckey,key,gcompinfo)
            self.reserved.pop(ckey)
            if not gckey in self.compinfo_names: self.compinfo_names[gckey] = set([])
            self.compinfo_names[gckey].add(compinfo.get_name())
            self.register_gcompinfo(fid,ckey,gcompinfo)
            return gcompinfo
        def f(index,key):
            if not index in self.compinfo_names: self.compinfo_names[index] = set([])
            self.compinfo_names[index].add(compinfo.get_name())
            return CCompInfo(self,index,tags,args)
        compinfoindex = self.compinfo_table.add(key,f)
        gcompinfo = self.get_compinfo(compinfoindex)
        if ckey in self.conjectured:
            conjecturedkey = self.conjectured[ckey]
            gckey = gcompinfo.get_ckey()
            if gckey == conjecturedkey:
                self.ckey2gckey[fid][ckey] = gcompinfo.get_ckey()
                self.conjectured.pop(ckey)
                return gcompinfo
            else:
                logging.info('Conjecture failure for ' + compinfo.get_name()
                                 + ' (fid:' + str(fid) + ', ckey:' + str(ckey)
                                 + ', gckey: ' + str(gckey)
                                 + ', conjectured key: ' + str(conjecturedkey) + ')')
                raise ConjectureFailure(ckey,conjecturedkey)
        else:
            self.register_gcompinfo(fid,ckey,gcompinfo)
            self.pending.remove(compinfo.get_ckey())
            return gcompinfo

    def index_file_compinfos(self,fid,compinfos):
        if len(compinfos) > 0:
            while(1):
                self.compinfo_table.set_checkpoint()
                self.ckey2gckey[fid] = {}
                try:
                    for c in compinfos:
                        self.index_compinfo(fid,c)
                except ConjectureFailure as e:
                    checkpoint = self.compinfo_table.reset_to_checkpoint()
                    self.cleanup(checkpoint,e.ckey,e.gckey)
                else:
                    self.compinfo_table.remove_checkpoint()
                    self.incompatibles = {}
                    break


    # -------------------- Indexing varinfos -----------------------------------
    
    def index_init(self,init,fid=-1):
        try:
            if init.is_single():
                tags = [ 'single' ]
                args = [ self.dictionary.index_exp(init.get_exp()) ]
                def f(index,key): return CI.CSingleInitInfo(self,index,tags,args)
                return self.initinfo_table.add(IT.get_key(tags,args),f)
            if init.is_compound():
                tags = [ 'compound' ]
                gtype = self.dictionary.index_typ(init.get_typ())
                oinits = [ self.index_offset_init(x)
                            for x in init.get_offset_initializers() ]
                args = [ gtype ] + oinits
                def f(index,key): return CI.CCompoundInitInfo(self,index,tags,args)
                return self.initinfo_table.add(IT.get_key(tags,args),f)
            raise InvalidArgumentError('indexinit: ' + str(init))
        except IndexedTableError as e:
            print('Error in indexing ' + str(init) + ': ' + str(e))
            
        
    def index_offset_init(self,oinit,fid=-1):
        args = [ self.dictionary.index_offset(oinit.get_offset()),
                     self.index_init(oinit.get_initializer()) ]
        def f(index,key): return CI.COffsetInitInfo(self,index,[],args)
        return self.offset_init_table.add(IT.get_key([],args),f)


    def index_varinfo_vid(self,vid,fid):
        if fid == -1: return vid
        return self.get_gvid(vid,fid)

    def index_varinfo(self,fid,varinfo):
        if varinfo.vtype.is_default_function_prototype():
            self.default_function_prototypes.append((fid,varinfo))
            return
        vid = varinfo.get_vid()
        if varinfo.get_vstorage() == 's':
            vname = varinfo.vname + '__file__' + str(fid) + '__'
        else:
            vname = varinfo.vname
        vtypeix = self.dictionary.index_typ(varinfo.vtype.expand().strip_attributes())
        vtype = self.dictionary.get_typ(vtypeix)
        if varinfo.has_initializer():
            vinit = varinfo.get_initializer()
            gvinit = [ self.index_init(vinit,fid=fid) ]
        else:
            gvinit = []            
        tags = [ vname ]
        vargs = varinfo.args
        vaddrof = 1 if vtype.is_function() else vargs[6]
        args = [ -1, vtypeix, -1, vargs[3], vargs[4], -1, vaddrof, vargs[7] ] + gvinit
        key = (','.join(tags),','.join([str(x) for x in args]))
        def f(index,key): return CVarInfo(self,index,tags,args)
        gvarinfoindex = self.varinfo_table.add(key,f)
        gvarinfo = self.get_varinfo(gvarinfoindex)
        gvid = gvarinfo.get_vid()
        if not gvid in self.varinfo_storage_classes: self.varinfo_storage_classes[gvid] = ''
        vstorageclass = varinfo.tags[1]
        if not vstorageclass in self.varinfo_storage_classes[gvid]:
            self.varinfo_storage_classes[gvid] += vstorageclass
        self.vid2gvid[fid][vid] = gvarinfo.get_vid()
        logging.debug('Fid: ' + str(fid) + ', vid: ' + str(vid) + ', gvid: '
                         + str(gvarinfo.get_vid()) + ': ' + gvarinfo.vname)
        return gvarinfo

    def index_file_varinfos(self,fid,varinfos):
        if len(varinfos) > 0:
            self.vid2gvid[fid] = {}
            for v in varinfos:
                self.index_varinfo(fid,v)

    def resolve_default_function_prototypes(self):
        print('Resolving ' + str(len(self.default_function_prototypes)) + ' function prototypes')
        for (fid,varinfo) in self.default_function_prototypes:
            def f(key): return key[0].startswith(varinfo.vname)
            candidates = self.varinfo_table.retrieve_by_key(f)
            if len(candidates) == 1:
                self.vid2gvid[fid][varinfo.get_vid()] = candidates[0][1].get_vid()
                logging.info('Resolved prototype for ' + varinfo.vname)
            else:
                pcandidates = ','.join( [ c[1].vname for c in candidates ])
                for (_,c) in candidates:
                    if c.vname == varinfo.vname:
                        self.vid2gvid[fid][varinfo.get_vid()] = c.get_vid()
                        logging.warning('Selected prototype ' + c.vname + ' for ' + varinfo.vname
                                            + ' from multiple candidates: ' + pcandidates)
                        break
                else:
                    msg = ('Unable to resolve prototype for ' + varinfo.vname + ': '
                            + str(len(candidates)) + ': ' + pcandidates)
                    logging.warning(msg)

    # -------------------- Writing xml -----------------------------------------

    def write_xml(self,node):
        dnode = ET.Element('dictionary')
        self.dictionary.write_xml(dnode)
        node.append(dnode)
        
        def f(n,r):r.write_xml(n)
        for (t,_) in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode,f)
            node.append(tnode)

        cnode = ET.Element('compinfo-names')
        for ckey in sorted(self.compinfo_names):
            nnode = ET.Element('n')
            nnode.set('ckey',str(ckey))
            nnode.set('names',','.join(sorted(self.compinfo_names[ckey])))
            cnode.append(nnode)
        node.append(cnode)
            
        vsnode = ET.Element('varinfo-storage-classes')
        for vid in sorted(self.varinfo_storage_classes):
            if 'n' in self.varinfo_storage_classes[vid]: continue
            vnode = ET.Element('n')
            vnode.set('vid',str(vid))
            vnode.set('s',self.varinfo_storage_classes[vid])
            vsnode.append(vnode)
        node.append(vsnode)

    def __str__(self):
        lines = []
        lines.append(str(self.dictionary))
        for (t,_) in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return '\n'.join(lines)

    def _initialize(self):
        # Initialize global declarations from globaldefinitions file if available
        xnode = UF.get_global_declarations_xnode(self.capp.path)       # globals
        if xnode is None: return
        for (t,f) in self.tables:
            f(xnode.find(t.name))
        for n in xnode.find('compinfo-names').findall('n'):
            self.compinfo_names[int(n.get('ckey'))] = set(n.get('names').split(','))
        for n in xnode.find('varinfo-storage-classes'):
            self.varinfo_storage_classes[int(n.get('vid'))] = n.get('s')        
            
    def _read_xml_fieldinfo_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CFieldInfo(*args)
        self.fieldinfo_table.read_xml(xnode,'n',get_value)

    def _read_xml_compinfo_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CCompInfo(*args)
        self.compinfo_table.read_xml(xnode,'n',get_value)

    def _read_xml_varinfo_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CVarInfo(*args)
        self.varinfo_table.read_xml(xnode,'n',get_value)

    def _read_xml_initinfo_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            tag = rep[1][0]
            args = (self,) + rep
            return initinfo_constructors[tag](args)
        self.initinfo_table.read_xml(xnode,'n',get_value)

    def _read_xml_offset_init_table(self,xnode):
        def get_value(node):
            rep = IT.get_rep(node)
            args = (self,) + rep
            return CI.COffsetInitInfo(*args)
        self.offset_init_table.read_xml(xnode,'n',get_value)

    def _read_xml_varinfo_storage_classes(self,xnode):
        for n in xnode.findall('n'):
            vid = int(n.get('vid'))
            self.varinfo_storage_classes[vid] = set([])
            for c in n.get('s'):
                self.varinfo_storage_classes[vid].add(c)

    def _read_xml_compinfo_names(self,xnode):
        for n in xnode.findall('n'):
            ckey = int(n.get('ckey'))
            names = n.get('names').split(',')
            self.compinfo_names[ckey] = set(names)
