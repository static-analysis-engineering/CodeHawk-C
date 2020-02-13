# ------------------------------------------------------------------------------
# CodeHawkC Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Kestrel Technology LLC
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

import time

"""Utility functions for reporting proof obligations and their statistics."""

dischargemethods = [ 'stmt', 'local', 'api', 'contract', 'open', 'violated' ]

histogramcolors = {
    'violated': 'red',
    'stmt': 'green',
    'local': 'lightgreen',
    'api': 'springgreen',
    'contract': 'aquamarine',
    'open': 'orange'
    }

def get_dsmethods(extra):
    return extra + dischargemethods

def get_dsmethod_header(indent,dsmethods,header1=''):
    return (header1.ljust(indent) + ''.join([dm.rjust(10) for dm in dsmethods]) + 'total'.rjust(10))

def classifypo(po,d):
    '''Classify proof obligation with respect to discharge method and update dictionary.

    Args:
      po: proof obligation (CFunctionPO)
      d: dictionary, with discharge methods initialized (is updated)
    '''
    if po.is_closed():
        if po.is_violated(): d['violated'] += 1
        deps = po.dependencies
        if deps.has_external_dependencies():
            deptype = po.get_dependencies_type()
            d[deptype] += 1
        elif deps.is_stmt():
            d['stmt'] += 1
        elif deps.is_local() or deps.is_deadcode():
            d['local'] += 1
        else:
            print('Unable to classify ' + str(po))
    else:
        d['open'] += 1

def get_method_count(pos,filefilter=lambda f:True,extradsmethods=[]):
    '''Create dicharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by discharge method
    '''
    result = {}
    for dm in get_dsmethods(extradsmethods): result[dm] = 0
    for po in pos:
        classifypo(po,result)
    return result

def get_tag_method_count(pos,filefilter=lambda f:True,extradsmethods=[]):
    '''Create predicate tag, discharge method count dictionary.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by predicate and discharge method
    '''
    result = {}
    dsmethods = get_dsmethods(extradsmethods)
    for po in pos:
        if not filefilter(po.cfile.name): continue
        tag = po.predicatetag
        if not tag in result:
            result[tag] = {}
            for dm in dsmethods: result[tag][dm] = 0
        classifypo(po,result[tag])
    return result

def get_file_method_count(pos,filefilter=lambda f:True,extradsmethods=[]):
    '''Create file, discharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by file and discharge method
    '''
    result = {}
    dsmethods = get_dsmethods(extradsmethods)
    for po in pos:
        pofile = po.cfile.name
        if not filefilter(pofile): continue
        if not pofile in result:
            result[pofile] = {}
            for dm in dsmethods: result[pofile][dm] = 0
        classifypo(po,result[pofile])
    return result

def get_function_method_count(pos,extradsmethods=[]):
    '''Create function, discharge method count dictionary from proof obligation list.

    Args:
      pos: flat list of proof obligations (primary or secondary)
      filefilter: predicate that specifies which c files to include
      extradsmethods: additional discharge methods to include in classification
    Returns:
      dictionary that organizes proof obligations by function and discharge method
    '''
    result = {}
    dsmethods = get_dsmethods(extradsmethods)
    for po in pos:
        pofunction = po.cfun.name
        if not pofunction in result:
            result[pofunction] = {}
            for dm in dsmethods: result[pofunction][dm] = 0
        classifypo(po,result[pofunction])
    return result

def row_method_count_tostring(d,perc=False,extradsmethods=[],rhlen=25,header1=''):
    '''Display a dictionary with row-header - discharge method - count.

    Args:
      d: dictionary (row header -> discharge method -> count
      perc: boolean that indicates whether to print discharge method percentages
      extradsmethods: list of additional column headers (will be prepended)
      rhlen: maximum length of the row header (default 25)
    Returns:
      table of discharge method counts represented as a string
'''
    lines = []
    width = 10
    dsmethods = get_dsmethods(extradsmethods)
    lines.append(get_dsmethod_header(rhlen,dsmethods,header1=header1))
    barlen = 70 + rhlen
    lines.append('-' * barlen)
    for t in sorted(d):
        r = [ d[t][dm] for dm in dsmethods ]
        total = sum( [ d[t][dm] for dm in dsmethods if not dm == 'violated' ])
        lines.append(t.ljust(rhlen) + ''.join([str(x).rjust(width) for x in r]) + str(total).rjust(width))
    lines.append('-' * barlen )

    totals = {}
    for dm in dsmethods:
        totals[dm] = sum([ d[t][dm] for t in d ])
    totalcount = sum([ totals[dm] for dm in totals if not dm == 'violated'])
    lines.append('total'.ljust(rhlen) + ''.join([str(totals[dm]).rjust(width) for dm in dsmethods]) +
                     str(totalcount).rjust(width))
    if perc and totalcount > 0:
        scale = float(totalcount)/100.0
        lines.append('percent'.ljust(rhlen) +
                         ''.join([str('{:.2f}'.format(float(totals[dm])/scale)).rjust(width)
                                      for dm in dsmethods]))
    return '\n'.join(lines)
    

class FunctionDisplay(object):

    def __init__(self,cfunction,sourcecodeavailable):
        self.cfunction = cfunction
        self.sourcecodeavailable = sourcecodeavailable
        self.cfile = self.cfunction.cfile
        self.fline = self.cfunction.get_location().get_line()
        self.currentline = self.fline + 1

    def get_source_line(self,line):
        srcline = self.cfile.get_source_line(line)
        if not srcline is None:
            return self.cfile.get_source_line(line).strip()
        return '?'

    def pos_no_code_to_string(self,pos,pofilter=lambda po:True):
        lines = []
        for po in sorted(pos,key=lambda po:po.get_line()):
            if not pofilter(po): continue
            delegated = ''
            indent = 18 if po.is_ppo() else 24
            if po.is_closed():
                expl = po.explanation
                prefix = po.get_display_prefix()
                lines.append(prefix + ' ' + str(po))
                lines.append((' ' * indent) + expl)
            else:
                lines.append('\n<?> ' + str(po))
                if po.has_diagnostic():
                    amsgs = po.diagnostic.amsgs
                    if len(amsgs) > 0:
                        for arg in sorted(amsgs):
                            for s in sorted(amsgs[arg]):
                                lines.append((' ' * indent) + s)
                    kmsgs = po.diagnostic.kmsgs
                    if len(kmsgs) > 0:
                        for key in sorted(kmsgs):
                            for s in sorted(kmsgs[key]):
                                lines.append((' ' * indent) + key + ": " + s)
                    msgs = po.diagnostic.msgs
                    if len(msgs) > 0:
                        for m in msgs:
                            lines.append((' ' * indent) + m)
                    keys = po.diagnostic.get_argument_indices()
                    for k in sorted(keys):
                        invids = po.diagnostic.get_invariant_ids(k)
                        for id in invids:
                            inv = self.cfunction.invd.get_invariant_fact(id).get_non_relational_value()
                            lines.append((' ' * indent) + str(k) + ': ' + str(inv))
                else:
                    lines.append((' ' * indent) + '---> no diagnostic found')
        return '\n'.join(lines)


    def pos_on_code_tostring(self,pos,pofilter=lambda po:True,showinvs=False):
        lines = []
        contexts = set([])
        for po in sorted(pos,key=lambda po:po.get_line()):
            if not pofilter(po): continue
            line = po.get_line()
            if line >= self.currentline:
                if len(contexts) > 0 and showinvs:
                    lines.append('\n' + (' ' * indent) + '-------- context invariants --------')
                    for c in contexts:
                        lines.append((' ' * indent) + str(c))
                        lines.append((' ' * indent) + ('-' * len(str(c))))
                        lines.append(str(self._get_context_invariants(c)))
                        lines.append(' ')
                lines.append('-' * 80)
                if self.sourcecodeavailable:
                    for n in range(self.currentline,line+1):
                        lines.append(self.get_source_line(n))
                else:
                    if self.currentline == line:
                        lines.append('source line ' + str(line))
                    else:
                        lines.append('source lines ' + str(self.currentline) + ' - '
                                        + str(line))
                lines.append('-' * 80)
                contexts = set([])
            self.currentline = line + 1
            delegated = ''
            indent = 18 if po.is_ppo() else 24
            if po.is_closed():
                # contexts.add(po.context)    (uncomment to see all invariants)
                expl = po.explanation
                prefix = po.get_display_prefix()
                lines.append(prefix + ' ' + str(po))
                lines.append((' ' * indent) + expl)
            else:
                contexts.add(po.context)
                lines.append('\n<?> ' + str(po))
                if po.has_diagnostic():
                    amsgs = po.diagnostic.amsgs
                    if len(amsgs) > 0:
                        for arg in sorted(amsgs):
                            for s in sorted(amsgs[arg]):
                                lines.append((' ' * indent) + s)
                    kmsgs = po.diagnostic.kmsgs
                    if len(kmsgs) > 0:
                        for key in sorted(kmsgs):
                            for s in sorted(kmsgs[key]):
                                lines.append((' ' * indent) + key + ": " + s)
                    msgs = po.diagnostic.msgs
                    if len(msgs) > 0:
                        for m in msgs:
                            lines.append((' ' * indent) + m)
                    keys = po.diagnostic.get_argument_indices()
                    for k in sorted(keys):
                        invids = po.diagnostic.get_invariant_ids(k)
                        for id in invids:
                            inv = self.cfunction.invd.get_invariant_fact(id).get_non_relational_value()
                            lines.append((' ' * indent) + str(k) + ': ' + str(inv))
                else:
                    lines.append((' ' * indent) + '---> no diagnostic found')
                lines.append(' ')

                if (showinvs and (not po.has_diagnostic())):
                    lines.append((' ' * 18) + '--')
                    lines.append(self._get_po_invariants(po.context,po.id))

        if len(contexts) > 0 and showinvs:
                lines.append('\n' + (' ' * indent) + '-------- context invariants --------')
                for c in contexts:
                        lines.append((' ' * indent) + '=== ' + str(c) + ' ===')
                        lines.append(str(self._get_context_invariants(c)))
                        lines.append(' ')

        self.currentline = self.fline + 1
        return '\n'.join(lines)

    def _get_po_invariants(self,context,poId):
        lines = []
        invs = self.cfunction.invtable.get_po_invariants(context,poId)
        for inv in invs:
            lines.append((' ' * 18) + str(inv))
        return '\n'.join(lines)

    def _get_context_invariants(self,context):
        lines = []
        invs = self.cfunction.invtable.get_sorted_invariants(context)
        for inv in invs:
            lines.append((' ' * 18) + str(inv))
        return '\n'.join(lines)

def function_pos_to_string(fn,pofilter=lambda po:True):
    lines = []
    ppos = fn.get_ppos()
    ppos = [ x for x in ppos if pofilter(x) ]
    spos = fn.get_spos()
    fd = FunctionDisplay(fn,False)
    if len(ppos) + len(spos) > 0:
        lines.append('\nFunction ' + fn.name)
        lines.append(fd.pos_no_code_to_string(ppos,pofilter=pofilter))
        lines.append(fd.pos_no_code_to_string(spos,pofilter=pofilter))
    return '\n'.join(lines)

def function_code_tostring(fn,pofilter=lambda po:True,showinvs=False,showpreamble=True):
    lines = []
    ppos = fn.get_ppos()
    ppos = [ x for x in ppos if pofilter(x) ]
    spos = fn.get_spos()
    fnstartline = fn.get_line_number()
    if fnstartline is None:
        lines.append('\nFunction ' + fn.name + ' (source code not available, included from '
                         + str(fn.get_source_code_file()) + ')')
        fd = FunctionDisplay(fn,False)
    else:
        fnstartline = fn.cfile.get_source_line(fnstartline)
        lines.append('\nFunction ' + fn.name)
        lines.append('-' * 80)
        lines.append(fnstartline.strip())
        fd = FunctionDisplay(fn,True)
    if showpreamble:
        lines.append('-' * 80)
        lines.append(str(fn.api))
        lines.append('-' * 80)
    if len(ppos) > 0:
        lines.append('Primary Proof Obligations:')
        lines.append(fd.pos_on_code_tostring(ppos,pofilter=pofilter,showinvs=showinvs))
        lines.append('-' * 80)
    if len(spos) > 0:
        lines.append('Supporting Proof Obligations:')
        lines.append(fd.pos_on_code_tostring(spos,pofilter=pofilter,showinvs=showinvs))
    return '\n'.join(lines)

def function_code_open_tostring(fn,showinvs=False):
    pofilter = lambda po:(po.is_violated() or (not po.is_closed()))
    return function_code_tostring(fn,pofilter=pofilter,showinvs=showinvs)

def function_code_violation_tostring(fn,showinvs=False):
    pofilter = lambda po:po.is_violated()
    return function_code_tostring(fn,pofilter=pofilter,showinvs=showinvs)

def function_code_predicate_tostring(fn,p,showinvs=False):
    pofilter = lambda po:po.predicatetag == p
    return function_code_tostring(fn,pofilter=pofilter,showinvs=showinvs)

def file_pos_violations_to_string(cfile):
    lines = []
    pofilter = lambda po:(po.is_violated())
    def f(fn): lines.append(function_pos_to_string(fn,pofilter=pofilter))
    cfile.iter_functions(f)
    return '\n'.join(lines)
    
def file_code_tostring(cfile,pofilter=lambda po:True,showinvs=False):
    lines = []
    def f(fn): lines.append(function_code_tostring(fn,pofilter=pofilter,showinvs=showinvs))
    cfile.iter_functions(f)
    return '\n'.join(lines)

def file_code_open_tostring(fn,showinvs=False):
    pofilter = lambda po:(po.is_violated() or (not po.is_closed()))
    return file_code_tostring(fn,pofilter=pofilter,showinvs=showinvs)

def proofobligation_stats_tostring(pporesults,sporesults,rhlen=28,header1='',extradsmethods=[]):
    lines = []
    lines.append('\nPrimary Proof Obligations')
    lines.append(row_method_count_tostring(pporesults,perc=True,rhlen=rhlen,header1=header1))
    if len(sporesults) > 0:
        lines.append('\nSupporting Proof Obligations')
        lines.append(row_method_count_tostring(sporesults,perc=True,rhlen=rhlen,header1=header1))   
    return '\n'.join(lines)

def project_proofobligation_stats_tostring(capp,filefilter=lambda f:True,extradsmethods=[]):
    lines = []
    ppos = capp.get_ppos()
    spos = capp.get_spos()
    pporesults = get_file_method_count(ppos,extradsmethods=extradsmethods,filefilter=filefilter)
    sporesults = get_file_method_count(spos,extradsmethods=extradsmethods,filefilter=filefilter)

    rhlen = capp.get_max_filename_length() + 3
    lines.append(proofobligation_stats_tostring(pporesults,sporesults,rhlen=rhlen,header1='c files',
                                                    extradsmethods=extradsmethods))
    tagpporesults = get_tag_method_count(ppos,filefilter=filefilter,extradsmethods=extradsmethods)
    tagsporesults = get_tag_method_count(spos,filefilter=filefilter,extradsmethods=extradsmethods)

    lines.append('\n\nProof Obligation Statistics')
    lines.append('~' * 80)
    lines.append(proofobligation_stats_tostring(tagpporesults,tagsporesults,
                                                    extradsmethods=extradsmethods))
    return '\n'.join(lines)

def project_proofobligation_stats_to_dict(capp,filefilter=lambda f:True,extradsmethods=[]):
    ppos = capp.get_ppos()
    spos = capp.get_spos()
    pporesults = get_file_method_count(ppos,extradsmethods=extradsmethods,filefilter=filefilter)
    sporesults = get_file_method_count(spos,extradsmethods=extradsmethods,filefilter=filefilter)    
    tagpporesults = get_tag_method_count(ppos,filefilter=filefilter,extradsmethods=extradsmethods)
    tagsporesults = get_tag_method_count(spos,filefilter=filefilter,extradsmethods=extradsmethods)
    result = {}
    result['tagresults'] = {}
    result['fileresults'] = {}
    result['stats'] = capp.get_project_counts(filefilter=filefilter)
    result['tagresults']['ppos'] = tagpporesults
    result['tagresults']['spos'] = tagsporesults
    result['fileresults']['ppos'] = pporesults
    result['fileresults']['spos'] = sporesults
    return result

def project_proofobligation_stats_dict_to_string(stats_dict):
    lines = []

    pporesults = stats_dict['fileresults']['ppos']
    sporesults = stats_dict['fileresults']['spos']

    rhlen = max([ len(x) for x in pporesults ])
    lines.append(proofobligation_stats_tostring(pporesults,sporesults,rhlen=rhlen,header1='c files'))

    lines.append('\n\nProof Obligation Statistics')

    tagpporesults = stats_dict['tagresults']['ppos']
    tagsporesults = stats_dict['tagresults']['spos']
    lines.append(proofobligation_stats_tostring(tagpporesults,tagsporesults))

    return '\n'.join(lines)
    
def file_proofobligation_stats_tostring(cfile,extradsmethods=[]):
    lines = []
    ppos = cfile.get_ppos()
    spos = cfile.get_spos()
    pporesults = get_function_method_count(ppos,extradsmethods=extradsmethods)
    sporesults = get_function_method_count(spos,extradsmethods=extradsmethods)

    rhlen = cfile.get_max_functionname_length() + 3
    lines.append(proofobligation_stats_tostring(pporesults,sporesults,rhlen=rhlen,
                                                    header1='functions'))

    tagpporesults = get_tag_method_count(ppos,extradsmethods=extradsmethods)
    tagsporesults = get_tag_method_count(spos,extradsmethods=extradsmethods)

    lines.append('\n\nProof Obligation Statistics for file ' + cfile.name)
    lines.append('~' * 80)

    lines.append(proofobligation_stats_tostring(tagpporesults,tagsporesults))
    
    return '\n'.join(lines)

def file_global_assumptions_tostring(cfile):
    lines = []
    lines.append('\nGlobal assumptions')
    lines.append(('-' * 80))
    polines = set([])
    ppos = cfile.get_ppos()
    spos = cfile.get_spos()
    for po in ppos + spos:
        for a in po.get_global_assumptions():
            polines.add(str(a))
    return '\n'.join(sorted(lines) + sorted(list(polines)))

def file_postcondition_assumptions_tostring(cfile):
    lines = []
    lines.append('\nPostcondition assumptions')
    lines.append(('-' * 80))
    polines = set([])
    ppos = cfile.get_ppos()
    spos = cfile.get_spos()
    for po in ppos + spos:
        for a in po.get_postcondition_assumptions():
            polines.add(str(a))
    return '\n'.join(lines + sorted(list(polines)))

def function_proofobligation_stats_tostring(cfunction,extradsmethods=[]):
    lines = []
    ppos = cfunction.get_ppos()
    spos = cfunction.get_spos()
    tagpporesults = get_tag_method_count(ppos,extradsmethods=extradsmethods)
    tagsporesults = get_tag_method_count(spos,extradsmethods=extradsmethods)

    lines.append('\n\nProof Obligation Statistics for function ' + cfunction.name)
    lines.append('~' * 80)

    lines.append(proofobligation_stats_tostring(tagpporesults,tagsporesults))
    return '\n'.join(lines)


def make_po_tag_dict(pos,pofilter=lambda po:True):
    '''Create a predicate tag dictionary from a a list of proof obligations.

    Args:
      pos: list of proof obligations (primary or supporting)
      pofilter: predicate that specifies which proof obligations to include
    Returns:
      dictionary that organizes the proof obligations by predicate tag
    '''
    result = {}
    for po in pos:
        if pofilter(po):
            tag = po.get_predicate_tag()
            if not tag in result: result[tag] = []
            result[tag].append(po)
    return result

def make_po_file_function_dict(pos,filefilter=lambda f:True):
    '''Create a file, function dictionary from a list of proof obligations.

    Args:
      pos: list of proof obligations (primary or supporting)
      filefilter: predicate that specifies which c files to include
    Returns:
      dictionary that organizes the proof obligations by c file
    '''
    result = {}
    for po in pos:
        cfile = po.cfile.name
        if filefilter(cfile):
            if not cfile in result: result[cfile] = {}
            cfun = po.cfun.name
            if not cfun in result[cfile]: result[cfile][cfun] = []
            result[cfile][cfun].append(po)
    return result
        
def tag_file_function_pos_tostring(pos,filefilter=lambda f:True,pofilter=lambda po:True):
    lines = []
    tagdict = make_po_tag_dict(pos,pofilter=pofilter)
    for tag in sorted(tagdict):
        fundict = make_po_file_function_dict(tagdict[tag],filefilter=filefilter)
        lines.append('\n\n' + tag + '\n' + ('-' * 80))
        for f in sorted(fundict):
            lines.append('\n  File: ' + f)
            for ff in sorted(fundict[f]):
                lines.append('    Function: ' + ff)
                for po in sorted(fundict[f][ff],key=lambda po:po.get_line()):
                    invd = po.cfun.invd
                    lines.append((' ' * 6) + str(po))
                    if po.is_closed():
                        lines.append((' ' * 14) + str(po.explanation))

                    if po.has_diagnostic():
                        amsgs = po.diagnostic.amsgs
                        if len(amsgs) > 0:
                            for arg in sorted(amsgs):
                                for s in sorted(amsgs[arg]):
                                    lines.append((' ' * 14) + s)
                        msgs = po.diagnostic.msgs
                        if len(msgs) > 0:
                            lines.append((' ' * 8) + ' ---> ' + msgs[0])
                            for s in msgs[1:]:
                                lines.append((' ' * 14) + s)
                            lines.append(' ')
                        keys = po.diagnostic.get_argument_indices()
                        for k in keys:
                            invids = po.diagnostic.get_invariant_ids(k)
                            for id in invids:
                                lines.append((' ' * 14) + str(k) + ': ' +
                                                 str(invd.get_invariant_fact(id).get_non_relational_value()))
                        lines.append(' ')

    return '\n'.join(lines)

def get_totals_from_tagtotals(tagtotals):
    totals = {}
    dsmethods = get_dsmethods([])
    for dm in dsmethods:
        totals[dm] = sum([ tagtotals[t][dm] for t in tagtotals if dm in tagtotals[t] ])
    return totals

def totals_to_string(tagtotals,absolute=True,totals=True):
    lines = []
    rhlen = max( [ max ([ len(t) for t in tagtotals ]), 12 ])
    header1 = ''
    dsmethods = get_dsmethods([])
    width = 10
    lines.append(get_dsmethod_header(rhlen,dsmethods,header1=header1) + '    %closed')
    barlen = 80 + rhlen
    lines.append('-' * barlen)
    for t in sorted(tagtotals):
        r = [ tagtotals[t][dm] for dm in dsmethods ]
        rsum = sum(r)
        if rsum == 0: continue
        tagopenpct = (1.0 - (float(tagtotals[t]['open'])/float(rsum))) * 100.0
        tagopenpct = str('{:.1f}'.format(tagopenpct))
        if absolute:
            lines.append(t.ljust(rhlen) + ''.join([str(x).rjust(width) for x in r])
                            + str(sum(r)).rjust(10) + tagopenpct.rjust(width))
        else:
            lines.append(t.ljust(rhlen)
                             + ''.join([str('{:.2f}'.format(float(x)/float(rsum) * 100.0)).rjust(width)
                                            for x in r]))
    if totals:
        lines.append('-' * barlen )
        totals = get_totals_from_tagtotals(tagtotals)
        totalcount = sum(totals.values())
        if totalcount > 0:
            tagopenpct = (1.0 - (float(totals['open'])/float(totalcount))) * 100.0
            tagopenpct = str('{:.1f}'.format(tagopenpct))
            if absolute:
                lines.append('total'.ljust(rhlen) + ''.join([str(totals[dm]).rjust(width) for dm in dsmethods])
                                + str(totalcount).rjust(10) + tagopenpct.rjust(width))
            scale = float(totalcount)/100.0
            lines.append('percent'.ljust(rhlen) +
                            ''.join([str('{:.2f}'.format(float(totals[dm])/scale)).rjust(width)
                                        for dm in dsmethods]))
    return lines

def totals_to_presentation_string(ppototals,spototals,projectstats,absolute=True,totals=True):
    lines = []
    rhlen = max( [ max([ len(t) for t in ppototals ]), 12 ])
    header1 = ''
    dsmethods = get_dsmethods([])
    lines.append(' '.rjust(rhlen) + 'line count'.rjust(10)
                     + "total ppo's".rjust(15) + '%closed'.rjust(10)
                     + "total spo'".rjust(15) + '%closed'.rjust(10))
    barlen = 64 + rhlen
    lines.append('-' * barlen)
    for t in sorted(ppototals):
        (lc,_,_) = projectstats[t]
        rppo = [ ppototals[t][dm] for dm in dsmethods ]
        rspo = [ spototals[t][dm] for dm in dsmethods ]
        rpposum = sum(rppo)
        rsposum = sum(rspo)
        if rpposum == 0: continue
        ppoopenpct = (1.0 - (float(ppototals[t]['open'])/float(rpposum))) * 100.0
        ppoopenpct = str('{:.1f}'.format(ppoopenpct))
        if rsposum == 0: continue
        spoopenpct = (1.0 - (float(spototals[t]['open'])/float(rsposum))) * 100.0
        spoopenpct = str('{:.1f}'.format(spoopenpct))
        
        if absolute:
            lines.append(t.ljust(rhlen) + str(lc).rjust(10)
                             + str(sum(rppo)).rjust(15) + ppoopenpct.rjust(10)
                             + str(sum(rspo)).rjust(15) + spoopenpct.rjust(10))
            '''
            lines.append(t.ljust(rhlen) + ''.join([str(x).rjust(8) for x in r])
                            + str(sum(r)).rjust(10) + ppoopenpct.rjust(8))
            '''
        else:
            lines.append(t.ljust(rhlen)
                             + ''.join([str('{:.2f}'.format(float(x)/float(rsum) * 100.0)).rjust(8)
                                            for x in r]))
    if totals:
        lines.append('-' * barlen )
        lctotal = sum( [ projectstats[t][0] for t in projectstats ])
        dmppototals = {}
        dmspototals = {}
        for dm in dsmethods:
            dmppototals[dm] = sum([ ppototals[t][dm] for t in ppototals ])
            dmspototals[dm] = sum([ spototals[t][dm] for t in spototals ])
        ppototalcount = sum(dmppototals.values())
        spototalcount = sum(dmspototals.values())
        if ppototalcount > 0:
            ppotagopenpct = (1.0 - (float(dmppototals['open'])/float(ppototalcount))) * 100.0
            ppotagopenpct = str('{:.1f}'.format(ppotagopenpct))
            spotagopenpct = (1.0 - (float(dmspototals['open'])/float(spototalcount))) * 100.0
            spotagopenpct = str('{:.1f}'.format(spotagopenpct))
            if absolute:
                lines.append('total'.ljust(rhlen)
                                 + str(lctotal).rjust(10)
                                 + str(ppototalcount).rjust(15)
                                 + ppotagopenpct.rjust(10)
                                 + str(spototalcount).rjust(15)
                                 + spotagopenpct.rjust(10))
            '''
            scale = float(totalcount)/100.0
            lines.append('percent'.ljust(rhlen) +
                            ''.join([str('{:.2f}'.format(float(totals[dm])/scale)).rjust(8)
                                        for dm in dsmethods]))
            '''
    return lines
