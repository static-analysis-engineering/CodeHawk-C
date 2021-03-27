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

import xml.etree.ElementTree as ET

import chc.app.CDictionaryRecord as CD


class CLocation(CD.CDeclarationsRecord):
    """Location in a C source program.

    tags: -

    args:
        0: filename index
        1: byte number
        2: line number
    """

    def __init__(self, decls, index, tags, args):
        CD.CDeclarationsRecord.__init__(self, decls, index, tags, args)

    def get_byte(self):
        return int(self.args[1])

    def get_line(self):
        return int(self.args[2])

    def get_file(self):
        return self.decls.get_filename(int(self.args[0]))

    def get_loc(self):
        return (self.get_file(), self.get_line(), self.get_byte())

    def __ge__(self, loc):
        return self.get_loc >= loc.get_loc()

    def __gt__(self, loc):
        return self.get_loc > loc.get_loc()

    def __le__(self, loc):
        return self.get_loc <= loc.get_loc()

    def __lt__(self, loc):
        return self.get_loc < loc.get_loc()

    def __eq__(self, loc):
        return self.get_loc == loc.get_loc()

    def __ne__(self, loc):
        return self.get_loc != loc.get_loc()

    def __str__(self):
        return str(self.get_file()) + ":" + str(self.get_line())
