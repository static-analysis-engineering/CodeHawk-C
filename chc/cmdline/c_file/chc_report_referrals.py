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
import chc.reporting.ProofObligations as RP

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help='name of the directory that holds the semantics directory')
    parser.add_argument('cfile',help='filename of a c file')
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
    
    sempath = os.path.join(cpath,'semantics')

    capp = CApplication(sempath,args.cfile)
    cfile = capp.get_cfile()

    openppos = cfile.get_open_ppos()

    result = []

    for ppo in openppos:
        if  ppo.has_referral_diagnostic():
            result.append(ppo)

    for ppo in result:
        referral = ppo.get_referral_diagnostics()
        for k in referral:
            print('  ' + k + ': ' + str(referral[k]))
                
