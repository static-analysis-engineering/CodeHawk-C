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
from typing import Any, Dict

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                            help=('directory that holds the semantics directory'
                                      + ' or the name of a test application'))
    parser.add_argument('--all',help='show all, including application headers',
                            action='store_true')
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

    resultheaders: Dict[Any, Any] = {}
    result: Dict[Any, Any] = {}

    def get_fn_missing_summaries(fn):
        missingsummaries = fn.api.get_missing_summaries()
        for s in missingsummaries:
            names = s.split('/')
            if len(names) == 2:
                resultheaders.setdefault(names[0],{})
                resultheaders[names[0]].setdefault(names[1],0)
                resultheaders[names[0]][names[1]] += 1
            else:
                result.setdefault(s,0)
                result[s] += 1

    def get_fi_missing_summaries(fi):
        fi.iter_functions(get_fn_missing_summaries)

    capp.iter_files(get_fi_missing_summaries)

    for h in sorted(resultheaders):
        if capp.is_application_header(h) and not args.all: continue        
        print('\n' + h)
        for m in sorted(resultheaders[h]):
            print('  ' + str(resultheaders[h][m]).rjust(4) + '  ' + m)

    if len(result) > 0:
        print('\n\nOthers:')
        for m in sorted(result):
            print(str(result[m]).rjust(4) + '  ' + m)

