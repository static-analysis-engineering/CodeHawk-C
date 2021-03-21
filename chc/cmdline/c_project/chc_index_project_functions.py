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
import logging
import time
import os
import subprocess
from typing import Any, Dict

from contextlib import contextmanager

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                            help=('directory that holds the semantics directory (or tar.gz file)'
                                      + ' or the name of a test applications'))
    parser.add_argument('--verbose',help='show progress',action='store_true')
    args = parser.parse_args()
    return args

@contextmanager
def timing(activity):
    t0 = time.time()
    yield
    print('\n' + ('=' * 80) + 
          '\nCompleted ' + activity + ' in ' + str(time.time() - t0) + ' secs' +
          '\n' + ('=' * 80))

functionindex: Dict[Any, Any] = {}

if __name__ == '__main__':

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)
        
    sempath = os.path.join(cpath,'semantics')

    def indexfile(cfile):
        if args.verbose: print('- ' + cfile.name)
        def indexfn(cfun):
            if not cfun.name in functionindex:
                functionindex[cfun.name] = []
            cfunrecord = {}
            cfunrecord['f'] = cfile.name
            cfunrecord['s'] = cfun.svar.get_vstorage()
            functionindex[cfun.name].append(cfunrecord)
        cfile.iter_functions(indexfn)

    capp = CApplication(sempath)

    with timing('indexing functions'):

        if args.verbose:
            print('-' * 80)
            print('Indexing files ...')
        capp.iter_files(indexfile)
        
        if args.verbose:
            print('-' * 80)
            print('Index:')
            for fn in sorted(functionindex):
                print('  - ' + fn)
                for fnrec in functionindex[fn]:
                    pstatic = ' (static)' if fnrec['s'] == 's' else ''
                    print('      ~ ' + fnrec['f'] + pstatic)
            print('-' * 80)

        UF.save_functionindex(cpath,functionindex)

            

        

        
