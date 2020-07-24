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
"""Utility functions for printing a score report for a Juliet Test."""

from chc.cmdline.juliet.JulietTestSetRef import JulietTestSetRef


violationcategories = [ 'V', 'S', 'D', 'U', 'O' ]
safecontrolcategories = [ 'S', 'D', 'X', 'U', 'O']

violations = 'vs'
safecontrols = 'sc'

'''Return true if a ppo matches a ppo listed in the test set reference.

A ppo listed in a test set reference is always characterized by the ppo
predicate, and may additionally be characterized (if multiple ppo's with
the same predicate appear on the same line) by a set of variable names,
one of which has to appear in the ppo, or an expression context.
'''
def keymatches(tppo,ppo):
    return (tppo.line == ppo.get_line()
                and tppo.predicate == ppo.predicatetag
                and tppo.matches_exp_ctxt(ppo)
                and tppo.matches_variable_names(ppo)
                and tppo.matches_variable_names_plus(ppo)
                and tppo.matches_variable_deref(ppo)
                and tppo.matches_target_type(ppo)
                and tppo.matches_pred_arg(ppo)
                and tppo.matches_reference_type(ppo))

def initialize_testsummary(testset,d):
    def f(tindex,test):
        d[tindex] = {}
        d[tindex][violations] = {}
        for c in violationcategories:
            d[tindex][violations][c] = 0
        d[tindex][safecontrols] = {}
        for c in safecontrolcategories:
            d[tindex][safecontrols][c] = 0
    testset.iter(f)

def classify_tgt_violation(po,capp):
    if po is None: return 'U'                                # unknown
    if po.is_open(): return 'U'                              # unknown
    if po.is_violated(): return 'V'                          # violation reported
    if po.dependencies is None: return 'U'                   # unknown
    dm = po.dependencies.level
    if dm == 'f' or dm == 's': return 'S'                     # found safe
    if po.is_delegated():
        spos = get_associated_spos(po,capp)
        if len(spos) > 0:
            classifications = [ classify_tgt_violation(spo,capp) for spo in spos ]
            if 'V' in classifications: return 'V'              # violation reported
            if all( [ x == 'S' for x in classifications ] ): return 'S'     # found safe
        else:
            return 'O'                                         # no callsite found
        return 'D'                                             # found deferred
    return 'O'                                                 # other

def classify_tgt_safecontrol_contract_assumption(po,capp):
    return 'S'

def classify_tgt_safecontrol(po,capp):
    if po is None: return 'U'                                 # unknown
    if po.is_open(): return 'U'                               # unknown
    if po.is_violated(): return 'O'                           # violation
    if po.dependencies is None: return 'U'                    # unknown
    dm = po.dependencies.level
    if dm == 's' or dm == 'f': return 'S'                      # safe
    if po.is_delegated():
        dependencies_type = po.get_dependencies_type()
        if po.get_dependencies_type() == 'contract':
            return classify_tgt_safecontrol_contract_assumption(po,capp)
        spos = get_associated_spos(po,capp)
        if len(spos) > 0:
            classifications = [ classify_tgt_safecontrol(spo,capp) for spo in spos ]
            if all( [ x == 'S' for x in classifications ]):
                return 'S'                                      # safe
            if 'O' in classifications: return 'O'
            return 'D'                                          # deferred
        else:
            return 'O'
    if po.is_deadcode(): return 'X'                            # dead code
    return 'O'                                                  # other

def fill_testsummary(pairs,d,capp):
    for filename in pairs:
        for fn in pairs[filename]:
            for (jppo,ppo) in pairs[filename][fn]:
                tindex = jppo.get_test()
                tsummary = d[tindex]
                if jppo.is_violation():
                    classification = classify_tgt_violation(ppo,capp)
                    tsummary[violations][classification] += 1
                else:
                    classification = classify_tgt_safecontrol(ppo,capp)
                    tsummary[safecontrols][classification] += 1

def get_associated_spos(ppo,capp):
    result = []
    if ppo.has_dependencies():
        cfun = ppo.cfun
        cfile = ppo.cfile
        callsites = capp.get_callsites(cfile.index,cfun.svar.get_vid())
        assumptions = ppo.dependencies.ids
        assumptions = [ cfun.podictionary.get_assumption_type(i) for i in assumptions ]
        assumptions = [ a.get_predid() for a in assumptions
                            if a.is_api_assumption() or a.is_global_api_assumption() ]
        if len(callsites) > 0:
            for ((fid,vid),cs) in callsites:
                def f(spo):
                    if spo.apiid in assumptions:
                        result.append(spo)
                cs.iter(f)
    return result

def testppo_calls_tostring(ppo,capp):
    lines = []
    cfun = ppo.cfun
    cfile = ppo.cfile
    callsites = capp.get_callsites(cfile.index,cfun.svar.get_vid())
    if len(callsites) > 0:
        lines.append('    calls:')
        for ((fid,vid),cs) in callsites:
            def f(spo):
                sev = spo.explanation
                if sev is None: sevtxt = '?'
                else:
                    sevtxt = spo.get_display_prefix() + '  ' + sev
                lines.append('     C:' + str(spo.get_line()).rjust(3) + '  ' +
                                 spo.predicatetag.ljust(25) + sevtxt)
            cs.iter(f)
    return '\n'.join(lines)
    

def testppo_results_tostring(pairs,capp):
    lines = []
    for filename in sorted(pairs):
        lines.append('\n' + filename)
        for fn in sorted(pairs[filename]):
            if len(pairs[filename][fn]) == 0: continue
            lines.append('\n  ' + fn)
            for (jppo,ppo) in pairs[filename][fn]:
                ev = ppo.explanation
                if ev is None:
                    evstr = '?'
                else:
                    evstr = ppo.get_display_prefix() + '  ' + ev
                lines.append('    ' + str(ppo.get_line()).rjust(3) + '  ' +
                                 str(ppo.id).rjust(3) + ': ' +
                                 ppo.predicatetag.ljust(25) + evstr)
                if (not ev is None) and ppo.is_delegated():
                    lines.append(testppo_calls_tostring(ppo,capp))
    return '\n'.join(lines)
                                 
def testsummary_tostring(d,totals):
    lines = []
    lines.append('\nSummary\n')
    lines.append('test              violations                    safe-controls')
    lines.append('         V    S    D    U    O                S    D    X    U    O')
    lines.append('-' * 80)
    for tindex in sorted(d):
        if tindex == 'total': continue
        sv = d[tindex][violations]
        ss = d[tindex][safecontrols]
        lines.append(tindex.ljust(5) +
                        ''.join([str(sv[c]).rjust(5) for c in violationcategories]) +
                        '       |    ' +
                        ''.join([str(ss[c]).rjust(5) for c in safecontrolcategories]))
    lines.append('-' * 80)
    totals = d['total']
    lines.append('total' +
              ''.join([str(totals[violations][c]).rjust(5) for c in violationcategories]) +
              '       |    ' +
              ''.join([str(totals[safecontrols][c]).rjust(5) for c in safecontrolcategories]))
    return '\n'.join(lines)


'''Return the ppos from the testsetref in a dictionary indexed by filename.

Note: the reference ppos are function agnostic.
'''
def get_julietppos(testset):
    ppos = {}
    def g(filename,fileref):
        if not filename in ppos: ppos[filename] = []
        def h(line,jppo):
            ppos[filename].append(jppo)
        fileref.iter(h)
    def f(tindex,test): test.iter(g)
    testset.iter(f)
    return ppos

'''Return pairs of the reference ppo with the actual ppo for all reference ppos.

Organized as a dictionary: filename -> functionname -> (testppo,ppo) list
'''
def get_ppo_pairs(julietppos,capp):
    pairs = {}
    for filename in julietppos:
        if not filename in pairs: pairs[filename] = {}
        julietfileppos = julietppos[filename]
        cfile = capp.get_file(filename)

        fileppos = cfile.get_ppos()
        for ppo in fileppos:
            fname = ppo.cfun.name
            if not fname in pairs[filename]: pairs[filename][fname] = []
            for jppo in julietfileppos:
                if keymatches(jppo,ppo):
                    pairs[filename][fname].append((jppo,ppo))
    return pairs

'''Return a dictionary with the counts of the different categories over all files.

violation/safe-controls -> category -> total count over all files.
'''
def get_testsummarytotals(d):
    if 'total' in d:
        return d['total']
    totals = {}
    totals[violations] = {}
    totals[safecontrols] = {}
    for c in violationcategories:
        totals[violations][c] = sum([d[x][violations][c] for x in d ])
    for c in safecontrolcategories:
        totals[safecontrols][c] = sum([d[x][safecontrols][c] for x in d ])
    d['total'] = totals
    return d
    

    
    

