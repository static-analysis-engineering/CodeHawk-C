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
    parser.add_argument('functionname',help='name of the function to find')
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

    functionindex = UF.load_functionindex(cpath)

    def get_alternatives(fnname):
        if len(functionindex)  < 20:
            return sorted(functionindex.keys())
        fstarts1 = [ n for n in functionindex if n.startswith(fnname[0]) ]
        if len(fstarts1) > 0:
            if len(fstarts1) < 20:
                return sorted(fstarts1)
            fstarts2 = [ n for n in functionindex if n.startswith(fnname[0:2]) ]
            if len(fstarts2) > 0:
                return sorted(fstarts2)
            else:
                return sorted(fstarts1)
        return sorted(functionindex.keys())

    def handle_request():
        if args.functionname in functionindex:
            fnrecs = functionindex[args.functionname]
            pfiles = 'Files' if len(fnrecs) > 1 else 'File'
            print(pfiles + ' with a function named ' + args.functionname + ':')
            for fnrec in fnrecs:
                pstatic = ' (static)' if fnrec['s'] == 's' else ''
                print(' - ' + fnrec['f'] +  '.c' + pstatic)
                if 'n' in fnrec:
                    print('   Notes: ' + '; '.join(fnrec['n']))
        else:
            print('Function ' + args.functionname + ' not found in the function index')
            print('Did you mean:')
            alternatives = get_alternatives(args.functionname)
            for a in alternatives:
                print(a)

    if len(functionindex) > 0:
        handle_request()

    else:
        cmd = ['python', 'chc_index_project_functions.py', args.path, '--verbose' ]
        result = subprocess.call(cmd,stderr=subprocess.STDOUT)
        if result != 0:
            print('Error in indexing functions for ' + args.path)
            exit(0)

        functionindex = UF.load_functionindex(cpath)
        if len(functionindex) > 0:
            handle_request()

        else:
            print('Indexing the functions was not successful')
        
            
        
    

