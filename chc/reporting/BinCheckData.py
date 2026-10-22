# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2026  Aarno Labs LLC
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

from abc import ABC, abstractmethod
from typing import Any, cast, ClassVar, Dict, List, TYPE_CHECKING

from chc.jsoninterface.JSONResult import JSONResult

if TYPE_CHECKING:
    from chc.app.CApplication import CApplication
    from chc.app.CCompInfo import CCompInfo
    from chc.app.CFile import CFile
    from chc.app.CFunction import CFunction
    from chc.app.CTyp import (
        CTyp, CTypInt, CTypFloat, CTypPtr, CTypComp, CTypArray, CTypFun)
    from chc.app.CVarInfo import CVarInfo


class BinCheckTypeClassification(ABC):

    def __init__(self, ctype: "CTyp") -> None:
        self._ctype = ctype

    @property
    def ctype(self) -> "CTyp":
        return self._ctype

    @abstractmethod
    def to_json_result(self) -> JSONResult:
        ...


class BinCheckTypeInteger(BinCheckTypeClassification):

    def __init__(self, ctype: "CTypInt") -> None:
        BinCheckTypeClassification.__init__(self, ctype)

    @property
    def ctype(self) -> "CTypInt":
        return cast("CTypInt", super().ctype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "int"
        content["kind"] = self.ctype.ikind
        return JSONResult("inttypeclass", content, "ok")


class BinCheckTypeFloat(BinCheckTypeClassification):

    def __init__(self, ctype: "CTypFloat") -> None:
        BinCheckTypeClassification.__init__(self, ctype)

    @property
    def ctype(self) -> "CTypFloat":
        return cast("CTypFloat", super().ctype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "float"
        content["kind"] = self.ctype.fkind
        return JSONResult("floattypeclass", content, "ok")


class BinCheckTypePointer(BinCheckTypeClassification):

    def __init__(self, ctype: "CTyp") -> None:
        BinCheckTypeClassification.__init__(self, ctype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "pointer"
        content["is-function-pointer"] = self.ctype.is_function
        return JSONResult("pointertypeclass", content, "ok")


class BinCheckTypeCompound(BinCheckTypeClassification):

    compinfokeys: ClassVar[List[int]] = []
    compinfos: ClassVar[Dict[int, "CCompInfo"]] = {}

    def __init__(self, ctype: "CTypComp") -> None:
        BinCheckTypeClassification.__init__(self, ctype)
        if not ctype.ckey in self.compinfokeys:
            self.compinfos.setdefault(ctype.ckey, ctype.compinfo)

    @property
    def ctype(self) -> "CTypComp":
        return cast("CTypComp", super().ctype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "compound"
        content["kind"] = "struct" if self.ctype.is_struct else "union"
        content["ckey"] = self.ctype.ckey
        content["name"] = self.ctype.name
        return JSONResult("compoundtypeclass", content, "ok")


class BinCheckTypeArray(BinCheckTypeClassification):

    def __init__(self, ctype: "CTypArray") -> None:
        BinCheckTypeClassification.__init__(self, ctype)

    @property
    def ctype(self) -> "CTypArray":
        return cast("CTypArray", super().ctype)

    @property
    def elementtype(self) -> BinCheckTypeClassification:
        return get_type_classification(self.ctype.array_basetype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "array"
        content["elem-type"] = self.elementtype.to_json_result().content
        content["elem-count"] = (
            self.ctype.size if self.ctype.has_array_constant_size() else 0)
        return JSONResult("arraytypeclass", content, "ok")


class BinCheckTypeOther(BinCheckTypeClassification):

    def __init__(self, ctype: "CTyp") -> None:
        BinCheckTypeClassification.__init__(self, ctype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["typeclass"] = "other"
        content["name"] = str(self.ctype)
        return JSONResult("othertypeclass", content, "ok")


class BinCheckTypeClassificationFactory:

    @staticmethod
    def get_bincheck_type_classification(
            ctype: "CTyp") -> BinCheckTypeClassification:
        ctype = ctype.expand()
        if ctype.is_int:
            ictype = cast("CTypInt", ctype)
            return BinCheckTypeInteger(ictype)
        elif ctype.is_float:
            fctype = cast("CTypFloat", ctype)
            return BinCheckTypeFloat(fctype)
        elif ctype.is_pointer:
            return BinCheckTypePointer(ctype)
        elif ctype.is_array:
            actype = cast ("CTypArray", ctype)
            return BinCheckTypeArray(actype)
        elif ctype.is_comp:
            cctype = cast ("CTypComp", ctype)
            return BinCheckTypeCompound(cctype)
        else:
            return BinCheckTypeOther(ctype)


def get_type_classification(ctype: "CTyp") -> BinCheckTypeClassification:
    return BinCheckTypeClassificationFactory.get_bincheck_type_classification(
        ctype.expand())


class BinCheckSignature:

    def __init__(self, ftype: "CTypFun") -> None:
        self._ftype = ftype

    @property
    def ftype(self) -> "CTypFun":
        return self._ftype

    @property
    def returntype(self) -> BinCheckTypeClassification:
        return get_type_classification(self.ftype.return_type)

    @property
    def argument_types(self) -> List[BinCheckTypeClassification]:
        if self.ftype.funargs is None:
            return []
        result: List[BinCheckTypeClassification] = []
        for arg in self.ftype.funargs.arguments:
            bctype = get_type_classification(arg.typ)
            result.append(bctype)
        return result

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["return-type"] = self.returntype.to_json_result().content
        content["is-vararg"] = self.ftype.is_vararg
        content["argument-types"] = argtypes = []
        for argtype in self.argument_types:
            argtypes.append(argtype.to_json_result().content)
        return JSONResult("binchecksignature", content, "ok")


class BinCheckStructDef:

    def __init__(self, compinfo: "CCompInfo") -> None:
        self._compinfo = compinfo

    @property
    def compinfo(self) -> "CCompInfo":
        return self._compinfo

    @property
    def field_types(self) -> List[BinCheckTypeClassification]:
        result: List[BinCheckTypeClassification] = []
        for fieldinfo in self.compinfo.fields:
            bctype = get_type_classification(fieldinfo.ftype)
            result.append(bctype)
        return result

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["ckey"] = self.compinfo.ckey
        content["name"] = self.compinfo.name
        content["field-types"] = fields = []
        for f in self.field_types:
            fields.append(f.to_json_result().content)
        return JSONResult("bincheckstructdef", content, "ok")


class BinCheckLocalVar:

    def __init__(self, cvar: "CVarInfo") -> None:
        self._cvar = cvar

    @property
    def cvar(self) -> "CVarInfo":
        return self._cvar

    @property
    def ctype(self) -> BinCheckTypeClassification:
        return get_type_classification(self.cvar.vtype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["vname"] = self.cvar.vname
        content["vtype"] = self.ctype.to_json_result().content
        return JSONResult("binchecklocalvar", content, "ok")


class BinCheckGlobalVar:

    def __init__(self, cvar: "CVarInfo") -> None:
        self._cvar = cvar

    @property
    def cvar(self) -> "CVarInfo":
        return self._cvar

    @property
    def ctype(self) -> BinCheckTypeClassification:
        return get_type_classification(self.cvar.vtype)

    @property
    def is_static(self) -> bool:
        return self.cvar.is_static

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["vname"] = self.cvar.vname
        content["vtype"] = self.ctype.to_json_result().content
        content["is-static"] = self.is_static
        return JSONResult("bincheckglobalvar", content, "ok")


class BinCheckFunctionData:

    def __init__(self, cfun: "CFunction") -> None:
        self._cfun = cfun

    @property
    def cfun(self) -> "CFunction":
        return self._cfun

    @property
    def localvars(self) -> List[BinCheckLocalVar]:
        return [BinCheckLocalVar(cvar) for cvar in self.cfun.locals.values()]

    @property
    def signature(self) -> BinCheckSignature:
        ftype = cast("CTypFun", self.cfun.ftype)
        return BinCheckSignature(ftype)

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["name"] = self.cfun.name
        content["signature"] = self.signature.to_json_result().content
        content["local-vars"] = locals = []
        for cvar in self.localvars:
            locals.append(cvar.to_json_result().content)
        return JSONResult("bincheckfunctiondata", content, "ok")


class BinCheckFileData:

    def __init__(self, cfile: "CFile") -> None:
        self._cfile = cfile
        self._functiondata: Dict[str, BinCheckFunctionData] = {}
        self._staticvars: Dict[str, BinCheckGlobalVar] = {}

    @property
    def cfile(self) -> "CFile":
        return self._cfile

    @property
    def functiondata(self) -> List[BinCheckFunctionData]:
        return [BinCheckFunctionData(cfun) for cfun in self.cfile.functions.values()]

    @property
    def staticvars(self) -> List[BinCheckGlobalVar]:
        result: List[BinCheckGlobalVar] = []
        for cvar in self.cfile.cfileglobals.global_varinfo_names.values():
            if cvar.is_static:
                result.append(BinCheckGlobalVar(cvar))
        return result

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["filename"] = self.cfile.name
        content["static-vars"] = statics = []
        for cvar in self.staticvars:
            statics.append(cvar.to_json_result().content)
        content["functions"] = cfuns = []
        for cfun in self.functiondata:
            cfuns.append(cfun.to_json_result().content)
        content["structdefs"] = jstructdefs = []
        structdefs = list(BinCheckTypeCompound.compinfos.values())
        structdefkeys = list(BinCheckTypeCompound.compinfos.keys())
        while len(structdefs) > 0:
            BinCheckTypeCompound.compinfokeys.extend(structdefkeys)
            BinCheckTypeCompound.compinfos.clear()
            bcstructdefs = [BinCheckStructDef(s) for s in sorted(structdefs, key=lambda s:s.ckey)]
            jstructdefs.extend([s.to_json_result().content for s in bcstructdefs])
            structdefs = list(BinCheckTypeCompound.compinfos.values())
            structdefkeys = list(BinCheckTypeCompound.compinfos.keys())
        return JSONResult("bincheckfiledata", content, "ok")


class BinCheckData:

    def __init__(self, capp: "CApplication") -> None:
        self._capp = capp
        self._filedata: Dict[str, BinCheckFileData] = {}
        self._globalvars: Dict[str, BinCheckGlobalVar] = {}
        self._structdefs: Dict[int, BinCheckStructDef] = {}

    @property
    def capp(self) -> "CApplication":
        return self._capp

    @property
    def filedata(self) -> List[BinCheckFileData]:
        return [BinCheckFileData(cfile) for cfile in self.capp.files.values()]

    @property
    def globalvars(self) -> List[BinCheckGlobalVar]:
        result: List[BinCheckGlobalVar] = []
        for cvar in self.capp.declarations.varinfo_values():
            if not cvar.is_static and not cvar.vtype.is_function:
                result.append(BinCheckGlobalVar(cvar))
        return result

    def to_json_result(self) -> JSONResult:
        content: Dict[str, Any] = {}
        content["projectname"] = self.capp.projectname
        content["global-vars"] = [
            g.to_json_result().content for g in self.globalvars]
        content["files"] = [f.to_json_result().content for f in self.filedata]
        return JSONResult("bincheckdata", content, "ok")
