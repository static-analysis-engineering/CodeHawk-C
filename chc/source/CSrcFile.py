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

import os

import chc.util.fileutil as UF

class CSrcFile(object):
    """Represents the text file that holds the C source code."""

    def __init__(self,capp,fname):
        self.capp = capp
        self.fname = fname
        self.lines = {}
        if not self.fname.endswith('.c'): self.fname = fname + '.c'

    def get_line_count(self):
        return sum(1 for line in open(self.fname))

    def get_line(self,n):
        self._initialize()
        if n <= len(self.lines):
            return (str(n) + '  ' + self.lines[n])

    def _initialize(self):
        if len(self.lines) > 0: return
        if os.path.isfile(self.fname):
            print('Reading file ' + self.fname)
            n = 1
            with open(self.fname) as f:
                for line in f:
                    self.lines[n] = line
                    n += 1
        else:
            print('Source file ' + self.fname + ' not found')
