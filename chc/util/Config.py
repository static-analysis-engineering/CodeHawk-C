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

import os

if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ConfigLocal.py")):
    import chc.util.ConfigLocal as ConfigLocal
    localconfig = True


class Config(object):

    def __init__(self):
        # platform settings
        if os.uname()[0] == 'Linux': self.platform = 'linux'
        elif os.uname()[0] == 'Darwin': self.platform = 'mac'

        # general settings
        self.utildir = os.path.dirname(os.path.abspath(__file__)) 
        self.rootdir = os.path.dirname(self.utildir)
        self.bindir = os.path.join(self.rootdir,'bin')
        self.topdir = os.path.dirname(self.rootdir)
        self.testdir = os.path.join(self.topdir,'tests')
        summariesdir = os.path.join(self.rootdir,'summaries')
        self.summaries = os.path.join(summariesdir,'cchsummaries.jar')
        self.binariesdir = os.path.join(self.bindir,'binaries')
        self.cparser = os.path.join(self.binariesdir,'parseFile_linux')
        self.canalyzer = os.path.join(self.binariesdir,'chc_analyze_linux')
        self.chc_gui = os.path.join(self.binariesdir,'chc_gui_linux')
        self.bear = None
        self.libear = None
        if self.platform == 'mac':
            self.cparser = os.path.join(self.binariesdir,'parseFile_mac')
            self.canalyzer = os.path.join(self.binariesdir,'chc_analyze_mac')
            self.chc_gui = os.path.join(self.binariesdir,'chch_gui_mac')

        # tests included in this repository
        self.kendradir = os.path.join(self.testdir,'kendra')
        self.zitserdir = os.path.join(self.testdir,'zitser')

        '''test cases'''
        self.projects = {}
        self.myprojects = {}
        self.mycfiles = {}

        # personalization
        if localconfig: ConfigLocal.getLocals(self)

    def __str__(self):
        plen = 20
        lines = []
        parserfound = ' (found)' if os.path.isfile(self.cparser) else ' (not found)'
        analyzerfound = ' (found)' if os.path.isfile(self.canalyzer) else ' (not found)'
        summariesfound = ' (found)' if os.path.isfile(self.summaries) else  ' (not found)'
        lines.append('Analyzer configuration:')
        lines.append('-----------------------')
        lines.append('  platform : ' + self.platform)        
        lines.append('  parser   : ' + self.cparser +  parserfound)
        lines.append('  analyzer : ' + self.canalyzer + analyzerfound)
        if not self.bear is None:
            lines.append('bear'.ljust(plen) + ': ' + self.bear)
            lines.append('libear'.ljust(plen) + ': ' + self.libear)
        lines.append('  summaries: ' + self.summaries + summariesfound)
        
        lines.append('\nTest directories')
        lines.append('-' * 64)
        lines.append('test directory'.ljust(plen) + ': ' + self.testdir)
        lines.append('projects'.ljust(plen) + ':')
        if len(self.myprojects) > 0:
            lines.append('my projects'.ljust(plen) + ':')
            for (p,d) in sorted(self.myprojects.items()):
                lines.append(' '.ljust(3) + str(p).ljust(12) + ': ' + str(d))
        lines.append('-' * 64)
        return '\n'.join(lines)


if __name__ == '__main__':

    print(Config())
