# ------------------------------------------------------------------------------
# CodeHawk C Analyze
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


class CFieldInfo(CD.CDeclarationsRecord):
    """Definition of a struct field.

    tags:
        0: fname

    args:
        0: fcomp.ckey  (-1 for global structs)
        1: ftype
        2: fbitfield
        3: fattr       (-1 for global structs)
        4: floc        (-1 for global structs)
    """

    def __init__(self, cdecls, index, tags, args):
        CD.CDeclarationsRecord.__init__(self, cdecls, index, tags, args)
        self.fname = self.tags[0]
        self.ftype = self.get_dictionary().get_typ(self.args[1])
        self.bitfield = self.args[2]

    def get_size(self):
        return self.ftype.get_size()

    def get_location(self):
        if self.args[4] >= 0:
            return self.decls.get_location(self.args[4])

    def get_attributes(self):
        if self.args[3] >= 0:
            return self.decls.get_attributes(self.args[3])

    def __str__(self):
        return self.fname + ":" + str(self.ftype)
