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

import xml.etree.ElementTree as ET

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger
import chc.util.xmlutil as UX

if TYPE_CHECKING:
    from chc.app.CFileDeclarations import CFileDeclarations
    from chc.app.CFile import CFile

fidvidmax_initial_value = 1000000

"""
TODO:
  - save gxrefs file if new vid's were added to a file
"""


class IndexManager:

    def __init__(self, issinglefile: bool) -> None:
        self.issinglefile = issinglefile  # application consists of a single file

        self.vid2gvid: Dict[int, Dict[int, int]] = {}  # fid -> vid -> gvid
        self.gvid2vid: Dict[int, Dict[int, int]] = {}  # gvid -> fid -> vid

        self.fidvidmax: Dict[int, int] = {}  # fid -> maximum vid in file with index fid

        self.ckey2gckey: Dict[int, Dict[int, int]] = {}  # fid -> ckey -> gckey
        self.gckey2ckey: Dict[int, Dict[int, int]] = {}  # gckey -> fid -> ckey

        # gvid -> fid  (file in which gvid is defined)
        self.gviddefs: Dict[int, int] = {}

    def get_vid_gvid_subst(self, fid: int) -> Dict[int, int]:
        return self.vid2gvid[fid]

    def get_fid_gvid_subset(self, fileindex: int) -> Dict[int, int]:
        result: Dict[int, int] = {}
        for gvid in self.gvid2vid:
            for fid in self.gvid2vid[gvid]:
                if fid == fileindex:
                    result[gvid] = self.gvid2vid[gvid][fid]
        return result

    """return the fid of the file in which this vid is defined, with the
    local vid.
    """

    def resolve_vid(self, fid: int, vid: int) -> Optional[Tuple[int, int]]:
        if self.issinglefile:
            return (fid, vid)
        msg = "indexmgr:resolve-vid(" + str(fid) + "," + str(vid) + "): "
        if fid in self.vid2gvid:
            if vid in self.vid2gvid[fid]:
                gvid = self.vid2gvid[fid][vid]
                if gvid in self.gviddefs:
                    tgtfid = self.gviddefs[gvid]
                    if gvid in self.gvid2vid:
                        if tgtfid in self.gvid2vid[gvid]:
                            return (tgtfid, self.gvid2vid[gvid][tgtfid])
                        chklogger.logger.debug(
                            "target fid: %s not found in gvid2vid[%s] for "
                            + "(%s, %s)",
                            str(tgtfid),
                            str(gvid),
                            str(fid),
                            str(vid))
                        return None
                    chklogger.logger.debug(
                        "global vid %s not found in gvid2vid for (%s, %s)",
                        str(gvid), str(fid), str(vid))
                    return None
                chklogger.logger.debug(
                    "global vid %s not found gviddefs for (%s, %s)",
                    str(gvid), str(fid), str(vid))
                return None
            chklogger.logger.debug(
                "local vid %s not found in vid2gvid[%s] for (%s, %s)",
                str(vid), str(fid), str(fid), str(vid))
            return None
        chklogger.logger.debug("file id %s not found in vid2gvid", str(fid))
        return None

    """return a list of (fid,vid) pairs that refer to the same global variable."""

    def get_gvid_references(self, gvid: int) -> List[Tuple[int, int]]:
        result: List[Tuple[int, int]] = []
        for fid in self.gvid2vid[gvid]:
            result.append((fid, self.gvid2vid[gvid][fid]))
        return result

    def has_gvid_reference(self, gvid: int, fid: int) -> bool:
        if gvid in self.gvid2vid:
            return fid in self.gvid2vid[gvid]
        else:
            return False

    def get_gvid_reference(self, gvid: int, fid: int) -> Optional[int]:
        if gvid in self.gvid2vid:
            if fid in self.gvid2vid[gvid]:
                return self.gvid2vid[gvid][fid]
        return None

    """return a list of (fid,vid) pairs that refer to the same variable."""

    def get_vid_references(self, srcfid: int, srcvid: int) -> List[Tuple[int, int]]:
        result: List[Tuple[int, int]] = []
        if self.issinglefile:
            return result
        if srcfid in self.vid2gvid:
            if srcvid in self.vid2gvid[srcfid]:
                gvid = self.vid2gvid[srcfid][srcvid]
                for fid in self.gvid2vid[gvid]:
                    if fid == srcfid:
                        continue
                    result.append((fid, self.gvid2vid[gvid][fid]))
        return result

    """return the vid in the file with index fidtgt for the variable vid in fidsrc.

    If the target file does not map the gvid then create a new vid in this file to
    map the gvid.
    """

    def convert_vid(self, fidsrc: int, vid: int, fidtgt: int) -> Optional[int]:
        if self.issinglefile:
            return vid
        gvid = self.get_gvid(fidsrc, vid)
        msg = (
            "indexmgr:convert-vid("
            + str(fidsrc)
            + ","
            + str(vid)
            + ","
            + str(fidtgt)
            + "): "
        )
        if gvid is not None:
            if gvid in self.gvid2vid:
                if fidtgt in self.gvid2vid[gvid]:
                    return self.gvid2vid[gvid][fidtgt]
                else:
                    chklogger.logger.warning(
                        "create new index for global variable %s for "
                        + "fidsrc: %s, vid: %s, fidtgt: %s",
                        str(gvid),
                        str(fidsrc),
                        str(vid),
                        str(fidtgt))
                    return None
                """
                    self.gvid2vid[gvid][fidtgt] = self.fidvidmax[fidtgt]
                    self.fidvidmax[fidtgt] += 1
                    return self.gvid2vid[gvid][fidtgt]
                """
        return None

    """return the gvid of the vid in the file with index fid."""

    def get_gvid(self, fid: int, vid: int) -> Optional[int]:
        if self.issinglefile:
            return vid
        if fid in self.vid2gvid:
            if vid in self.vid2gvid[fid]:
                return self.vid2gvid[fid][vid]
        return None

    """return the vid of the gvid in the file with index fid."""

    def get_vid(self, fid: int, gvid: int) -> Optional[int]:
        if self.issinglefile:
            return gvid
        if gvid in self.gvid2vid:
            if fid in self.gvid2vid[gvid]:
                return self.gvid2vid[gvid][fid]
        return None

    def get_gckey(self, fid: int, ckey: int) -> Optional[int]:
        if self.issinglefile:
            return ckey
        if fid in self.ckey2gckey:
            if ckey in self.ckey2gckey[fid]:
                return self.ckey2gckey[fid][ckey]
        return None

    def convert_ckey(self, fidsrc: int, ckey: int, fidtgt: int) -> Optional[int]:
        if self.issinglefile:
            return ckey
        gckey = self.get_gckey(fidsrc, ckey)
        if gckey is not None:
            if gckey in self.gckey2ckey:
                if fidtgt in self.gckey2ckey[gckey]:
                    return self.gckey2ckey[gckey][fidtgt]
                else:
                    chklogger.logger.debug(
                        "target fid %s not found for global key %s",
                        str(fidtgt), str(gckey))
            else:
                chklogger.logger.debug(
                    "global key %s not found in converter", str(gckey))
        else:
            chklogger.logger.debug(
                "local key %s not found in source file %s",
                str(ckey), str(fidsrc))
        return None

    def add_ckey2gckey(self, fid: int, ckey: int, gckey: int) -> None:
        if fid not in self.ckey2gckey:
            self.ckey2gckey[fid] = {}
        self.ckey2gckey[fid][ckey] = gckey
        if gckey not in self.gckey2ckey:
            self.gckey2ckey[gckey] = {}
        self.gckey2ckey[gckey][fid] = ckey

    def add_vid2gvid(self, fid: int, vid: int, gvid: int) -> None:
        if fid not in self.vid2gvid:
            self.vid2gvid[fid] = {}
        self.vid2gvid[fid][vid] = gvid
        if gvid not in self.gvid2vid:
            self.gvid2vid[gvid] = {}
        self.gvid2vid[gvid][fid] = vid

    def add_file(self, cfile: "CFile") -> None:
        path = cfile.capp.path
        fname = cfile.name
        fid = cfile.index
        xxreffile = UF.get_cxreffile_xnode(path, fname)
        if xxreffile is not None:
            self._add_xrefs(xxreffile, fid)
        self._add_globaldefinitions(cfile.declarations, fid)
        self.fidvidmax[fid] = fidvidmax_initial_value

    def save_xrefs(self, path: str, fname: str, fid: int) -> None:
        xrefroot = UX.get_xml_header("global-xrefs", "global-xrefs")
        xrefsnode = ET.Element("global-xrefs")
        xrefroot.append(xrefsnode)
        cxrefsnode = ET.Element("compinfo-xrefs")
        vxrefsnode = ET.Element("varinfo-xrefs")
        xrefsnode.extend([cxrefsnode, vxrefsnode])

        if fid in self.ckey2gckey:
            for ckey in sorted(self.ckey2gckey[fid]):
                xref = ET.Element("cxref")
                xref.set("ckey", str(ckey))
                xref.set("gckey", str(self.ckey2gckey[fid][ckey]))
                cxrefsnode.append(xref)

        if fid in self.vid2gvid:
            for vid in sorted(self.vid2gvid[fid]):
                xref = ET.Element("vxref")
                xref.set("vid", str(vid))
                xref.set("gvid", str(self.vid2gvid[fid][vid]))
                vxrefsnode.append(xref)

        xreffilename = UF.get_cxreffile_filename(path, fname)
        xreffile = open(xreffilename, "w")
        xreffile.write(UX.doc_to_pretty(ET.ElementTree(xrefroot)))

    def _add_xrefs(self, xnode: ET.Element, fid: int) -> None:
        if fid not in self.ckey2gckey:
            self.ckey2gckey[fid] = {}

        xcompinfoxrefs = xnode.find("compinfo-xrefs")
        if xcompinfoxrefs is not None:
            for cxref in xcompinfoxrefs.findall("cxref"):
                xckey = cxref.get("ckey")
                if xckey is not None:
                    ckey = int(xckey)
                    xgckey = cxref.get("gckey")
                    if xgckey is not None:
                        gckey = int(xgckey)
                        self.ckey2gckey[fid][ckey] = gckey
                        self.gckey2ckey.setdefault(gckey, {})
                        # if gckey not in self.gckey2ckey:
                        #    self.gckey2ckey[gckey] = {}
                        self.gckey2ckey[gckey][fid] = ckey
                    else:
                        raise UF.CHCError(
                            "Compinfo xref without gckey attribute")
                else:
                    raise UF.CHCError("Compinfo xref without ckey attribute")

        if fid not in self.vid2gvid:
            self.vid2gvid[fid] = {}

        xvarinfoxrefs = xnode.find("varinfo-xrefs")
        if xvarinfoxrefs is not None:
            for vxref in xvarinfoxrefs.findall("vxref"):
                xvid = vxref.get("vid")
                if xvid is not None:
                    vid = int(xvid)
                    xgvid = vxref.get("gvid")
                    if xgvid is not None:
                        gvid = int(xgvid)
                        self.vid2gvid[fid][vid] = gvid
                        self.gvid2vid.setdefault(gvid, {})
                        # if gvid not in self.gvid2vid:
                        # self.gvid2vid[gvid] = {}
                        self.gvid2vid[gvid][fid] = vid
                    else:
                        raise UF.CHCError(
                            "Varinfo xref without gvid attribute")
                else:
                    raise UF.CHCError("Varinfo xref without vid attribute")

    def _add_globaldefinitions(
            self, declarations: "CFileDeclarations", fid: int) -> None:
        for gvar in declarations.get_globalvar_definitions():
            gvid = self.get_gvid(fid, gvar.varinfo.vid)
            if gvid is not None:
                self.gviddefs[gvid] = fid

        for gfun in declarations.get_global_functions():
            gvid = self.get_gvid(fid, gfun.varinfo.vid)
            if gvid is not None:
                chklogger.logger.info(
                    "set function %s (%s) to file %s",
                    gfun.varinfo.vname, str(gvid), str(fid))
                self.gviddefs[gvid] = fid
