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
    from chc.api.ApiAssumption import ApiAssumption
    from chc.api.CFunctionApi import CFunctionApi
    from chc.api.GlobalAssumption import GlobalAssumption
    from chc.api.PostConditionRequest import PostConditionRequest
    from chc.app.CContext import CContextNode
    from chc.app.CContext import CfgContext
    from chc.app.CContext import ExpContext
    from chc.app.CContext import ProgramContext
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


def api_assumption_to_json_result(a: "ApiAssumption") -> JSONResult:
    content: Dict[str, Any] = {}
    content["index"] = a.id
    content["predicate"] = str(a.predicate)
    content["dependent-ppos"] = sorted(a.ppos)
    content["dependent-spos"] = sorted(a.spos)
    return JSONResult("api-assumption", content, "ok")


def postcondition_request_to_json_result(
        pcr: "PostConditionRequest") -> JSONResult:
    content: Dict[str, Any] = {}
    content["callee"] = pcr.callee.vname
    content["predicate"] = str(pcr.postcondition)
    content["dependent-ppos"] = sorted(pcr.get_open_ppos())
    content["dependent-spos"] = sorted(pcr.get_open_spos())
    return JSONResult("postcondition-request", content, "ok")


def global_assumption_request_to_json_result(g: "GlobalAssumption") -> JSONResult:
    content: Dict[str, Any] = {}
    content["index"] = g.id
    content["predicate"] = str(g.predicate)
    content["dependent-ppos"] = sorted(g.get_open_ppos())
    content["dependent-spos"] = sorted(g.get_open_spos())
    return JSONResult("global-assumption-request", content, "ok")


def fn_api_to_json_result(fapi: "CFunctionApi") -> JSONResult:
    content: Dict[str, Any] = {}
    aaresults: List[Dict[str, Any]] = []
    for assumption in fapi.api_assumptions.values():
        aaresult = api_assumption_to_json_result(assumption)
        aaresults.append(aaresult.content)
    postreqresults: List[Dict[str, Any]] = []
    for postrequest in fapi.postcondition_requests.values():
        pcresult = postcondition_request_to_json_result(postrequest)
        postreqresults.append(pcresult.content)
    globalrequests: List[Dict[str, Any]] = []
    for globalrequest in fapi.global_assumption_requests.values():
        gresult = global_assumption_request_to_json_result(globalrequest)
        globalrequests.append(gresult.content)
    content["api-assumptions"] = aaresults
    content["postcondition-requests"] = postreqresults
    content["global-requests"] = globalrequests
    return JSONResult("fnapi", content, "ok")


def contextnode_to_json_result(node: "CContextNode") -> JSONResult:
    content: Dict[str, Any] = {}
    if node.has_data_id():
        content["ctxtid"] = node.data_id
    content["name"] = node.name
    if node.has_additional_info():
        content["info"] = node.info
    return JSONResult("contextnode", content, "ok")


def expcontext_to_json_result(ectxt: "ExpContext") -> JSONResult:
    content: Dict[str, Any] = {}
    content["nodes"] = nodes = []
    for n in ectxt.nodes:
        cnode = contextnode_to_json_result(n)
        if not cnode.is_ok:
            return JSONResult("contextnode", {}, "fail", cnode.reason)
        else:
            nodes.append(cnode.content)
    return JSONResult("expcontext", content, "ok")


def cfgcontext_to_json_result(cctxt: "CfgContext") -> JSONResult:
    content: Dict[str, Any] = {}
    content["nodes"] = nodes = []
    for n in cctxt.nodes:
        cnode = contextnode_to_json_result(n)
        if not cnode.is_ok:
            return JSONResult("contextnode", {}, "fail", cnode.reason)
        else:
            nodes.append(cnode.content)
    return JSONResult("cfgcontext", content, "ok")


def programcontext_to_json_result(pctxt: "ProgramContext") -> JSONResult:
    content: Dict[str, Any] = {}
    jcfgcontext = cfgcontext_to_json_result(pctxt.cfg_context)
    if not jcfgcontext.is_ok:
        return JSONResult("programcontext", {}, "fail", jcfgcontext.reason)
    else:
        content["cfg-context"] = jcfgcontext.content
    jexpcontext = expcontext_to_json_result(pctxt.exp_context)
    if not jexpcontext.is_ok:
        return JSONResult("programcontext", {}, "fail", jexpcontext.reason)
    else:
        content["exp-context"] = jexpcontext.content
    return JSONResult("programcontext", content, "ok")


def ppo_to_json_result(po: "CFunctionPO") -> JSONResult:
    content: Dict[str, Any] = {}
    content["index"] = po.po_index
    content["line"] = po.line
    content["status"] = po.status
    content["predicate"] = str(po.predicate)
    content["context"] = programcontext_to_json_result(po.context).content
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
    # XXX: Add fn.api like in the text report
    ppos: Sequence["CFunctionPO"] = fn.get_ppos()
    jppos: List[Dict[str, Any]] = []
    for ppo in sorted(ppos, key=lambda po: po.line):
        pporesult = ppo_to_json_result(ppo)
        jppos.append(pporesult.content)
    content["ppos"] = jppos
    spos = fn.get_spos()
    jspos: List[Dict[str, Any]] = []
    for spo in sorted(spos, key=lambda po: po.line):
        sporesult = ppo_to_json_result(spo)
        jspos.append(sporesult.content)
    content["spos"] = jspos
    return JSONResult("cfunppos", content, "ok")


def file_proofobligations_to_json_result(cfile: "CFile") -> JSONResult:
    content: Dict[str, Any] = {}
    content["filedata"] = jsonfiledata(cfile)
    content["filesource"] = csource_to_json_result(cfile.sourcefile).content
    fnsdata: List[Dict[str, Any]] = []
    for fn in cfile.get_functions():
        fndata: Dict[str, Any] = {}
        fndata["functiondata"] = jsonfunctiondata(fn)
        fndata["pos"] = fn_proofobligations_to_json_result(fn).content
        fndata["api"] = fn_api_to_json_result(fn.api).content
        fnsdata.append(fndata)
    content["functions"] = fnsdata
    return JSONResult("fileproofobligations", content, "ok")
