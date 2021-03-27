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

import chc.app.CDictionaryRecord as CD


class CCompInfo(CD.CDeclarationsRecord):
    """Struct definition.

    tags:
        0: cname                 ('?' for global struct)

    args:
        0: ckey                  (-1 for global struct)
        1: isstruct
        2: iattr                 (-1 for global struct)
        3 ->: field indices
    """

    def __init__(self, decls, index, tags, args):
        CD.CDeclarationsRecord.__init__(self, decls, index, tags, args)
        self.fields = [self.decls.get_fieldinfo(i) for i in self.args[3:]]
        self.isstruct = self.args[1] == 1
        self.cattr = self.get_dictionary().get_attributes(args[2])

    def get_ckey(self):
        ckey = int(self.args[0])
        return ckey if ckey >= 0 else self.index

    def get_size(self):
        return sum([f.get_size() for f in self.fields])

    def get_name(self):
        if self.tags[0] == "?":
            name = list(self.decls.compinfo_names[self.get_ckey()])[0]
        else:
            name = self.tags[0]
        return name

    def get_field_strings(self):
        return ":".join([f.fname for f in self.fields])

    def __str__(self):
        lines = []
        lines.append("struct " + self.get_name())
        offset = 0
        for f in self.fields:
            lines.append((" " * 25) + str(offset).rjust(4) + "  " + str(f))
            offset += f.get_size()
        return "\n".join(lines)
