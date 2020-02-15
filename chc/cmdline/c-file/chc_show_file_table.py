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
import chc.reporting.DictionaryTables as DT

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help='directory that holds the semantics directory')
    parser.add_argument('cfile',help='name of c file')
    parser.add_argument('tablename',help='name of the table to be shown')
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
       
    try:
        cfapp = CApplication(sempath,args.cfile)
        cfile = cfapp.get_cfile()
    except UF.CFileNotFoundException as e:
        print(str(e.wrap()))
        exit(1)

    cfile = cfapp.get_cfile()

    print(DT.get_file_table(cfile,args.tablename))

