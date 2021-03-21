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
from typing import Any, Dict

import chc.util.fileutil as UF

from chc.app.CApplication import CApplication

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('path',help=('directory that holds the semantics directory'
                                         + ' (or the name of a test application'))
    args = parser.parse_args()
    return args

def get_descendants(fname,graph):
    result = []
    if not fname in graph:
        return result
    callees = graph[fname]['callees']
    def add_callees(fn):
        if fn in result:
            return
        result.append(fn)
        if fn in graph:
            for c in  graph[fn]['callees']:
                add_callees(c)
    add_callees(fname)
    return result[1:]

def check_preserves_memory(fname,graph):
    descendants = get_descendants(fname,graph)
    memfreefns = [ 'free', 'realloc', 'regfree' ]
    return [ n for n in descendants if n in memfreefns ]


if __name__ == '__main__':

    args = parse()

    try:
        cpath = UF.get_project_path(args.path)
        UF.check_analysis_results(cpath)        
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    callgraph = UF.load_callgraph(cpath)

    if len(callgraph) == 0:
        print('Please create a callgraph first with chc_make_callgraph.py')
        exit(0)

    sempath = os.path.join(cpath,'semantics')
    if not os.path.isdir(sempath):
        print('semantics_not_found_err_msg: ' + cpath)
        exit(1)
        
    capp = CApplication(sempath)
    lines = []

    stats = {}
    stats['npost'] = 0
    stats['nglobal'] = 0
    stats['ndepppo'] = 0
    stats['ndepspo'] = 0

    calleetable: Dict[Any, Any] = {}  # file -> function -> postcondition request list

    def record_callee(callerfile,p):
        calleefn = callerfile.capp.resolve_vid_function(callerfile.index,p.callee.get_vid())
        if calleefn is None:  return

        calleefile = calleefn.cfile.name
        calleename  = p.callee.vname
        calleetable.setdefault(calleefile,{})
        calleetable[calleefile].setdefault(calleename,[])
        calleetable[calleefile][calleename].append(p)

    def calleetable_to_string():
        for fi in sorted(calleetable):
            lines.append('')
            lines.append('-' * 80)
            lines.append(fi)
            lines.append('-' * 80)
            for fn in sorted(calleetable[fi]):
                freeing = check_preserves_memory(fn,callgraph)
                freeing = ' ** [ ' + ', '.join(freeing) + ' ] **' if len(freeing) > 0 else ''
                lines.append('\n  ' + fn + freeing )
                for p in sorted(calleetable[fi][fn],key=lambda p:p.postrequest.get_postcondition().tags[0]):
                    lines.append('      ' + str(p))
        return '\n'.join(lines)

    def save_preserves_memory_functions():
        result = {}
        for fi in sorted(calleetable):
            result.setdefault(fi,[])
            for fn in sorted(calleetable[fi]):
                freeing =  check_preserves_memory(fn,callgraph)
                if len(freeing) == 0:
                    result[fi].append(fn)
        UF.save_preserves_memory_functions(cpath,result)

    def report_requests(fi):
        lines.append(fi.name)
        def f(fn):
            if fn.api.has_outstanding_requests():
                lines.append('  ' + fn.name)
                if fn.api.has_outstanding_postcondition_requests():
                    lines.append('    postcondition requests:')
                    for p in fn.api.get_postcondition_requests():
                        if p.has_open_pos():
                            record_callee(fi,p)
                            lines.append('      ' + str(p))
                            stats['npost'] += 1
                            stats['ndepppo'] += len(p.ppos)
                            stats['ndepspo'] += len(p.spos)
                            if p.postrequest.get_postcondition().is_preserves_all_memory():
                                freeing = check_preserves_memory(p.callee.vname,callgraph)
                                if len(freeing) > 0:
                                    lines.append('        ** [ ' + ', '.join(freeing) + ' ] **')
                            lines.append('')
                if fn.api.has_outstanding_global_requests():
                    lines.append('    global assumption requests:')
                    for p in fn.api.get_global_assumption_requests():
                        lines.append('      ' + str(p))
                        stats['nglobal'] += 1
                        stats['ndepppo'] += len(p.ppos)
                        stats['ndepspo'] += len(p.spos)
                        lines.append('')
        fi.iter_functions(f)

    capp.iter_files(report_requests)

    print('\n'.join(lines))

    print('\n\nPostcondition requests by callee')
    print(calleetable_to_string())
    save_preserves_memory_functions()

    print('\n' + ('-' * 80))
    print('Postcondition requests: ' + str(stats['npost']).rjust(4))
    print('Global requests       : ' + str(stats['nglobal']).rjust(4))
    print('Dependent ppos        : ' + str(stats['ndepppo']).rjust(4))
    print('Dependent spos        : ' + str(stats['ndepspo']).rjust(4))
    print('-' * 80)
    

    
