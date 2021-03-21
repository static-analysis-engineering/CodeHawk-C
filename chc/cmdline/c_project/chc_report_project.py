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
import time

from contextlib import contextmanager

import chc.reporting.ProofObligations as RP
import chc.util.fileutil as UF

from chc.util.Config import Config
from chc.util.IndexedTable import IndexedTableError
from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help=('directory that holds the semantics directory'
                                         + ' or the name of a test application'))
    parser.add_argument('--history',help='include historical results',
                            action='store_true')
    args = parser.parse_args()
    return args

@contextmanager
def timing(activity):
    t0 = time.time()
    yield
    print('\n' + ('=' * 80) +
          '\nCompleted ' + activity + ' in ' + str(time.time() - t0) + ' secs' +
          '\n' + ('=' * 80))

if __name__ == '__main__':

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_analysis_results(cpath)        
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    if args.history:
        summarieslist = UF.read_project_summary_results_history(cpath)
    else:
        summaries = UF.read_project_summary_results(cpath)
        summarieslist = [ summaries ] if summaries else []
   
    for summaries in summarieslist:
        # summaries = UF.read_project_summary_results(cpath)
        try:
            if summaries == None:
                sempath = os.path.join(cpath,'semantics')
                capp = CApplication(sempath)
                timestamp = os.stat(capp.path).st_ctime
                result = RP.project_proofobligation_stats_to_dict(capp)
                result['timestamp'] = timestamp
                result['project'] = cpath
                UF.save_project_summary_results(cpath, result)
                UF.save_project_summary_results_as_xml(cpath, result)
                summaries = UF.read_project_summary_results(cpath)
            print(RP.project_proofobligation_stats_dict_to_string(summaries))
        except IndexedTableError as e:
            print(
                '\n' + ('*' * 80) + '\nThe analysis results format has changed'
                + '\nYou may have to re-run the analysis first: '
                + '\n' + e.msg
                + '\n' + ('*' * 80))
    
