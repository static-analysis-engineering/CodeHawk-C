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

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                            help=('directory that holds the semantics directory'
                                      + ' or the name of a test application'))
    parser.add_argument('--contractpath',help='path to the contracts file',default=None)
    parser.add_argument('--xpre',help="don't show preconditions",action='store_true')
    parser.add_argument('--xpost',help="don't show postconditions",action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_semantics(cpath,deletesemantics=False)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    sempath = os.path.join(cpath,'semantics')
       
    if args.contractpath is None:
        contractpath = os.path.join(cpath,'chc_contracts')
    else:
        contractpath = args.contractpath

    capp = CApplication(sempath,contractpath=contractpath)


    lines = []
    result = {}
    result['pre'] = 0
    result['post'] = 0

    def f(fi):
        if fi.has_file_contracts():
            if (not args.xpost) and fi.contracts.has_postconditions():
                lines.append(str(fi.contracts.report_postconditions()))
                result['post'] += fi.contracts.count_postconditions()
            if (not args.xpre)  and fi.contracts.has_preconditions():
                lines.append(str(fi.contracts.report_preconditions()))
                result['pre'] += fi.contracts.count_preconditions()

    try:
        capp.iter_files(f)
    except UF.CHCError as e:
        print(str(e.wrap()))
        exit(1)

    print('\n'.join(lines))

    print('\n')
    print('=' * 80)
    print('Postconditions: ' + str(result['post']))
    print('Preconditions : ' + str(result['pre']))
    print('=' * 80)
        

