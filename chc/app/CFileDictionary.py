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

from typing import TYPE_CHECKING

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT

import chc.app.CExp as CE
import chc.app.CLval as CV


from chc.app.CDictionary import CDictionary

if TYPE_CHECKING:
    from chc.app.CFileDeclarations import CFileDeclarations


class CKeyLookupError(Exception):
    def __init__(self, thisfid, tgtfid, ckey):
        self.thisfid = thisfid
        self.tgtfid = tgtfid
        self.ckey = ckey

    def __str__(self):
        return (
            "Unable to find corresponding compinfo key for "
            + str(self.ckey)
            + " from file "
            + str(self.tgtfid)
            + " in file "
            + str(self.thisfid)
        )


class CFileDictionary(CDictionary):
    def __init__(self, decls: "CFileDeclarations") -> None:
        CDictionary.__init__(self)
        self.decls = decls
        self.cfile = self.decls.cfile
        self.initialize()

    def initialize(self, force=False):
        xnode = UF.get_cfile_dictionary_xnode(self.cfile.capp.path, self.cfile.name)
        xnode = xnode.find("c-dictionary")
        CDictionary.initialize(self, xnode, force)

    def index_compinfo_key(self, compinfo, _):
        cfid = compinfo.decls.cfile.index
        fid = self.cfile.index
        ckey = compinfo.get_ckey()
        if not (cfid == fid):
            tgtkey = self.cfile.capp.indexmanager.convert_ckey(cfid, ckey, fid)
            if tgtkey is None:
                raise LookupError(
                    "Index_compinfo: Unable to find key for "
                    + str(ckey)
                    + " from file "
                    + str(cfid)
                    + " in file "
                    + str(fid)
                )
            else:
                return tgtkey
        else:
            return ckey

    def convert_ckey(self, ckey, fid=-1):
        if fid == -1:
            return ckey
        thisfid = self.cfile.index
        if not (thisfid == fid):
            tgtkey = self.cfile.capp.indexmanager.convert_ckey(fid, ckey, thisfid)
            if tgtkey is None:
                raise CKeyLookupError(thisfid, fid, ckey)
            else:
                return tgtkey
        else:
            return ckey

    def index_lhost_offset(self, lhost, offset):
        args = [lhost, offset]

        def f(index, key):
            return CV.CLval(self, index, [], args)

        return self.lval_table.add(IT.get_key([], args), f)

    def mk_lval_exp(self, lval):
        args = [lval]
        tags = ["lval"]

        def f(index, key):
            return CE.CExpLval(self, index, tags, args)

        return self.exp_table.add(IT.get_key(tags, args), f)

    def index_exp(self, e, subst={}, fid=-1):
        if e.is_lval():
            lhost = e.get_lval().get_lhost()
            if lhost.is_var() and lhost.get_vid() in subst:
                if e.get_lval().get_offset().has_offset():
                    if e.get_lval().get_offset().is_field():
                        paroffset = e.get_lval().get_offset()
                        newsubst = subst.copy()
                        newsubst.pop(lhost.get_vid())
                        iargexp = self.index_exp(subst[lhost.get_vid()], newsubst, fid)
                        argexp = self.get_exp(iargexp)
                        if argexp.is_lval():
                            arghost = argexp.get_lval().get_lhost()
                            if argexp.get_lval().get_offset().has_offset():
                                argoffset = argexp.get_lval().get_offset()
                                raise Exception(
                                    "Unexpected offset in substitution argument: "
                                    + str(argexp)
                                    + "; offset: "
                                    + str(argoffset)
                                )
                            iarghost = self.index_lhost(arghost, newsubst, fid)
                            iargoffset = self.index_offset(paroffset, fid)
                            iarglval = self.index_lhost_offset(iarghost, iargoffset)
                            return self.mk_lval_exp(iarglval)
                        else:
                            raise Exception(
                                "Unexpected type in substition argument (not an lval): "
                                + str(callarg)
                            )
                    else:
                        raise Exception(
                            "Unexpected offset in exp to be substituted: " + str(e)
                        )
                # avoid re-substitution for recursive functions
                newsubst = subst.copy()
                newsubst.pop(lhost.get_vid())
                return self.index_exp(subst[lhost.get_vid()], newsubst, fid)
        return CDictionary.index_exp(self, e, subst, fid)
