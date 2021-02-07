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

from typing import Dict, List
import xml.etree.ElementTree as ET
import datetime
import os

replace_lst = [ ('&', "&amp;") , ('<',"&lt;")  , ('>',"&gt;") ,
                ('"',"&quot;") , ('\'',"&apos;") ]

def sanitize(str: str) -> str:
    for (c,r) in replace_lst:
        str = str.replace(c,r)
    return str

def attributes_to_pretty (attr: Dict[str, str],indent: int = 0) -> str:
    if len(attr) == 0:
        return ''
    if len(attr) > 4:
        lines: List[str] = []
        for key in sorted(attr):
            lines.append(((' ' * (indent + 2)) + key
                              + '="' + sanitize(str(attr[key])) + '"'))
        return ('\n' + '\n'.join(lines))
    else:
        return (' ' + ' '.join(key + '="' + sanitize(str(attr[key]))
                                   + '"' for key in sorted(attr)))

def element_to_pretty (e: ET.Element,indent:int = 0) -> List[str]:
    lines: List[str] = []
    attrs = attributes_to_pretty(e.attrib,indent)
    ind = ' ' * indent
    if e.text is None:
        children = list(e.findall('*'))
        if children == []:
            lines.append(ind + '<' + e.tag + attrs + '/>\n')
            return lines
        else:
            lines.append(ind + '<' + e.tag + attrs + '>\n')
            for c in children:
                lines.extend(element_to_pretty(c,indent+2))
            lines.append(ind + '</' + e.tag + '>\n')
            return lines
    else:
        lines.append(ind + '<' + e.tag + attrs + '>' + e.text + '</' + e.tag + '>\n')
    return lines


def doc_to_pretty (t: ET.ElementTree) -> str:
    lines = [ '<?xml version="1.0" encoding="UTF-8"?>\n' ]
    lines.extend(element_to_pretty(t.getroot()))
    return ''.join(lines)

def get_xml_header(filename: str,info: str) -> ET.Element:
    root = ET.Element('c-analysis')
    tree = ET.ElementTree(root)
    header = ET.Element('header')
    header.set('info',info)
    header.set('name',filename)
    header.set('time',str(datetime.datetime.now()))
    root.append(header)
    return root


