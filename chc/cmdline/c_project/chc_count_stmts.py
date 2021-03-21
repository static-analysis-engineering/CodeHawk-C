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
from typing import Any, Dict, List

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                            help=('directory that holds the semantics directory'
                                      + ' or the name of a test application'))
    parser.add_argument('--verbose',help='show individual function values',action='store_true')
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

    result: Dict[Any, Any] = {}
    asminstrs: List[Any] = []

    def f(fi):
        if not fi.name in result: result[fi.name] = {}
        def g(fn):
            if not fn.name in result[fi.name]:
                result[fi.name][fn.name] = {}
                result[fi.name][fn.name]['stmts'] = 0
                result[fi.name][fn.name]['calls'] = 0
                result[fi.name][fn.name]['assigns'] = 0
                result[fi.name][fn.name]['asms'] = 0
            def h(stmt):
                def i(instr):
                    entry = result[fi.name][fn.name]
                    if instr.is_assign(): entry['assigns'] += 1
                    elif instr.is_call(): entry['calls'] += 1
                    elif instr.is_asm():
                        entry['asms'] += 1
                        asminstrs.append(instr)
                    else: print('unknown instruction')
                result[fi.name][fn.name]['stmts'] += 1
                if stmt.is_instrs_stmt():
                    stmt.iter_instrs(i)
                stmt.iter_stmts(h)
            fn.body.iter_stmts(h)
        fi.iter_functions(g)
    capp.iter_files(f)

    if args.verbose:
        for filename in sorted(result):
            print('\n' + filename)
            for fnname in sorted(result[filename]):
                print('  ' + fnname)
                for s in sorted(result[filename][fnname]):
                    print('    ' + str(s).ljust(10) + ':' + str(result[filename][fnname][s]).rjust(4))

    nStmts = 0
    nCalls = 0
    nAssigns = 0
    nAsms = 0

    for filename in result:
        for fnname in result[filename]:
            entry = result [filename][fnname]
            nStmts += entry['stmts']
            nCalls += entry['calls']
            nAssigns += entry['assigns']
            nAsms += entry['asms']

    print('=' * 80)
    print('Statemenets              : ' + str(nStmts).rjust(5))
    print('  Call instructions      : ' + str(nCalls).rjust(5))
    print('  Assignment instructions: ' + str(nAssigns).rjust(5))
    print('  Assembly instructions  : ' + str(nAsms).rjust(5))
    print('=' * 80)

    if len(asminstrs) > 0:
        print('\nAssembly instructions')
        print('-' * 80)
        for i in asminstrs:
            print(str(i))
        print('-' * 80)
                                
                                
