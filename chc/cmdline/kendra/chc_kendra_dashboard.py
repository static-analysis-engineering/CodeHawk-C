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

"""Shows results of the regression (kendra) tests.

The report should show the following columns:

testcase            name of the quartet of testcases (e.g. id115Q)
ppos                total number of primary proof obligations generated (e.g. 12)
spos                total number of secondary proof obligations generated (e;g. 0)
predicate           (optional) predicate of the ppo/spo that is violated (one per line)  
                      (e.g. index-upper-bound). For most test cases there is only one
                      predicate, occasionally there are two.
cfg-context         (optional) the location of the violated ppo/spo in the cfg
exp-context         (optional) the location of the violated ppo in an expression (only
                      applicable to ppo)
%safe (ppo)         percent of safe ppos proven safe
%violation (ppo)    percent of violated ppos proven violation
unknowns (ppo)      number of ppos not discharged
%safe (spo)         percent of safe spos proven safe (N/A if there are no spos)
%violation (spo)    percent of violated spos proven violation (N/A if there are no spos)
unknowns (spo)      number of spos not discharged (N/A if there are no spos)

"""
    
import argparse
import json
import os

from chc.util.Config import Config

kendra = os.path.join(os.path.join(Config().testdir,'sard'),'kendra')
testcases = [ (i,'id' + str(i) + 'Q') for i in range(115,394,4) ]

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--predicates',
                            help='Show violated predicates with location',action='store_true')
    args = parser.parse_args()
    return args

def getppocount(spec):
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            total += len(spec["cfiles"][f]["functions"][ff]["ppos"])
    return total

def getspocount(spec):
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            if "spos" in spec["cfiles"][f]["functions"][ff]:
                total += len(spec["cfiles"][f]["functions"][ff]["spos"])
    return total

def getppos(spec,f):
    ppos = []
    for ff in spec["cfiles"][f]["functions"]:
        ppos.extend(spec["cfiles"][f]["functions"][ff]["ppos"])
    return ppos
                
def getspos(spec, f):
    spos = []
    for ff in spec["cfiles"][f]["functions"]:
        if "spos" in spec["cfiles"][f]["functions"][ff]:
            spos.extend(spec["cfiles"][f]["functions"][ff]["spos"])
    return spos
    
def getviolationpredicates(spec):
    predicates = set([])
    for f in spec['cfiles']:
        for ppo in getppos(spec,f):
            status = ppo['tgtstatus']
            if status == 'violation':
                predicates.add((ppo['predicate'],ppo['cfgctxt'],ppo['expctxt']))
    return predicates
                                   
def getsafeproofperc(spec, obligationtype):
    safetgtcount = 0
    safecount = 0
    violationcount = 0
    violationtgtcount = 0
    unknowntgtcount = 0
    for f in spec['cfiles']:
        if obligationtype == 'ppo':
            for ppo in getppos(spec,f):
                if ppo['status'] == 'safe':
                    safetgtcount += 1
                    safecount += 1
                elif ppo['status'] == 'violation':
                    violationtgtcount += 1
                    violationcount += 1
                elif ppo['tgtstatus'] == 'safe':
                    safetgtcount += 1
                elif ppo['tgtstatus'] == 'violation':
                    violationtgtcount += 1
                else:
                    unknowntgtcount += 1
        elif obligationtype == 'spo':
            for spo in getspos(spec, f):
                if spo['status'] == 'safe':
                    safetgtcount += 1
                    safecount += 1
                elif spo['status'] == 'violations':
                    violationtgtcount += 1
                    violationcount += 1
                elif spo['tgtstatus'] == 'safe':
                    safetgtcount += 1
                elif spo['tgtstatus'] == 'violation':
                    violationtgtcount += 1
                else:
                    unknowntgtcount += 1
    if safetgtcount > 0:
        safepct = float(safecount)/float(safetgtcount) * 100.0
    else:
        safepct = 0.0
    if violationtgtcount > 0:
        violationpct = float(violationcount)/float(violationtgtcount) * 100.0
    else:
        violationpct = 0.0
    unknowns = '  -'
    if unknowntgtcount > 0:
        unknowns = str(unknowntgtcount).rjust(3)
    return ('{:>10.1f}'.format(safepct) + '    ' + '{:>10.1f}'.format(violationpct) +
                '     ' + unknowns + '   ')

def testdata(printpredicates,i,t,spec):
    lines = []
    ppocount = getppocount(spec)
    spocount = getspocount(spec)
    ppoproofperc = getsafeproofperc(spec, "ppo")
    spoproofperc = ''
    if spocount > 0 : spoproofperc = getsafeproofperc(spec, "spo")
    violationpreds = list(getviolationpredicates(spec))
    base = t + '  ' + str(ppocount).rjust(5) + '  ' + str(spocount).rjust(3) + ' '
    if len(violationpreds) == 0 and printpredicates == True:
        lines.append(base + (' ' * 104) + ppoproofperc + spoproofperc)
    elif printpredicates == True:
        lines.append(base + violationpreds[0][0].ljust(24) +
                         violationpreds[0][1].ljust(40) +
                         violationpreds[0][2].ljust(40) + ppoproofperc + spoproofperc)
        for v in violationpreds[1:]:
            lines.append((' ' * 19) + v[0].ljust(24) + v[1].ljust(40) + v[2].ljust(40))
    else:
        lines.append(base + ppoproofperc + spoproofperc)
    return lines

if __name__ == '__main__': 
    args = parse()

    header = 'testcase'.ljust(9) + 'ppos'.rjust(5) + 'spos'.rjust(5) + '  ' 
    if args.predicates:
        header += 'predicates'.ljust(24) + 'cfg-context'.ljust(40) + 'exp-context'.ljust(40)
    header += '%safe (ppos)'.rjust(10) + '  %violation'.rjust(10) + '  unknowns  '
    header += '%safe (spos)'.rjust(10) + '  %violation'.rjust(10) + '  unknowns'
    print header
    print('-' * 150)
    for (i,t) in testcases:
        specfilename = os.path.join(os.path.join(kendra, t),t + '.json')
        with open(specfilename) as fp:
            spec = json.load(fp)
        for l in testdata(args.predicates,i,t,spec):
            print(l)
        
