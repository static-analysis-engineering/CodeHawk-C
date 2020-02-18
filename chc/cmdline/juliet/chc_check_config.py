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

from chc.util.Config import Config

width = 15

def itemstr(name,item,checkfilepresence=False,checkdirpresence=False):
    if checkfilepresence:
        checkpresence = os.path.isfile
    elif checkdirpresence:
        checkpresence = os.path.isdir
    else:
        checkpresence = None
    if checkpresence is None:
        found = ''
    else:
        if checkpresence(item):
            found = ' (found)'
        else:
            found = ' (** not found **)'
    return name.ljust(width) + ': ' + str(item) + found
    

if __name__ == '__main__':

    config = Config()

    print('\nAnalyzer configuration:')
    print('-' * 80)
    print(itemstr('base directory',config.topdir))
    print(itemstr('C parser',config.cparser,checkfilepresence=True))
    print(itemstr('C analyzer',config.canalyzer,checkfilepresence=True))
    print(itemstr('summaries',config.summaries,checkfilepresence=True))
    print('-' * 80)

    try:
        testcases = UF.get_juliet_testcases()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    total = 0
    print('Juliet Tests:')    
    for cwe in sorted(testcases):
        print('  ' + cwe.ljust(10))
        for subset in sorted(testcases[cwe]):
            total += len(testcases[cwe][subset])
            print('    '
                    + subset.ljust(10)
                    + str(len(testcases[cwe][subset])).rjust(4)
                    + (' tests' if len(testcases[cwe][subset]) > 1 else ' test'))
    print('-' * 80)
    print('  Total:'.ljust(12)
              + str(total).rjust(4)
              + ' test sets\n')
              
