#!/usr/bin/env python
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
import json
import os
import shutil

import chc.util.fileutil as UF
from chc.util.Config import Config

from chc.cmdline.ParseManager import ParseManager

def parse():
    usage = ('\nCall with the name of the c file\n\n' +
                 '  Example: python chc_parse_file.py id115.c\n\n' +
                 'Optionally add the name of an existing directory to save \n' +
                 'the semantics files.\n\n' +
                 '  Example: python chc_parse_file.py id115.c --targetpath mysemanticsdir\n\n')
    description = ('Preprocesses and parses a single c source code file.\n' +
                       'Preprocessing is performed with the gcc preprocessor.')
    epilog = ('==Note==:' +
                  '  When run on a MacOSX platform, the parser may not be able ' +
                  'to handle the syntax of mac standard header files.')
    parser = argparse.ArgumentParser(usage=usage,description=description,epilog=epilog)
    parser.add_argument('filename',help='name of .c file to parse')
    parser.add_argument('--targetpath',
                            help=('name of directory to save semantics files ' +
                                      '(default is same directory as filename)'),
                                      default=None)
    parser.add_argument('--savesemantics',
                            help='create gzipped tar file with semantics files',
                            action='store_true')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()

    try:
        UF.check_parser()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    cfilename = os.path.abspath(args.filename)
    if not os.path.isfile(cfilename):
        print('*' * 80)
        print('C source code file ' + cfilename + ' not found')
        print('*' * 80)
        exit(1)

    if not cfilename.endswith('.c'):
        print('*' * 80)
        print('C source code file should have extension .c')
        print('*' * 80)
        exit(1)

    cpath = os.path.dirname(cfilename)
    if args.targetpath:
        targetpath = os.path.abspath(args.targetpath)
    else:
        targetpath = cpath
        
    if not os.path.isdir(targetpath):
        print('*' * 80)
        print('Target directory ' + targetpath + ' not found')
        print('Please create directory first')
        print('*' * 80)
        exit(1)

    os.chdir(targetpath)
    if os.path.isdir('semantics'):
        print('Removing semantics directory')
        shutil.rmtree('semantics')

    if args.savesemantics:
        if os.path.isfile('semantics_linux.tar.gz'):
            print('Removing semantics_linux.tar.gz')
            os.remove('semantics_linux.tar.gz')
    
    parsemanager = ParseManager(cpath,targetpath)
    parsemanager.initialize_paths()

    try:
        basename = os.path.basename(cfilename)
        ifilename = parsemanager.preprocess_file_with_gcc(basename)
        result = parsemanager.parse_ifile(ifilename)
        if result != 0:
            print('*' * 80)
            print('Error in parsing ' + cfilename)
            if Config().platform == 'macOS':
                print('  (Problem may be related to standard header files on macOS)')
            print('*' * 80)
            exit(1)
    except OSError as e:
        print('Error when parsing file: ' + str(e))
        exit(1)
        
    
    if args.savesemantics:
        parsemanager.save_semantics()
