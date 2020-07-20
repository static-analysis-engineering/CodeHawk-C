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
import chc.reporting.ProofObligations as RP

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help='path to directory that holds the semantics directory')
    parser.add_argument('cfile',help='filename of c file')
    parser.add_argument('cfunction',help='name of function to report on')
    parser.add_argument('--open',help='only show open proof obligations',action='store_true')
    parser.add_argument('--violations',help='only show proof obligations that are violated',
                            action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    cpath = os.path.abspath(args.path)

    try:
        UF.check_semantics(cpath)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)
        
    sempath = os.path.join(args.path, 'semantics')
        
    cfapp = CApplication(sempath,args.cfile)
    cfile = cfapp.get_cfile()

    try:
        cfunction = cfile.get_function_by_name(args.cfunction)
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if args.open and args.violations:
        def pofilter(po):return not po.is_closed() or po.is_violated()
    elif args.open:
        def pofilter(po):return not po.is_closed()
    elif args.violations:
        def pofilter(po):return po.is_violated()
    else:
        def pofilter(po):return True

    print(RP.function_code_tostring(cfunction,pofilter=pofilter))
