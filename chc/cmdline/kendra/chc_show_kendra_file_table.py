# ------------------------------------------------------------------------------
# CodeHawk C Source Code Analyzer
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
    parser.add_argument('cfilename',help='name of kendra c file (.e.g., id115.c)')
    parser.add_argument('--table',help='name of table to be shown')
    parser.add_argument('--list',help='list names of file tables',action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    cfilename = args.cfilename
    cpath = UF.get_kendra_cpath(cfilename)

    if cpath is None:
        print('*' * 80)
        print('Unable to find the test set for file ' + cfilename)
        print('*' * 80)
        exit(1)

    sempath = os.path.join(cpath,'semantics')
    cfapp = CApplication(sempath,cfilename)
    if cfapp.has_single_file():
        cfile = cfapp.get_cfile()

        if (args.table is None) or args.list:
            print(str(DT.list_file_tables()))

        else:
            print(str(DT.get_file_table(cfile,args.table)))

    else:
        print('*' * 80)
        print('File not found. Please make sure the test has been analyzed.')
        print('*' * 80)
        exit(1)
