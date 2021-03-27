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
from typing import Dict

if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ConfigLocal.py")):
    import chc.util.ConfigLocal as ConfigLocal
    localconfig = True
else:
    localconfig = False


class Config(object):

    def __init__(self) -> None:
        # platform settings
        if os.uname()[0] == 'Linux': self.platform = 'linux'
        elif os.uname()[0] == 'Darwin': self.platform = 'macOS'

        # general settings
        self.utildir = os.path.dirname(os.path.abspath(__file__)) 
        self.rootdir = os.path.dirname(self.utildir)
        self.bindir = os.path.join(self.rootdir,'bin')
        self.topdir = os.path.dirname(self.rootdir)
        self.testdir = os.path.join(self.topdir,'tests')

        # parser and analyzer executables
        if self.platform == 'linux':
            self.linuxdir = os.path.join(self.bindir,'linux')
            self.cparser = os.path.join(self.linuxdir,'parseFile')
            self.canalyzer = os.path.join(self.linuxdir,'canalyzer')
            self.chc_gui = None

        if self.platform == 'macOS':
            self.macOSdir = os.path.join(self.bindir,'macOS')
            self.cparser = os.path.join(self.macOSdir,'parseFile')
            self.canalyzer = os.path.join(self.macOSdir,'canalyzer')
            self.chc_gui = None

        # bear: a tool that generates a compilation database in json
        self.bear = None
        self.libear = None

        # summaries
        summariesdir = os.path.join(self.rootdir,'summaries')
        self.summaries = os.path.join(summariesdir,'cchsummaries.jar')

        # tests included in this repository
        self.kendradir = os.path.join(self.testdir,'kendra')
        self.zitserdir = os.path.join(self.testdir,'zitser')
        self.libcsummarytestdir = os.path.join(self.testdir,'libcsummaries')

        # analysis targets
        self.name_separator = ':'
        self.targets: Dict[str, str] = {}

        # personalization
        if localconfig: ConfigLocal.getLocals(self)

    def __str__(self) -> str:
        lines = []
        parserfound = ' (found)' if os.path.isfile(self.cparser) else ' (not found)'
        analyzerfound = ' (found)' if os.path.isfile(self.canalyzer) else ' (not found)'
        summariesfound = ' (found)' if os.path.isfile(self.summaries) else  ' (not found)'
        lines.append('=' * 80)
        lines.append('Analyzer configuration:')
        lines.append('-----------------------')
        lines.append('  platform : ' + self.platform)        
        lines.append('  parser   : ' + self.cparser +  parserfound)
        lines.append('  analyzer : ' + self.canalyzer + analyzerfound)
        if not self.chc_gui is None:
            chcguifound = ' (found)' if os.path.isfile(self.chc_gui) else ' (not found)'
            lines.append('  gui      : ' + self.chc_gui + chcguifound)
        if not self.bear is None:
            lines.append('bear  :' + self.bear)
            lines.append('libear:' + self.libear)
        lines.append('\n  summaries: ' + self.summaries + summariesfound)
        
        lines.append('\nTest directories')
        lines.append('-' * 64)
        lines.append('  test directory:' + self.testdir)
        lines.append('-' * 80)

        if len(self.targets) > 0:
            lines.append('\nRegistered analysis targets')
            lines.append('-' * 80)
            for group in self.targets:
                lines.append('  ' + group + ': ' + self.targets[group])
            lines.append('-' * 80)
        return '\n'.join(lines)



if __name__ == '__main__':

    print(Config())
