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


class CGXrefs(object):

    def __init__(self,cfile,xnode):
        self.cfile = cfile
        self.xnode = xnode
        self.compkeys = {}      # local id -> global id
        self.varinfos = {}      # local id -> global id
        self._initialize()

    def getglobalkey(self,localkey):
        if self.xnode is None: return localkey
        if localkey in self.compkeys:
            return self.compkeys[localkey]
        return localkey

    def getglobalvid(self,localvid):
        if self.xnode is None: return localvid
        if localvid in self.varinfos:
            return self.varinfos[localvid]
        return localvid

    def _initialize(self):
        if self.xnode is None: return
        if len(self.compkeys) == 0 or len(self.varinfos) == 0:
            for c in self.xnode.find('compinfo-xrefs').findall('cxref'):
                self.compkeys[int(c.get('ckey'))] = int(c.get('gckey'))
            for v in self.xnode.find('varinfo-xrefs').findall('vxref'):
                self.varinfos[int(v.get('vid'))] = int(v.get('gvid'))
                
