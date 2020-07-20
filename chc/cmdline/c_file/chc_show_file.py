# ------------------------------------------------------------------------------
# CodeHawk C Analyzer Analysis Results
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

import chc.reporting.reportutil as UR
from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help='directory that holds the analysis results')
    parser.add_argument('cfile',help='relative filename of the c source file')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    sempath = os.path.join(args.path,'semantics')
    capp = CApplication(sempath,args.cfile)
    cfile = capp.get_cfile()

    print(UR.reportheader('Global definitions and declarations for ' + args.cfile))

    print('-' * 80)
    print('Global type definitions')
    print('-' * 80)
    gtypes = cfile.get_gtypes()
    for gt in sorted(gtypes):
        tinfo = gt.typeinfo
        print(str(tinfo.get_type()) + ': ' + tinfo.get_name() +
              ' (' + gt.get_location().get_file() + ')')

    print('-' * 80)
    print('Global struct definitions')
    print('-' * 80)
    gcomptags = cfile.get_gcomptagdefs().values()
    for gc in sorted(gcomptags,key=lambda t:t.get_struct().get_name()):
        compinfo = gc.get_struct()
        print(compinfo.get_name() + ' (' + str(len(compinfo.fields)) +
              ' fields)')

    print('-' * 80)
    print('Global struct declarations')
    print('-' * 80)
    gcomptags = cfile.get_gcomptagdecls()
    for gc in sorted(gcomptags,key=lambda t:t.get_struct().get_name()):
        compinfo = gc.get_struct()
        print(compinfo.get_name() + ' (' + str(len(compinfo.fields())) +
              ' fields)')   

    print ('-' * 80)
    print('Global variable declarations')
    print('-' * 80)
    gvardecls = cfile.get_gvardecls()
    for vd in sorted(gvardecls,key=lambda v:v.varinfo.vname):
        vinfo = vd.varinfo
        print(str(vinfo.vtype) + '  ' + vinfo.vname)

    print('-' * 80)
    print('Global variable definitions')
    print('-' * 80)
    gvardefs = cfile.get_gvardefs()
    for vd in sorted(gvardefs,key=lambda v:v.varinfo.vname):
        vinfo = vd.varinfo
        print(str(vinfo.vtype) + '  ' + vinfo.vname)

    print('-' * 80)
    print('Function declarations')
    print('-' * 80)
    gfunctions = cfile.get_gfunctions().values()
    for f in sorted(gfunctions,key=lambda f:f.varinfo.vname):
        print(str(f))
