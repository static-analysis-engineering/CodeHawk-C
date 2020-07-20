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
import json
import os

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help=('path to directory that holds the semantics directory'
                                         + ' (or the name of a test application)'))
    parser.add_argument('--contractpath',help='path to save the contracts file',default=None)
    parser.add_argument('--preservesmemory',help='initialize with preserves-memory postcondition',
                            action='store_true')
    parser.add_argument('--ignorefile',help='json file that lists functions included from header files')
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
    capp = CApplication(sempath)
    if args.contractpath is None:
        contractpath = os.path.join(cpath,'chc_contracts')
    else:
        contractpath = args.contractpath

    ignorefns = {}

    if not args.ignorefile is None:
        if os.path.isfile(args.ignorefile):
            with open(args.ignorefile,'r') as fp:
                headers = json.load(fp)
            for h in headers:
                for fn in headers[h]['functions']:
                    ignorefns[fn] = h

    preserves_memory_functions = UF.load_preserves_memory_functions(cpath)

    def create_contract_file(f):
        if f.name in preserves_memory_functions:
            preservesmemory = preserves_memory_functions[f.name]
        else:
            preservesmemory = []
        f.create_contract(contractpath,preservesmemory=preservesmemory)

    # capp.iter_files(lambda f:f.create_contract(contractpath,args.preservesmemory,ignorefns=ignorefns))
    capp.iter_files(create_contract_file)

