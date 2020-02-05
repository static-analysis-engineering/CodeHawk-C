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

The report shows the following columns:

testcase: name of the quartet of testcases (e.g. id115Q).
  ppos: total number of primary proof obligations generated;
  %safe proven: percent of safe ppos proven safe;
  %violation proven: percent of violations proven to be violation;
  %delegated: percent of proof obligations delegated;
  open: number of open ppos;

  spos: total number of supporting proof obligations generated;
  %safe proven: percent of safe spos proven safe;
  %violation proven: percent of violations proven to be violation;
  %delegated: percent of spos delegated;
  open: number of open spos;

predicates: predicates that are violated.
"""
    
import argparse
import json
import os

from chc.util.Config import Config

kendra = os.path.join(Config().testdir,'kendra')
testcases = [ (i,'id' + str(i) + 'Q') for i in range(115,394,4) ]

def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()
    return args

def get_ppo_count(spec):
    """Returns the number of ppos in the spec file."""
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            total += len(spec["cfiles"][f]["functions"][ff]["ppos"])
    return total

def get_spo_count(spec):
    """Returns the number of spos in the spec file."""
    total = 0
    for f in spec["cfiles"]:
        for ff in spec["cfiles"][f]["functions"]:
            if "spos" in spec["cfiles"][f]["functions"][ff]:
                total += len(spec["cfiles"][f]["functions"][ff]["spos"])
    return total

def get_ppos(spec,f):
    ppos = []
    for ff in spec["cfiles"][f]["functions"]:
        ppos.extend(spec["cfiles"][f]["functions"][ff]["ppos"])
    return ppos
                
def get_spos(spec, f):
    spos = []
    for ff in spec["cfiles"][f]["functions"]:
        if "spos" in spec["cfiles"][f]["functions"][ff]:
            spos.extend(spec["cfiles"][f]["functions"][ff]["spos"])
    return spos
    
def get_violation_predicates(spec):
    predicates = set([])
    for f in spec['cfiles']:
        for ppo in get_ppos(spec,f):
            status = ppo['tgtstatus']
            if status in ['violation','violation:delegated']:
                predicates.add(ppo['predicate'])
        for spo in get_spos(spec,f):
            status = spo['tgtstatus']
            if status == 'violation':
                predicates.add(ppo['predicate'])
    return predicates

def get_perc(x,y,width):
    fmt = '{:>' + str(width) + '.1f}'
    if y > 0:
        perc = float(x)/float(y) * 100.0
        return fmt.format(perc)
    else:
        return ' - '.rjust(width)

def get_status_ppo_counts(spec,status):
    count = 0
    tgtcount = 0
    for f in spec['cfiles']:
        for ppo in get_ppos(spec,f):
            if ppo['tgtstatus'] == status:
                tgtcount += 1
                if ppo['status'] == status:
                    count += 1
    return (count,tgtcount)

def get_open_ppo_count(spec):
    count = 0
    for f in spec['cfiles']:
        for ppo in get_ppos(spec,f):
            if ppo['status'] == 'open':
                count += 1
    return count

def get_safe_ppo_counts(spec):
    return get_status_ppo_counts(spec,'safe')

def get_safe_ppo_perc(spec,width):
    (cnt,tgtcnt)  = get_safe_ppo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_violation_ppo_counts(spec):
    return get_status_ppo_counts(spec,'violation')

def get_violation_ppo_perc(spec,width):
    (cnt,tgtcnt) = get_violation_ppo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_delegated_ppo_counts(spec):
    (safecnt,safetgtcnt) = get_status_ppo_counts(spec,'safe:delegated')
    (vcnt,vtgtcnt) = get_status_ppo_counts(spec,'violation:delegated')
    return (safecnt + vcnt, safetgtcnt + vtgtcnt)

def get_delegated_ppo_perc(spec,width):
    (cnt,tgtcnt) = get_delegated_ppo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_status_spo_counts(spec,status):
    count = 0
    tgtcount = 0
    for f in spec['cfiles']:
        for spo in get_spos(spec,f):
            if spo['tgtstatus'] == status:
                tgtcount += 1
                if spo['status'] == status:
                    count += 1
    return (count,tgtcount)

def get_open_spo_count(spec):
    count = 0
    for f in spec['cfiles']:
        for spo in get_spos(spec,f):
            if spo['status'] == 'open':
                count += 1
    return count

def get_safe_spo_counts(spec):
    return get_status_spo_counts(spec,'safe')

def get_safe_spo_perc(spec,width):
    (cnt,tgtcnt) = get_safe_spo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_violation_spo_counts(spec):
    return get_status_spo_counts(spec,'violation')

def get_violation_spo_perc(spec,width):
    (cnt,tgtcnt) = get_violation_spo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_delegated_spo_counts(spec):
    (safecnt,safetgtcnt) = get_status_spo_counts(spec,'safe:delegated')
    (vcnt,vtgtcnt) = get_status_spo_counts(spec,'violation:delegated')
    return (safecnt + vcnt, safetgtcnt + vtgtcnt)

def get_delegated_spo_perc(spec,width):
    (cnt,tgtcnt) = get_delegated_spo_counts(spec)
    return get_perc(cnt,tgtcnt,width)

def get_ppo_results(spec):
    opencnt = get_open_ppo_count(spec)
    if opencnt == 0: opencnt = '-'
    return (str(get_ppo_count(spec)).rjust(6)
                + get_safe_ppo_perc(spec,12)
                + get_violation_ppo_perc(spec,12)
                + get_delegated_ppo_perc(spec,12)
                + str(opencnt).rjust(10))

def get_spo_results(spec):
    spocount = get_spo_count(spec)
    if spocount == 0: spocount = '-'
    opencnt = get_open_spo_count(spec)
    if opencnt == 0: opencnt =  '-'
    return (str(spocount).rjust(6)
                + get_safe_spo_perc(spec,12)
                + get_violation_spo_perc(spec,12)
                + get_delegated_spo_perc(spec,12)
                + str(opencnt).rjust(10))

if __name__ == '__main__': 
    args = parse()
    header = 'testcase'.ljust(9)
    headerppos = ('ppos'.rjust(6) + '   ' + '%safe'.center(12) + '%violation'.center(12)
                      + '%delegated'.center(12)
                      + '%open'.center(12))
    headerspos =  ('spos'.rjust(6) + '  ' + '%safe'.center(12) + '%violation'.center(12)
                       + '%delegated'.center(12)
                       + '%open'.center(12))
    header = header + headerppos + headerspos + '  predicates'
    headerline2 = (' '.ljust(18) + 'proven'.center(12) + 'proven'.center(12)
                       + '-'.ljust(32) + 'proven'.center(12) + 'proven'.center(12))
    print(header)
    print(headerline2)
    print('-' * 150)
    for (i,t) in testcases:
        if (i % 100) < 4: print('-' * 120)
        specfilename = os.path.join(os.path.join(kendra, t),t + '.json')
        with open(specfilename) as fp:
            spec = json.load(fp)
        print(t.ljust(9) + get_ppo_results(spec)
                  + '   | ' 
                  + get_spo_results(spec) + ' '.ljust(6)
                  + ','.join(get_violation_predicates(spec)))
    print('-' * 150)
        
