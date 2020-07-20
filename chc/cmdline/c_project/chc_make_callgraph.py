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

import argparse
import os
import subprocess

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                            help=('directory that holds the semantics directory (or tar.gz file)'
                                      + ' or the name of a test application'))
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    
    try:
        cpath = UF.get_project_path(args.path)
        UF.check_analysis_results(cpath)        
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')
    capp = CApplication(sempath)

    result = {}

    def collect_fn_callees(fn):
        callees = [ str(i.get_callee()) for i in fn.get_call_instrs() ]
        fnresult = result[fn.name] = {}
        fncallees = fnresult['callees'] = {}
        for c in callees:
            fncallees.setdefault(c,0)
            fncallees[c] += 1

    def collect_fi_callees(fi):
        fi.iter_functions(collect_fn_callees)

    capp.iter_files(collect_fi_callees)

    UF.save_callgraph(cpath,result)

    for name in sorted(result):
        print('\n' + name)
        for c in sorted(result[name]['callees']):
            print('  ' + str(result[name]['callees'][c]).rjust(4)
                      + '  ' + str(c))
    
