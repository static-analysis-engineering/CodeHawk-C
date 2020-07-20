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
"""Lists the projects registered in Config.targets."""

import os

import chc.util.fileutil as UF

if __name__ == '__main__':

    targets = UF.get_registered_analysis_targets()

    for group in sorted(targets):
        gpath = targets[group]['path']
        print('=' * 80)
        print(group)
        print('-' * 80)
        for project in sorted(targets[group]['projects']):
            ppath = os.path.join(gpath,targets[group]['projects'][project]['path'])
            semfilename = os.path.join(ppath,'semantics_linux.tar.gz')
            semfound = ' present' if os.path.isfile(semfilename) else ' not found'
            print('\n  ' + project)
            print('    path: ' + ppath)
            print('    semantics file: '  + semfound)
