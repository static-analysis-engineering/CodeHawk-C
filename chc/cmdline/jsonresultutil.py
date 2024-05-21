# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2024  Aarno Labs LLC
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

import datetime

from typing import (
    Any, Dict, List, Mapping, Optional, Sequence, Tuple, TYPE_CHECKING)

from chc.jsoninterface.JSONResult import JSONResult
from chc.jsoninterface.JSONSchema import JSONSchema

import chc.util.fileutil as UF
from chc.util.loggingutil import chklogger

if TYPE_CHECKING:
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.proof.CFunctionPO import CFunctionPO
    from chc.source.CSrcFile import CSrcFile


def jsondate() -> Tuple[str, str]:
    currenttime = datetime.datetime.now()
    cdate = currenttime.strftime("%Y-%m-%d")
    ctime = currenttime.strftime("%H:%M:%S")
    return (cdate, ctime)


def jsonfail(msg: Optional[str]) -> Dict[str, Any]:
    jresult: Dict[str, Any] = {}
    jresult["meta"] = jmeta = {}
    jmeta["status"] = "fail"
    jmeta["reason"] = str(msg)
    (jmeta["date"], jmeta["time"]) = jsondate()
    return jresult


def jsonok(schemaname: str, content: Dict[str, Any]) -> Dict[str, Any]:
    jresult: Dict[str, Any] = {}
    jresult["meta"] = jmeta = {}
    jmeta["status"] = "ok"
    (jmeta["date"], jmeta["time"]) = jsondate()
    jmeta["schema"] = schemaname
    jresult["content"] = content
    return jresult


def jsonfiledata(cfile: "CFile") -> Dict[str, str]:
    result: Dict[str, str] = {}
    result["filename"] = cfile.cfilename + ".c"
    return result


def jsonfunctiondata(cfunction: "CFunction") -> Dict[str, str]:
    result: Dict[str, str] = {}
    result["name"] = cfunction.name
    return result


def csource_to_json_result(csrc: "CSrcFile") -> JSONResult:
    content: Dict[str, Any] = {}
    srclines: List[Tuple[int, str]] = []
    for (i, line) in sorted(csrc.lines.items()):
        srclines.append((i, line))
    content["sourcelines"] = srclines
    return JSONResult("sourcelines", content, "ok")


def ppo_to_json_result(po: "CFunctionPO") -> JSONResult:
    content: Dict[str, Any] = {}
    content["index"] = po.po_index
    content["line"] = po.line
    content["status"] = po.status
    content["predicate"] = str(po.predicate)
    if po.is_closed:
        content["expl"] = po.explanation
    else:
        if po.has_diagnostic():
            content["argdiagnostics"] = po.diagnostic.argument_msgs
            content["keydiagnostics"] = po.diagnostic.keyword_msgs
            content["msgdiagnostics"] = po.diagnostic.msgs
    return JSONResult("ppo", content, "ok")


def fn_proofobligations_to_json_result(fn: "CFunction") -> JSONResult:
    content: Dict[str, Any] = {}
    ppos: Sequence["CFunctionPO"] = fn.get_ppos()
    jppos: List[Dict[str, Any]] = []
    for ppo in sorted(ppos, key=lambda po: po.line):
        pporesult = ppo_to_json_result(ppo)
        jppos.append(pporesult.content)
    content["ppos"] = jppos
    return JSONResult("cfunppos", content, "ok")


def file_proofobligations_to_json_result(cfile: "CFile") -> JSONResult:
    content: Dict[str, Any] = {}
    content["filedata"] = jsonfiledata(cfile)
    content["filesource"] = csource_to_json_result(cfile.sourcefile).content
    fnsdata: List[Dict[str, Any]] = []
    for fn in cfile.get_functions():
        fndata: Dict[str, Any] = {}
        fndata["functiondata"] = jsonfunctiondata(fn)
        fndata["ppos"] = fn_proofobligations_to_json_result(fn).content
        fnsdata.append(fndata)
    content["functions"] = fnsdata
    return JSONResult("fileproofobligations", content, "ok")
