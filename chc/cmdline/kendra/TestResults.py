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

import os

class TestResults(object):

    def __init__(self,testsetref):
        self.testsetref = testsetref      # TestSetRef
        self.cfiles = []
        self.parseresults = {}
        self.xfileresults = {}
        self.pporesults = {}
        self.pevresults = {}
        self.sporesults = {}
        self.sevresults = {}
        self._initialize()
        self.includesparsing = False
        self.includesppos = False
        self.includespevs = False
        self.includesspos = False
        self.includessevs = False

    def set_parsing(self): self.includesparsing = True

    def set_ppos(self): self.includesppos = True

    def set_pevs(self): self.includespevs = True

    def set_spos(self): self.includesspos = True

    def set_sevs(self): self.includessevs = True

    def add_parse_error(self,cfilename,msg):
        self.parseresults[cfilename] = 'error: ' + msg

    def add_parse_success(self,cfilename):
        self.parseresults[cfilename] = 'ok'

    def add_xcfile_error(self,cfilename):
        self.xfileresults[cfilename]['xcfile'] = 'missing'

    def add_xcfile_success(self,cfilename):
        self.xfileresults[cfilename]['xcfile'] = 'ok'

    def add_xffile_error(self,cfilename,cfun):
        self.xfileresults[cfilename]['xffiles'][cfun] = 'missing'

    def add_xffile_success(self,cfilename,cfun):
        self.xfileresults[cfilename]['xffiles'][cfun] = 'ok'

    def add_ppo_count_error(self,cfilename,cfun,lenppos,lenrefppos):
        discrepancy = lenrefppos - lenppos
        if discrepancy > 0:
            msg = (str(discrepancy) + ' ppos are missing')
        else:
            msg = (str(-discrepancy) + ' additional ppos')
                
        self.pporesults[cfilename][cfun]['count'] = 'error: ' + msg

    def add_spo_count_error(self,cfilename,cfun,lenspos,lenrefspos):
        discrepancy = lenrefspos - lenspos
        if discrepancy > 0:
            msg = (str(discrepancy) + ' spos are missing')
        else:
            msg = (str(-discrepancy) + ' additional spos')

        self.sporesults[cfilename][cfun]['count'] = 'error: ' + msg

    def add_ppo_count_success(self,cfilename,cfun):
        self.pporesults[cfilename][cfun]['count'] = 'ok'

    def add_spo_count_success(self,cfilename,cfun):
        self.sporesults[cfilename][cfun]['count'] = 'ok'

    def add_missing_ppo(self,cfilename,cfun,context,predicate):
        self.pporesults[cfilename][cfun]['missingpredicates'].append((context,predicate))

    def add_missing_spo(self,cfilename,cfun,context,hashstr):
        self.sporesults[cfilename][cfun]['missing'].append((context,hashstr))

    def add_pev_discrepancy(self,cfilename,cfun,ppo,status):
        hasmultiple = cfun.has_multiple(ppo.get_line(),ppo.get_predicate())
        self.pevresults[cfilename][cfun.name]['discrepancies'].append((
            ppo,status,hasmultiple))

    def add_sev_discrepancy(self,cfilename,cfun,spo,status):
        self.sevresults[cfilename][cfun.name]['discrepancies'].append((spo,status,False))

    def get_line_summary(self):
        name = os.path.basename(self.testsetref.specfilename)[:-5]
        parsing = ''
        ppogen = ''
        spogen = ''
        pporesult = ''
        sporesult = ''
        for cfile in self.cfiles:
            cfilename = cfile.name
            cfunctions = cfile.get_functions()
            parsingok = True
            ppogenok = True
            spogenok = True
            pporesultok = True
            sporesultok = True
            if len(cfunctions) > 0:
                for cfun in cfunctions:
                    fname = cfun.name
                    if self.includesparsing:
                        if self.xfileresults[cfilename]['xffiles'][fname] != 'ok':
                            parsingok = False
                    if self.includesppos:
                        funresults = self.pporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missingpredicates']
                        if count != 'ok' or len(missing) > 0:
                            ppogenok = False
                    if self.includesspos:
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missing']
                        if count != 'ok' or len(missing) > 0:
                            spogenok = False
                    if self.includespevs:
                        pevs = self.pevresults[cfilename][fname]['discrepancies']
                        if len(pevs) > 0:
                            pporesultok = False
                    if self.includessevs:
                        sevs = self.sevresults[cfilename][fname]['discrepancies']
                        if len(sevs) > 0:
                            sporesultok = False
                def pr(result): return '=' if result else 'X'
                parsing += pr(parsingok)
                ppogen += pr(ppogenok)
                spogen += pr(spogenok)
                pporesult += pr(pporesultok)
                sporesult += pr(sporesultok)
        return (name.ljust(10) + '[  ' + parsing.ljust(6) + ppogen.ljust(6)
                    + spogen.ljust(6) + pporesult.ljust(6)
                    + sporesult.ljust(6) + ']')


    def get_summary(self):
        lines = []
        header = ('File'.ljust(10) + 'Parsing'.center(15) + 'PPO Gen'.center(15)
                      + 'SPO Gen'.center(15) + 'PPO Results'.center(15)
                      + 'SPO Results'.center(15))
        lines.append(header)
        lines.append('-' * 85)
        for cfile in self.cfiles:
            cfilename = cfile.name
            cfunctions = cfile.get_functions()
            parsingok = ''
            pposok = 'ok'
            sposok = ''
            pevsok = 'ok'
            sevsok = ''
            if len(cfunctions) > 0:
                for cfun in cfunctions:
                    fname = cfun.name
                    if self.includesparsing:
                        if self.xfileresults[cfilename]['xffiles'][fname] != 'ok':
                            parsingok = 'bad'
                    if self.includesppos:
                        funresults = self.pporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missingpredicates']
                        if count != 'ok' or len(missing) > 0:
                            pposok = 'bad'
                    if self.includesspos:
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missing']
                        if count != 'ok' or len(missing) > 0 or sposok == 'bad':
                            sposok = 'bad'
                        else:
                            sposok = 'ok'
                    if self.includespevs:
                        pevs = self.pevresults[cfilename][fname]['discrepancies']
                        if len(pevs) != 0 or pevsok == 'bad':
                            pevsok = 'bad'
                    if self.includessevs:
                        sevs = self.sevresults[cfilename][fname]['discrepancies']
                        if len(sevs) != 0 or sevsok == 'bad':
                            sevsok = 'bad'
                        else:
                            sevsok = 'ok'

            if self.includesparsing:
                if self.parseresults[cfilename] != 'ok':
                    parsingok = 'bad'
                if self.xfileresults[cfilename]['xcfile'] != 'ok':
                    parsingok = 'bad'
                if parsingok != 'bad':
                    parsingok = 'ok'

            lines.append(cfilename.ljust(10) + parsingok.center(15) +  pposok.center(15)
                             + sposok.center(15) + pevsok.center(15) + sevsok.center(15))
        return '\n'.join(lines)

    def __str__(self):
        lines = []
        if self.includesparsing:
            lines.append('\nCheck parsing results:\n' + ('-' * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append(' ')
                lines.append(cfilename)
                lines.append('  parse : ' + self.parseresults[cfilename])
                lines.append('  xcfile: ' + self.xfileresults[cfilename]['xcfile'])
                cfunctions = cfile.get_functions()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        lines.append('    ' + fname + ': ' +
                                    self.xfileresults[cfilename]['xffiles'][fname])
        if self.includesppos:
            lines.append('\nCheck primary proof obligations:\n' + ('-' * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append('')
                lines.append(cfilename)
                cfunctions = cfile.get_functions()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        funresults = self.pporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missingpredicates']
                        if count == 'ok' and len(missing) == 0:
                            lines.append('    ' + fname + ': ok')
                        else:
                            lines.append('    ' + fname)
                            if count != 'ok':
                                lines.append('      count: ' + count)
                        for (ctxt,p) in missing:
                            lines.append('        (' + str(ctxt) + ')' + ': ' + p)

        if self.includesspos:
            lines.append('\nCheck secondary proof obligations:\n' + ('-' * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append('')
                lines.append(cfilename)
                cfunctions = cfile.get_functions()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        funresults = self.sporesults[cfilename][fname]
                        count = funresults['count']
                        missing = funresults['missing']
                        if count == 'ok' and len(missing) == 0:
                            lines.append('    ' + fname + ': ok')
                        else:
                            lines.append('    ' + fname)
                            if count != 'ok':
                                lines.append('     count: ' + count)
                        for (ctxt,hashstr) in missing:
                            lines.append('      ' + str(ctxt) + ': ' + str(hashstr))

        if self.includespevs:
            lines.append('\nCheck primary proof results:\n' + ('-' * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append('')
                lines.append(cfilename)
                cfunctions = cfile.get_functions()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        pevs = self.pevresults[cfilename][fname]['discrepancies']
                        if len(pevs) == 0:
                            lines.append('    ' + fname + ': ok')
                        else:
                            lines.append('    ' + fname)
                            for (ppo,status,hasmultiple) in pevs:
                                ctxt = ppo.get_context_string() if hasmultiple else ''
                                lines.append(
                                    '    ' + str(ppo.get_line()).rjust(4) + ' ' +
                                    ppo.get_predicate().ljust(20) +
                                    '  found:' + status.ljust(11) +
                                    '  expected:' + ppo.get_status().ljust(11) + '  ' + ctxt)

        if self.includessevs:
            lines.append('\nCheck secondary proof results:\n' + ('-' * 80))
            for cfile in self.cfiles:
                cfilename = cfile.name
                lines.append('')
                lines.append(cfilename)
                cfunctions = cfile.get_functions()
                if len(cfunctions) > 0:
                    for cfun in cfunctions:
                        fname = cfun.name
                        sevs = self.sevresults[cfilename][fname]['discrepancies']
                        if len(sevs) == 0:
                            lines.append('    ' + fname + ': ok')
                        else:
                            lines.append('    ' + fname)
                            for (spo,status,hasmultiple) in sevs:
                                ctxt = spo.get_cfg_context_string() if hasmultiple else ''
                                lines.append(
                                    '    ' + str(spo.get_line()).rjust(4) + ' ' +
                                    spo.get_predicate().ljust(20) +
                                    '  found:' + status.ljust(11) +
                                    '  expected:' + spo.get_status().ljust(11) + '  ' + ctxt)
        return '\n'.join(lines)
            
    def _initialize(self):
        self.cfiles = self.testsetref.get_cfiles()
        for cfile in self.cfiles:
            f = cfile.name
            self.parseresults[f] = 'none'
            self.xfileresults[f] = {}
            self.xfileresults[f]['xcfile'] = 'none'
            self.xfileresults[f]['xffiles'] = {}
            self.pporesults[f] = {}
            self.pevresults[f] = {}
            self.sporesults[f] = {}
            self.sevresults[f] = {}
            for cfun in cfile.get_functions():
                ff = cfun.name
                self.pporesults[f][ff] = {}
                self.pporesults[f][ff]['count'] = 'none'
                self.pporesults[f][ff]['missingpredicates'] = []
                self.pevresults[f][ff] = {}
                self.pevresults[f][ff]['discrepancies'] = []

                self.sporesults[f][ff] = {}
                self.sporesults[f][ff]['count'] = 'none'
                self.sporesults[f][ff]['missing'] = []
                self.sevresults[f][ff] = {}
                self.sevresults[f][ff]['discrepancies'] = []
            
