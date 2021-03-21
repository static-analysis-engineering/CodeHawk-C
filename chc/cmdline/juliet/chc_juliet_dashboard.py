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

violationcategories = [ 'V', 'S', 'D', 'U', 'O' ]
safecontrolcategories = [ 'S', 'D', 'X', 'U', 'O']

vhandled = [ 'V' ]
shandled = [ 'S', 'X' ]

violations = 'vs'
safecontrols = 'sc'

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cwe',help='only report on the given cwe')
    args = parser.parse_args()
    return args

if __name__ == '__main__':

    args = parse()
    cwerequested = 'all'
    if args.cwe is not None: cwerequested = args.cwe

    try:
        testcases = UF.get_flattened_juliet_testcases()
    except UF.CHError as e:
        print(str(e.wrap()))
        exit(1)

    stotals : Dict[Any, Any] = {}
    stotals[violations] = {}
    stotals[safecontrols] = {}
    for c in violationcategories: stotals[violations][c] = 0
    for c in safecontrolcategories: stotals[safecontrols][c] = 0

    vppototals = 0
    sppototals = 0
    vppohandled = 0
    sppohandled = 0

    tnamelength = 0
    for cwe in testcases:
        maxlen = max(len(t) for t in testcases[cwe]) + 3
        if maxlen > tnamelength:
            tnamelength = maxlen

    print('\n\nSummary')
    print('\n')
    print('test'.ljust(tnamelength + 10) +    'violations                     safe-controls')
    print(' '.ljust(tnamelength + 4) + 'V    S    D    U    O          S    D    X    U    O')
    print('-' * (tnamelength + 64))

    for cwe in sorted(testcases):
        if not (cwe == cwerequested or cwerequested == 'all'): continue
        print('\n'+cwe)
        ctotals: Dict[Any, Any] = {}
        ctotals[violations] = {}
        ctotals[safecontrols] = {}
        for c in violationcategories: ctotals[violations][c] = 0
        for c in safecontrolcategories: ctotals[safecontrols][c] = 0
        for cc in sorted(testcases[cwe]):
            testtotals = UF.read_juliet_test_summary(cwe,cc)
            if not (testtotals is None):
                totals = testtotals['total']
                print(cc.ljust(tnamelength) +
                        ''.join([str(totals[violations][c]).rjust(5) for c in violationcategories]) +
                        '   |  ' +
                        ''.join([str(totals[safecontrols][c]).rjust(5) for c in safecontrolcategories]))
                for c in violationcategories:
                    ctotals[violations][c] += totals[violations][c]
                    stotals[violations][c] += totals[violations][c]
                    vppototals += totals[violations][c]
                    if c in vhandled: vppohandled += totals[violations][c]
                for c in safecontrolcategories:
                    ctotals[safecontrols][c] += totals[safecontrols][c]
                    stotals[safecontrols][c] += totals[safecontrols][c]
                    sppototals += totals[safecontrols][c]
                    if c in shandled: sppohandled += totals[safecontrols][c]
            else:
                print(cc.ljust(tnamelength) + ('-'  * (44 - int(tnamelength/2))) + ' not found ' +
                        ('-' * (44 - int(tnamelength/2))))

        print('-' * (tnamelength + 64))
        print('total'.ljust(tnamelength) +
                  ''.join([str(ctotals[violations][c]).rjust(5) for c in violationcategories]) +
                  '   |  ' +
                  ''.join([str(ctotals[safecontrols][c]).rjust(5) for c in safecontrolcategories]))

    print('\n\n')
    print('=' * (tnamelength + 64))
    print('grand total'.ljust(tnamelength) +
              ''.join([str(stotals[violations][c]).rjust(5) for c in violationcategories]) +
              '   |  ' +
              ''.join([str(stotals[safecontrols][c]).rjust(5) for c in safecontrolcategories]))

    ppototals = vppototals + sppototals
    ppohandled = vppohandled + sppohandled

    if vppototals > 0:
        vperc = float(vppohandled)/float(vppototals) * 100.0
    else:
        vperc = 0.0
    if sppototals > 0:
        sperc = float(sppohandled)/float(sppototals) * 100.0
    else:
        sperc = 0.0
    if ppototals > 0:
        perc = float(ppohandled)/float(ppototals) * 100.0
    else:
        perc = 0.0
    print('\n\n' + ' '.ljust(28) + 'violation      safe-control     total')
    print('-' * 80)
    print('ppos'.ljust(20) + str(vppototals).rjust(15) + str(sppototals).rjust(15)
              + str(ppototals).rjust(15))
    print('reported'.ljust(20) + str(vppohandled).rjust(15)
              + str(sppohandled).rjust(15) + str(ppohandled).rjust(15))
    print('percent reported'.ljust(20)  + str('{:.1f}'.format(vperc)).rjust(15)
              + str('{:.1f}'.format(sperc)).rjust(15) +
              str('{:.1f}'.format(perc)).rjust(15))
    print('-' * 80)

