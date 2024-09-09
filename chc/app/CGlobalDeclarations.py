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
"""Declarations of global entities across files."""

from dataclasses import dataclass

from typing import (
    Any, Callable, cast, Dict, List, Optional, Set, Tuple, TYPE_CHECKING)
import xml.etree.ElementTree as ET

import chc.util.fileutil as UF
import chc.util.IndexedTable as IT
import chc.app.CInitInfo as CI

from chc.app.CCompInfo import CCompInfo
from chc.app.CDeclarations import CDeclarations
from chc.app.CFieldInfo import CFieldInfo
from chc.app.CGlobalDictionary import CGlobalDictionary
from chc.app.CInitInfo import CInitInfo, COffsetInitInfo
from chc.app.IndexManager import VarReference, CKeyReference
from chc.app.CVarInfo import CVarInfo

from chc.util.IndexedTable import IndexedTable, IndexedTableValue
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.api.CGlobalContract import CGlobalContract
    from chc.app.CApplication import CApplication
    from chc.app.CFile import CFile
    from chc.app.CInitInfo import CSingleInitInfo, CCompoundInitInfo


class ConjectureFailure(Exception):

    def __init__(self, ckey: int, gckey: int) -> None:
        self.ckey = ckey
        self.gckey = gckey

    def __str__(self) -> str:
        return (
            f"Compinfo {self.ckey} is not compatible with global compinfo {self.gckey}")


class CGlobalDeclarations(CDeclarations):
    """Dictionary that indexes global vars and struct definitions from all files.

    The indexing of struct definitions may involve backtracking in the case of
    structs that contain pointer references to itself, or circular references
    that involve multiple structs.

    The backtracking is performed per file. When a struct (represented by a
    compinfo) is indexed its status is set to pending. When a request for a
    TComp ckey conversion for the same compinfo is encountered a new global
    key is conjectured as follows:

    - gckey that has already been reserved for this ckey
    - gckey that has already been conjectured for this ckey
    - gckey for an existing global compinfo that has the same fields, if
      (ckey,gckey) is not in the list of incompatibles
    - reserve a new key from the indexed table and set its status to reserved,
      and remove its pending status

    When the compinfo for ckey has been constructed the state is updated as
    follows:

    - if ckey had a reserved key the reserved key is now committed
    - if ckey had a conjectured key and the conjectured key is the same as the
      returned gckey, nothing needs to be done
    - if ckey had a conjectured key but the conjectured key is not the same as the
      returned gckey, add (ckey,gckey) to the list of incompatibles, reset
      the indexed table to the file checkpoint, and re-index all compinfos
      in the file.

    """

    def __init__(self, capp: "CApplication", xnode: Optional[ET.Element]) -> None:
        self._capp = capp

        # Global definitions and declarations dictionary
        self.fieldinfo_table = IndexedTable("fieldinfo-table")
        self.compinfo_table = IndexedTable("compinfo-table")
        self.varinfo_table = IT.IndexedTable("varinfo-table")
        self.initinfo_table = IT.IndexedTable("initinfo-table")
        self.offset_init_table = IT.IndexedTable("offset-init-table")
        self.tables = [
            self.fieldinfo_table,
            self.compinfo_table,
            self.initinfo_table,
            self.varinfo_table,
            self.offset_init_table
        ]

        # Collect names for compinfo equivalence classes
        self.compinfo_names: Dict[int, Set[str]] = {}  # gckey -> string set

        # Collect storage classes for varinfo equivalence classes
        self._varinfo_storage_classes: Dict[int, Set[str]] = {}  # gvid -> string

        # Support data structures for linker
        self._ckey2gckey: Dict[int, Dict[int, int]] = {}  # fid -> ckey -> gckey
        self._vid2gvid: Dict[int, Dict[int, int]] = {}  # fid -> vid -> gvid

        # string of joined fields -> gckey list
        self._fieldstrings: Dict[str, List[int]] = {}
        self.pending: List[int] = []
        self.conjectured: Dict[int, int] = {}  # ckey -> gckey
        self.reserved: Dict[int, int] = {}  # ckey -> gckey
        self.incompatibles: Dict[int, Set[int]] = {}  # ckey -> gckey set

        # (fid,varinfo) list
        self.default_function_prototypes: List[Tuple[int, CVarInfo]] = []

        self._initialize(xnode)
        if self.compinfo_table.size() == 0:
            self.index_opaque_struct()

    @property
    def cfile(self) -> "CFile":
        raise UF.CHCError("No access to individual file via global dictionary")

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def globalcontract(self) -> "CGlobalContract":
        return self.capp.globalcontract

    @property
    def dictionary(self) -> "CGlobalDictionary":
        return self.capp.dictionary

    @property
    def varinfo_storage_classes(self) -> Dict[int, Set[str]]:
        return self._varinfo_storage_classes

    @property
    def fieldstrings(self) -> Dict[str, List[int]]:
        """Returns a map from a conjoined fieldstring to global struct keys

        fieldstrings -> gckey
        """
        return self._fieldstrings

    @property
    def ckey2gckey(self) -> Dict[int, Dict[int, int]]:
        """Returns the global compinfo key for a given file and compinfo key

        fid -> ckey -> gckey
        """

        return self._ckey2gckey

    def get_gckey(self, ckeyref: CKeyReference) -> Optional[int]:
        if ckeyref.fid is None:
            # this already is a global key
            return ckeyref.ckey

        if ckeyref.fid in self.ckey2gckey:
            if ckeyref.ckey in self.ckey2gckey[ckeyref.fid]:
                return self.ckey2gckey[ckeyref.fid][ckeyref.ckey]
        return None

    def register_gcompinfo(
            self, ckeyref: CKeyReference, gcompinfo: CCompInfo) -> None:
        if ckeyref.fid is None:
            chklogger.logger.warning(
                "register_gcompinfo is called with a global ckeyref: %s",
                gcompinfo.name)
            return

        gckey = gcompinfo.ckey
        fields = gcompinfo.field_strings
        self._fieldstrings.setdefault(fields, [])
        if gckey not in self.fieldstrings[fields]:
            self._fieldstrings[fields].append(gckey)
        self._ckey2gckey.setdefault(ckeyref.fid, {})
        self._ckey2gckey[ckeyref.fid][ckeyref.ckey] = gckey

    @property
    def vid2gvid(self) -> Dict[int, Dict[int, int]]:
        """Returns the global vid for a given file and varinfo vid.

        fid -> vid -> gvid.
        """

        return self._vid2gvid

    def get_gvid(self, varref: VarReference) -> Optional[int]:
        if varref.fid is None:
            chklogger.logger.warning(
                "get_gvid is called with a global vid; returning global vid")
            return varref.vid

        if varref.fid in self.vid2gvid:
            if varref.vid in self.vid2gvid[varref.fid]:
                return self.vid2gvid[varref.fid][varref.vid]
        return None

    def is_hidden_field(self, compname: str, fieldname: str) -> bool:
        return self.globalcontract.is_hidden_field(compname, fieldname)

    def is_hidden_struct(self, filename: str, compname: str) -> bool:
        return self.globalcontract.is_hidden_struct(filename, compname)

    # ---------------------- Retrieve items from definitions dictionary ------

    def get_fieldinfo(self, ix: int) -> CFieldInfo:
        itv = self.fieldinfo_table.retrieve(ix)
        return CFieldInfo(self, itv)

    def get_varinfo(self, ix: int) -> CVarInfo:
        itv = self.varinfo_table.retrieve(ix)
        return CVarInfo(self, itv)

    def get_compinfo(self, ix: int) -> CCompInfo:
        itv = self.compinfo_table.retrieve(ix)
        return CCompInfo(self, itv)

    def get_initinfo(self, ix: int) -> CInitInfo:
        itv = self.initinfo_table.retrieve(ix)
        return CInitInfo(self, itv)

    def get_offset_init(self, ix: int) -> COffsetInitInfo:
        itv = self.offset_init_table.retrieve(ix)
        return COffsetInitInfo(self, itv)

    # --------------------- Retrieve derived items ---------------------------

    def varinfo_values(self) -> List[CVarInfo]:
        return [CVarInfo(self, itv) for itv in self.varinfo_table.values()]

    def has_varinfo_by_name(self, name: str) -> bool:
        return any([v.vname == name for v in self.varinfo_values()])

    def get_varinfo_by_name(self, name: str) -> CVarInfo:
        for v in self.varinfo_values():
            if v.vname == name:
                return v
        raise Exception("No varinfo with name \"" + name + "\"")

    def get_compinfo_by_ckey(self, ckey: int) -> CCompInfo:
        raise Exception("get_compinfo_by_ckey: not yet implemented")

    def get_structname(self, ckey: int) -> str:
        if ckey in self.compinfo_names:
            return list(self.compinfo_names[ckey])[0]
        chklogger.logger.warning("Compinfo name for %s not found", str(ckey))
        return "struct " + str(ckey)

    def get_gcompinfo(self, ckeyref: CKeyReference) -> Optional[CCompInfo]:
        """Returns the global compinfo associated with a file compinfo."""

        if ckeyref.fid is None:
            chklogger.logger.warning(
                "get_gcompinfo is called with a global ckeyref")
            return None

        gckey = self.get_gckey(ckeyref)
        if gckey is not None:
            return self.get_compinfo(gckey)
        return None

    def convert_ckey(self, ckeyref: CKeyReference) -> Optional[int]:
        if ckeyref.fid is None:
            # this already is a global key
            return ckeyref.ckey

        return self.get_gckey(ckeyref)

    def list_compinfos(self) -> str:
        lines: List[str] = []
        for gckey in self.compinfo_names:
            names = ",".join(list(self.compinfo_names[gckey]))
            lines.append(names)
        return "\n".join(sorted(lines))

    def show_compinfos(self, name: str) -> List[Tuple[int, CCompInfo]]:
        result: List[Tuple[int, CCompInfo]] = []
        gckeys = [
            x for x in self.compinfo_names.keys()
            if name in self.compinfo_names[x]]
        for k in gckeys:
            result.append((k, self.get_compinfo(k)))
        return result

    # -------------------- Linker support services ---------------------------

    def reset_conjectures(self) -> None:
        self.pending = []
        self.conjectured = {}
        self.reserved = {}

    def cleanup(self, checkpoint: int, ckey: int, gckey: int) -> None:
        if ckey not in self.incompatibles:
            self.incompatibles[ckey] = set([])
        self.incompatibles[ckey].add(gckey)
        self.reset_conjectures()
        keystoberemoved: List[int] = []
        for k in self.compinfo_names.keys():
            if k >= checkpoint:
                keystoberemoved.append(k)
        for k in keystoberemoved:
            self.compinfo_names.pop(k)
        fskeystoberemoved: List[Tuple[str, int]] = []
        for fs in self.fieldstrings.keys():
            for gckey in self.fieldstrings[fs]:
                if gckey >= checkpoint:
                    fskeystoberemoved.append((fs, gckey))
        for (fs, gckey) in fskeystoberemoved:
            self.fieldstrings[fs].remove(gckey)

    def get_state(self) -> str:
        lines = []
        lines.append("Pending    : " + str(self.pending))
        lines.append("Conjectured: " + str(self.conjectured))
        lines.append("Reserved   : " + str(self.reserved))
        return "\n".join(lines)

    def get_field_strings_conjecture(
            self, cname: str, fields: str, ckey: int) -> Optional[int]:
        if fields in self.fieldstrings:
            for gckey in self.fieldstrings[fields]:
                conjecturedkey = gckey
                if (
                    ckey in self.incompatibles
                    and conjecturedkey in self.incompatibles[ckey]
                ):
                    pass
                else:
                    break
            else:
                return None
            return conjecturedkey
        return None

    def conjecture_key(self, fid: int, compinfo: CCompInfo) -> int:
        ckey = compinfo.ckey
        if ckey in self.reserved:
            return self.reserved[ckey]
        if ckey in self.conjectured:
            return self.conjectured[ckey]
        conjecturedkey = self.get_field_strings_conjecture(
            compinfo.name, compinfo.field_strings, ckey
        )
        if conjecturedkey is None:
            reservedkey = self.compinfo_table.reserve()
            self.reserved[ckey] = reservedkey
            self.pending.remove(ckey)
            return reservedkey
        else:
            self.conjectured[ckey] = conjecturedkey
            self.pending.remove(ckey)
            return conjecturedkey

    # ------------------- Indexing compinfos ---------------------------------

    def index_fieldinfo(self, fieldinfo: CFieldInfo, compinfoname: str) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CFieldInfo:
            itv = IndexedTableValue(index, tags, args)
            return CFieldInfo(self, itv)

        tags = [fieldinfo.fname]
        if self.is_hidden_field(compinfoname, fieldinfo.fname):
            gftype = self.index_opaque_struct_pointer()
        else:
            gftype = self.dictionary.index_typ(
                fieldinfo.ftype.expand().strip_attributes())
        args = [-1, gftype, fieldinfo.bitfield, -1, -1]

        return self.fieldinfo_table.add_tags_args(tags, args, f)

    # only compinfo's from files should be indexed
    def index_compinfo_key(self, compinfo: CCompInfo, fid: int) -> int:
        """Returns the global ckey for the given compinfo and file id."""

        chklogger.logger.info(
            "Index compinfo key for %s and fid %d", compinfo.name, fid)
        ckey = compinfo.ckey
        ckeyref = CKeyReference(fid, ckey)
        gckey = self.get_gckey(ckeyref)
        if gckey is not None:
            return gckey

        if ckey in self.conjectured:
            chklogger.logger.info(
                "Compinfo %s (fid.ckey: %s.%s) conjectured key: %s",
                compinfo.name,
                str(fid),
                str(ckey),
                str(self.conjectured[ckey]))
            return self.conjectured[ckey]

        if ckey in self.reserved:
            chklogger.logger.info(
                "Compinfo %s (fid.ckey: %s.%s) reserved key: %s",
                compinfo.name,
                str(fid),
                str(ckey),
                str(self.reserved[ckey]))
            return self.reserved[ckey]

        if ckey in self.pending:
            pendingkey = self.conjecture_key(fid, compinfo)
            chklogger.logger.info(
                "Compinfo %s (fid.ckey: %s.%s) new pending key: %s",
                compinfo.name,
                str(fid),
                str(ckey),
                str(pendingkey))
            return pendingkey

        # this compinfo is new
        return self.make_global_compinfo(fid, compinfo).ckey

    def index_opaque_struct(self) -> int:
        tags = ["?"]
        args = [-1, 1, -1]

        def f(index: int, tags: List[str], args: List[int]) -> CCompInfo:
            self.compinfo_names.setdefault(index, set([]))
            self.compinfo_names[index].add("opaque-struct")
            itv = IT.IndexedTableValue(index, tags, args)
            return CCompInfo(self, itv)

        return self.compinfo_table.add_tags_args(tags, args, f)

    def get_opaque_struct(self) -> CCompInfo:
        itv = self.compinfo_table.retrieve(1)
        return CCompInfo(self, itv)

    def index_opaque_struct_pointer(self) -> int:
        tags = ["tcomp"]
        args = [1]
        comptypix = self.dictionary.mk_typ_index(tags, args)
        tags = ["tptr"]
        args = [comptypix]
        return self.dictionary.mk_typ_index(tags, args)

    def make_global_compinfo(self, fid: int, compinfo: CCompInfo) -> CCompInfo:
        chklogger.logger.info(
            "Indexing compinfo %s for fid: %d", compinfo.name, fid)
        filename = self.capp.get_file_by_index(fid).name
        ckey = compinfo.ckey
        cname = compinfo.name
        if self.is_hidden_struct(filename, cname):
            chklogger.logger.info("Hide struct %s in file %", cname, filename)
            return self.get_opaque_struct()

        keyref = CKeyReference(fid, ckey)
        gcompinfo = self.get_gcompinfo(keyref)
        if gcompinfo is not None:
            return gcompinfo

        chklogger.logger.info("Make compinfo pending: %s", compinfo.name)
        self.pending.append(compinfo.ckey)
        tags = ["?"]    # we don't have a name yet
        fieldixs = [self.index_fieldinfo(f, cname) for f in compinfo.fields]

        # create a key with args: ckey = -1; is_struct; iattributes
        args = [-1, 1 if compinfo.is_struct else 0, -1] + fieldixs
        key = (",".join(tags), ",".join([str(x) for x in args]))

        if ckey in self.reserved:
            gckey = self.reserved[ckey]
            itv = IT.IndexedTableValue(gckey, tags, args)
            gcompinfo = CCompInfo(self, itv)
            self.compinfo_table.commit_reserved(gckey, key, gcompinfo)
            self.reserved.pop(ckey)
            self.compinfo_names.setdefault(gckey, set([]))
            self.compinfo_names[gckey].add(compinfo.name)
            self.register_gcompinfo(keyref, gcompinfo)
            return gcompinfo

        # use tags and args to obtain an index from the comp-info table

        def f(index: int, tags: List[str], args: List[int]) -> CCompInfo:
            self.compinfo_names.setdefault(index, set([]))
            self.compinfo_names[index].add(compinfo.name)
            itv = IT.IndexedTableValue(index, tags, args)
            return CCompInfo(self, itv)

        compinfoindex = self.compinfo_table.add_tags_args(tags, args, f)

        # check if this new index corresponds to an earlier conjectured key
        # if so return the global compinfo, otherwise fail and backtrack

        gcompinfo = self.get_compinfo(compinfoindex)
        if ckey in self.conjectured:
            conjecturedkey = self.conjectured[ckey]
            gckey = gcompinfo.ckey
            if gckey == conjecturedkey:
                self.ckey2gckey[fid][ckey] = gcompinfo.ckey
                self.conjectured.pop(ckey)
                return gcompinfo
            else:
                chklogger.logger.info(
                    "Conjecture failure for %s (fid:%s, ckey:%s, gckey:%s, "
                    + "conjectured key: %s",
                    compinfo.name,
                    str(fid),
                    str(ckey),
                    str(gckey),
                    str(conjecturedkey))
                raise ConjectureFailure(ckey, conjecturedkey)

        else:
            # connect the global compinfo to the file compinfo and clean up
            keyref = CKeyReference(fid, ckey)
            self.register_gcompinfo(keyref, gcompinfo)
            self.pending.remove(compinfo.ckey)
            return gcompinfo

    def index_file_compinfos(self, fid: int, compinfos: List[CCompInfo]) -> None:
        """Indexes and connects the compinfos from the individual c files."""

        if len(compinfos) > 0:
            chklogger.logger.info("Index %d compinfos", len(compinfos))
            while 1:
                self.compinfo_table.set_checkpoint()
                self._ckey2gckey[fid] = {}
                try:
                    for c in compinfos:
                        chklogger.logger.info(
                            "Index compinfo (fid: %d): %s", fid, c.name)
                        self.make_global_compinfo(fid, c)
                except ConjectureFailure as e:
                    checkpoint = self.compinfo_table.reset_to_checkpoint()
                    self.cleanup(checkpoint, e.ckey, e.gckey)
                else:
                    self.compinfo_table.remove_checkpoint()
                    self.incompatibles = {}
                    break

    # -------------------- Indexing varinfos ---------------------------------

    def mk_single_init_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CI.CInitInfo:
            itv = IndexedTableValue(index, tags, args)
            return CI.CSingleInitInfo(self, itv)

        return self.initinfo_table.add_tags_args(tags, args, f)

    def mk_compound_init_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CI.CInitInfo:
            itv = IndexedTableValue(index, tags, args)
            return CI.CCompoundInitInfo(self, itv)

        return self.initinfo_table.add_tags_args(tags, args, f)

    def mk_offset_init_index(self, tags: List[str], args: List[int]) -> int:

        def f(index: int, tags: List[str], args: List[int]) -> CI.COffsetInitInfo:
            itv = IndexedTableValue(index, tags, args)
            return CI.COffsetInitInfo(self, itv)

        return self.offset_init_table.add_tags_args(tags, args, f)

    def index_init(self, init: CInitInfo, fid: int = -1) -> int:

        args: List[int]

        if init.is_single:
            init = cast("CSingleInitInfo", init)
            args = [self.dictionary.index_exp(init.exp, fid=fid)]
            return self.mk_single_init_index(init.tags, args)

        if init.is_compound:
            init = cast("CCompoundInitInfo", init)
            gtype = self.dictionary.index_typ(init.typ)
            oinits: List[int] = [
                self.index_offset_init(x, fid=fid)
                for x in init.offset_initializers]
            args = [gtype] + oinits
            return self.mk_compound_init_index(init.tags, args)

        else:
            raise Exception("InitInfo not recognized")

    def index_offset_init(self, oinit: COffsetInitInfo, fid: int = -1) -> int:
        args: List[int] = [
            self.dictionary.index_offset(oinit.offset, fid=fid),
            self.index_init(oinit.initializer, fid=fid)]
        return self.mk_offset_init_index(oinit.tags, args)

    def index_varinfo_vid(self, varref: VarReference) -> Optional[int]:
        if varref.fid is None:
            # this already is a global vid
            return varref.vid

        return self.get_gvid(varref)

    def make_global_varinfo(self, fid: int, varinfo: CVarInfo) -> None:
        """Returns the global varinfo that corresponds to a file varinfo."""

        if varinfo.vtype.is_default_function_prototype:
            # a function declaration without arguments
            self.default_function_prototypes.append((fid, varinfo))
            return

        vid = varinfo.vid
        if varinfo.vstorage == "s":
            # create a file-specific name for static variables
            vname = varinfo.vname + "__file__" + str(fid) + "__"
        else:
            vname = varinfo.vname
        vtype = varinfo.vtype.expand().strip_attributes()
        vtypeix = self.dictionary.index_typ(vtype)
        vtype = self.dictionary.get_typ(vtypeix)
        if varinfo.has_initializer():
            vinit = varinfo.initializer
            try:
                gvinit = [self.index_init(vinit, fid=fid)]
            except UF.CHError as e:
                chklogger.logger.warning(
                    ("Global variable initializer for %s "
                     + "(vid: %d, line: %s, fid: %d) "
                     + " could not be indexed: %s"),
                    varinfo.vname,
                    varinfo.vid,
                    (varinfo.vdecl.line if varinfo.vdecl is not None else -1),
                    fid,
                    str(e))
                gvinit = []
        else:
            gvinit = []
        tags = [vname]
        vargs = varinfo.args
        vaddrof = 1 if vtype.is_function else vargs[6]

        args = [
            -1,          # vid: use the CVarInfo index as the gvid
            vtypeix,     # vtype index, as indexed in the global dictionary
            -1,          # vattr index: drop the attributes
            vargs[3],    # vglob: same as file varinfo
            vargs[4],    # vinline: same as file varinfo
            -1,          # vdecl: location is not kept at the global level
            vaddrof,     # true for functions, otherwise same as file varinfo
            vargs[7]] + gvinit  # global initializer as converted, or absent

        def f(index: int, tags: List[str], args: List[int]) -> CVarInfo:
            itv = IndexedTableValue(index, tags, args)
            return CVarInfo(self, itv)

        gvarinfoindex = self.varinfo_table.add_tags_args(tags, args, f)
        gvarinfo = self.get_varinfo(gvarinfoindex)
        gvid = gvarinfo.vid
        if gvid not in self.varinfo_storage_classes:
            self._varinfo_storage_classes[gvid] = set([""])
        vstorageclass = varinfo.tags[1]
        if vstorageclass not in self.varinfo_storage_classes[gvid]:
            self._varinfo_storage_classes[gvid].add(vstorageclass)
        self.vid2gvid[fid][vid] = gvarinfo.vid
        chklogger.logger.debug(
            "Fid: %s, vid:%s, gvid:%s: %s",
            str(fid),
            str(vid),
            str(gvarinfo.vid),
            gvarinfo.vname)

    def index_file_varinfos(self, fid: int, varinfos: List[CVarInfo]) -> None:
        chklogger.logger.debug(
            "Index %d file varinfos for fid: %d (%s)",
            len(varinfos), fid,
            ", ".join(v.vname
                      + "("
                      + str(v.vid)
                      + ", line: "
                      + str(v.line if v.vdecl is not None else "?")
                      + ")" for v in varinfos))
        if len(varinfos) > 0:
            self.vid2gvid[fid] = {}
            for v in varinfos:
                self.make_global_varinfo(fid, v)

    def resolve_default_function_prototypes(self) -> None:
        chklogger.logger.info(
            "Resolving %d function prototypes",
            len(self.default_function_prototypes))

        for (fid, varinfo) in self.default_function_prototypes:

            def f(key: Tuple[str, str]) -> bool:
                return key[0].startswith(varinfo.vname)

            itvcandidates = self.varinfo_table.retrieve_by_key(f)
            candidates = [
                (itv[0], CVarInfo(self, itv[1])) for itv in itvcandidates]
            if len(candidates) == 1:
                self.vid2gvid[fid][varinfo.vid] = candidates[0][1].vid
                chklogger.logger.info(
                    "Resolved prototype for %s", varinfo.vname)
            else:
                pcandidates = ",".join([c[1].vname for c in candidates])
                for (_, c) in candidates:
                    if c.vname == varinfo.vname:
                        self.vid2gvid[fid][varinfo.vid] = c.vid
                        chklogger.logger.warning(
                            "Selected prototype %s for %s from multiple "
                            + "candidates: %s",
                            c.vname,
                            varinfo.vname,
                            pcandidates)
                        break
                else:
                    chklogger.logger.warning(
                        "Unable to resolve prototype for %s: %s: %s",
                        varinfo.vname,
                        str(len(candidates)),
                        pcandidates)

    # -------------------- Writing xml ---------------------------------------

    def write_xml(self, node: ET.Element) -> None:
        dnode = ET.Element("dictionary")
        self.dictionary.write_xml(dnode)
        node.append(dnode)

        def f(n: ET.Element, r: IndexedTableValue) -> None:
            r.write_xml(n)

        for t in self.tables:
            tnode = ET.Element(t.name)
            t.write_xml(tnode, f)
            node.append(tnode)

        cnode = ET.Element("compinfo-names")
        for ckey in sorted(self.compinfo_names):
            nnode = ET.Element("n")
            nnode.set("ckey", str(ckey))
            nnode.set("names", ",".join(sorted(self.compinfo_names[ckey])))
            cnode.append(nnode)
        node.append(cnode)

        vsnode = ET.Element("varinfo-storage-classes")
        for vid in sorted(self.varinfo_storage_classes):
            if "n" in self.varinfo_storage_classes[vid]:
                continue
            if len(self.varinfo_storage_classes[vid]) > 1:
                chklogger.logger.warning(
                    "Multiple storage classes for variable %d", vid)
                continue
            else:
                storageclass = list(self.varinfo_storage_classes[vid])[0]
            vnode = ET.Element("n")
            vnode.set("vid", str(vid))
            vnode.set("s", storageclass)
            vsnode.append(vnode)
        node.append(vsnode)

    def __str__(self) -> str:
        lines = []
        lines.append(str(self.dictionary))
        for t in self.tables:
            if t.size() > 0:
                lines.append(str(t))
        return "\n".join(lines)

    def _initialize(self, xnode: Optional[ET.Element]) -> None:
        # Initialize global declarations from globaldefinitions file if
        # available
        if xnode is None:
            return

        for t in self.tables:
            xtable = xnode.find(t.name)
            if xtable is None:
                raise Exception("Missing element `" + t.name + "`")
            t.reset()
            t.read_xml(xtable, "n")
        xml_compinfo_names = xnode.find("compinfo-names")
        if xml_compinfo_names is None:
            raise Exception("Missing element `compinfo-names`")
        xml_compinfo_names_n = xml_compinfo_names.find("n")
        if xml_compinfo_names_n is None:
            raise Exception("Missing element `n`")
        for n in xml_compinfo_names_n:
            xml_ckey = n.get("ckey")
            if xml_ckey is None:
                raise Exception("Missing element `ckey`")
            xml_names = n.get("names")
            if xml_names is None:
                raise Exception("Missing element `names`")
            self.compinfo_names[int(xml_ckey)] = set(xml_names.split(","))
        xml_varinfo_storage_classes = xnode.find("varinfo-storage-classes")
        if xml_varinfo_storage_classes is None:
            raise Exception("Missing element `varinfo-storage-classes`")
        for n in xml_varinfo_storage_classes:
            xml_vid = n.get("vid")
            if xml_vid is None:
                raise Exception("Missing element `vid`")
            xml_s = n.get("s")
            if xml_s is None:
                raise Exception("Missing element `s`")
            self.varinfo_storage_classes[int(xml_vid)] = set([xml_s])

    def _read_xml_varinfo_storage_classes(self, xnode: ET.Element) -> None:
        for n in xnode.findall("n"):
            xml_vid = n.get("vid")
            if xml_vid is None:
                raise Exception("Missing `vid` element")
            vid = int(xml_vid)
            self.varinfo_storage_classes[vid] = set([])
            xml_s = n.get("s")
            if xml_s is None:
                raise Exception("Missing `s` element")
            for c in xml_s:
                self.varinfo_storage_classes[vid].add(c)

    def _read_xml_compinfo_names(self, xnode: ET.Element) -> None:
        for n in xnode.findall("n"):
            xml_ckey = n.get("ckey")
            if xml_ckey is None:
                raise Exception("Missing `ckey` element")
            ckey = int(xml_ckey)
            xml_names = n.get("names")
            if xml_names is None:
                raise Exception("Missing `names` element")
            names = xml_names.split(",")
            self.compinfo_names[ckey] = set(names)
