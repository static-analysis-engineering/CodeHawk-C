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
import chc.util.xmlutil as UX

fidvidmax_initial_value = 1000000

'''
TODO:
  - save gxrefs file if new vid's were added to a file
'''

class IndexManager(object):

    def __init__(self,issinglefile):
        self.issinglefile = issinglefile    # application consists of a single file
        
        self.vid2gvid = {}        # fid -> vid -> gvid
        self.gvid2vid = {}        # gvid -> fid -> vid

        self.fidvidmax = {}       # fid -> maximum vid in file with index fid

        self.ckey2gckey = {}      # fid -> ckey -> gckey
        self.gckey2ckey = {}      # gckey -> fid -> ckey

        self.gviddefs = {}        # gvid -> fid  (file in which gvid is defined)

    def get_vid_gvid_subst(self,fid): return self.vid2gvid[fid]

    def get_fid_gvid_subset(self,fileindex):
        result = {}
        for gvid in self.gvid2vid:
            for fid in self.gvid2vid[gvid]:
                if fid == fileindex:
                    result[gvid] = self.gvid2vid[gvid][fid]
        return result

    '''return the fid of the file in which this vid is defined, with the local vid.'''
    def resolve_vid(self,fid,vid):
        if self.issinglefile:
            return (fid,vid)
        msg = 'indexmgr:resolve-vid(' + str(fid) + ',' + str(vid) + '): '
        if fid in self.vid2gvid:
            if vid in self.vid2gvid[fid]:
                gvid = self.vid2gvid[fid][vid]
                if gvid in self.gviddefs:
                    tgtfid = self.gviddefs[gvid]
                    if gvid in self.gvid2vid:
                        if tgtfid in self.gvid2vid[gvid]:
                            return (tgtfid,self.gvid2vid[gvid][tgtfid])
                        logging.debug(msg + 'Target fid ' + str(tgtfid) + ' not found in gvid2vid['
                                            + str(gvid) + ']')
                        return None
                    logging.debug(msg + 'Global vid ' + str(gvid) + ' not found in gvid2vid')
                    return None
                logging.debug(msg + 'Global vid ' + str(gvid) + ' not found in gviddefs')
                return None
            logging.debug(msg + 'Local vid ' + str(vid) + ' not found in vid2gvid[' + str(fid) + ']')
            return None
        logging.debug(msg + 'File id ' + str(fid) + ' not found in vid2gvid')
        return None

    '''return a list of (fid,vid) pairs that refer to the same global variable.'''
    def get_gvid_references(self,gvid):
        result = []
        for fid in self.gvid2vid[gvid]:
            result.append((fid,self.gvid2vid[gvid][fid]))
        return result

    def has_gvid_reference(self,gvid,fid):
        if gvid in self.gvid2vid:
            return fid in self.gvid2vid[gvid]
        else:
            return False

    def get_gvid_reference(self,gvid,fid):
        if gvid in self.gvid2vid:
            if fid in self.gvid2vid[gvid]:
                return self.gvid2vid[gvid][fid]

    '''return a list of (fid,vid) pairs that refer to the same variable.'''
    def get_vid_references(self,srcfid,srcvid):
        result = []
        if self.issinglefile: return result
        if srcfid in self.vid2gvid:
            if srcvid in self.vid2gvid[srcfid]:
                gvid = self.vid2gvid[srcfid][srcvid]
                for fid in self.gvid2vid[gvid]:
                    if fid == srcfid: continue
                    result.append((fid,self.gvid2vid[gvid][fid]))
        return result

    '''return the vid in the file with index fidtgt for the variable vid in fidsrc.

    If the target file does not map the gvid then create a new vid in this file to
    map the gvid.
    '''
    def convert_vid(self,fidsrc,vid,fidtgt):
        if self.issinglefile:
            return vid
        gvid = self.get_gvid(fidsrc,vid)
        msg = 'indexmgr:convert-vid(' + str(fidsrc) + ',' + str(vid) + ',' + str(fidtgt) + '): '
        if not gvid is None:
            if gvid in self.gvid2vid:
                if fidtgt in self.gvid2vid[gvid]:
                    return self.gvid2vid[gvid][fidtgt]
                else:
                    logging.warning(msg + 'Create new index for global variable: '
                                        + str(gvid))
                    return None
                '''
                    self.gvid2vid[gvid][fidtgt] = self.fidvidmax[fidtgt]
                    self.fidvidmax[fidtgt] += 1
                    return self.gvid2vid[gvid][fidtgt]
                '''

    '''return the gvid of the vid in the file with index fid.'''
    def get_gvid(self,fid,vid):
        if self.issinglefile: return vid
        if fid in self.vid2gvid:
            if vid in self.vid2gvid[fid]:
                return self.vid2gvid[fid][vid]

    '''return the vid of the gvid in the file with index fid.'''
    def get_vid(self,fid,gvid):
        if self.issinglefile: return vid
        if gvid in self.gvid2vid:
            if fid in self.gvid2vid[gvid]:
                return self.gvid2vid[gvid][fid]

    def get_gckey(self,fid,ckey):
        if self.issinglefile: return ckey
        if fid in self.ckey2gckey:
            if ckey in self.ckey2gckey[fid]:
                return self.ckey2gckey[fid][ckey]

    def convert_ckey(self,fidsrc,ckey,fidtgt):
        if self.issinglefile:
            return ckey
        gckey = self.get_gckey(fidsrc,ckey)
        if not gckey is None:
            if gckey in self.gckey2ckey:
                if fidtgt in self.gckey2ckey[gckey]:
                    return self.gckey2ckey[gckey][fidtgt]
                else:
                    logging.debug('Target fid ' + str(fidtgt) + ' not found for global key ' + str(gckey))
            else:
                logging.debug('Global key ' + str(gckey) + ' not found in converter')
        else:
            logging.debug('Local key ' + str(ckey) + ' not found for source file ' + str(fidsrc))

    def add_ckey2gckey(self,fid,ckey,gckey):
        if not fid in self.ckey2gckey:
            self.ckey2gckey[fid] = {}
        self.ckey2gckey[fid][ckey] = gckey
        if not gckey in self.gckey2ckey:
            self.gckey2ckey[gckey] = {}
        self.gckey2ckey[gckey][fid] = ckey

    def add_vid2gvid(self,fid,vid,gvid):
        if not fid in self.vid2gvid:
            self.vid2gvid[fid] = {}
        self.vid2gvid[fid][vid] = gvid
        if not gvid in self.gvid2vid:
            self.gvid2vid[gvid] = {}
        self.gvid2vid[gvid][fid] = vid

    def add_file(self,cfile):
        path = cfile.capp.path
        fname = cfile.name
        fid = cfile.index
        xxreffile = UF.get_cxreffile_xnode(path,fname)
        if not xxreffile is None:
            self._add_xrefs(xxreffile,fid)
        self._add_globaldefinitions(cfile.declarations,fid)
        self.fidvidmax[fid] = fidvidmax_initial_value

    def save_xrefs(self,path,fname,fid):
        xrefroot = UX.get_xml_header('global-xrefs','global-xrefs')
        xrefsnode = ET.Element('global-xrefs')
        xrefroot.append(xrefsnode)
        cxrefsnode = ET.Element('compinfo-xrefs')
        vxrefsnode = ET.Element('varinfo-xrefs')
        xrefsnode.extend([ cxrefsnode, vxrefsnode ])

        if fid in self.ckey2gckey:
            for ckey in sorted(self.ckey2gckey[fid]):
                xref = ET.Element('cxref')
                xref.set('ckey',str(ckey))
                xref.set('gckey',str(self.ckey2gckey[fid][ckey]))
                cxrefsnode.append(xref)
        
        if fid in self.vid2gvid:
            for vid in sorted(self.vid2gvid[fid]):
                xref = ET.Element('vxref')
                xref.set('vid',str(vid))
                xref.set('gvid',str(self.vid2gvid[fid][vid]))
                vxrefsnode.append(xref)

        xreffilename = UF.get_cxreffile_filename(path,fname)
        xreffile = open(xreffilename,'w')
        xreffile.write(UX.doc_to_pretty(ET.ElementTree(xrefroot)))
                

    def _add_xrefs(self,xnode,fid):
        if not fid in self.ckey2gckey:
            self.ckey2gckey[fid] = {}
            
        xcompinfoxrefs = xnode.find('compinfo-xrefs')
        for cxref in xcompinfoxrefs.findall('cxref'):
            ckey = int(cxref.get('ckey'))
            gckey = int(cxref.get('gckey'))
            self.ckey2gckey[fid][ckey] = gckey
            if not gckey in self.gckey2ckey:
                self.gckey2ckey[gckey] = {}
            self.gckey2ckey[gckey][fid] = ckey

        if not fid in self.vid2gvid:
            self.vid2gvid[fid] = {}

        xvarinfoxrefs = xnode.find('varinfo-xrefs')
        for vxref in xvarinfoxrefs.findall('vxref'):
            vid = int(vxref.get('vid'))
            gvid = int(vxref.get('gvid'))
            self.vid2gvid[fid][vid] = gvid
            if not gvid in self.gvid2vid:
                self.gvid2vid[gvid] = {}
            self.gvid2vid[gvid][fid] = vid        


    def _add_globaldefinitions(self,declarations,fid):
        for gvar in declarations.get_globalvar_definitions():
            gvid = self.get_gvid(fid,gvar.varinfo.get_vid())
            if not gvid is None:
                self.gviddefs[gvid] = fid

        for gfun in declarations.get_global_functions():
            gvid = self.get_gvid(fid,gfun.varinfo.get_vid())
            if not gvid is None:
                logging.info('Set function ' + gfun.varinfo.vname + ' (' + str(gvid) + ')'
                                 + ' to file ' + str(fid))
                self.gviddefs[gvid] = fid
