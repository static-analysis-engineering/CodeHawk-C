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

import multiprocessing

import subprocess, os, shutil

import chc.util.fileutil as UF
from chc.util.Config import Config
# from chc.invariants.CGlobalInvariants import CGlobalInvariants

class AnalysisManager(object):
    """Provide the interface to the KT Advance (ocaml) analyzer."""

    def __init__(self,capp,wordsize=0,unreachability=False,
                     thirdpartysummaries=[],nofilter=True,
                     verbose=True):
        """Initialize the analyzer location and target file location.

        Args:
            capp (CApplication): application entry point

        Keyword args:
            wordsize (int): architecture wordsize (0,16,32,64) (default 0 (unspecified))
            unreachability (bool): use unreachability as justification to discharge 
                                   (default False)
            thirdpartysummaries (string list): names of function summary jars
            verbose (bool): display analyzer output (default True)
            nofilter (bool): don't remove functions with absolute filename (default True)
        """

        self.capp = capp
        self.contractpath = capp.contractpath
        self.config = Config()
        self.chsummaries = self.config.summaries
        self.path = self.capp.path
        self.canalyzer = self.config.canalyzer
        self.gui = self.config.chc_gui
        self.nofilter = nofilter
        self.wordsize = wordsize
        self.thirdpartysummaries = thirdpartysummaries
        self.unreachability = unreachability 
        self.verbose = verbose

    def reset(self):
        """Remove all file- and function-level files produced by the analysis."""
        
        def remove(f):
            if os.path.isfile(f): os.remove(f)
        def g(fi):
            cfiledir = UF.get_cfile_directory(self.path,fi.name)
            if os.path.isdir(cfiledir):
                for f in os.listdir(cfiledir):
                    if (len(f) > 10
                            and (f[-8:-4] in [ '_api', '_ppo', '_spo', '_pod' ]
                                     or f[-9:-4] in [ '_invs', '_vars' ])):
                        os.remove(os.path.join(cfiledir,f))
            remove(UF.get_cfile_predicate_dictionaryname(self.capp.path,fi.name))
            remove(UF.get_cfile_interface_dictionaryname(self.capp.path,fi.name))
            remove(UF.get_cfile_assignment_dictionaryname(self.capp.path,fi.name))
            remove(UF.get_cxreffile_filename(self.capp.path,fi.name))
            remove(UF.get_cfile_contexttablename(self.capp.path,fi.name))
        self.capp.iter_files(g)
        remove(UF.get_global_definitions_filename(self.capp.path))


    def reset_logfiles(self):
        """Remove all log files from semantics directory."""

        def g(fi):
            logfiledir = UF.get_cfile_logfiles_directory(self.path,fi.name)
            if os.path.isdir(logfiledir):
                for f in os.listdir(logfiledir):
                    if (f.endswith('chlog')
                            or f.endswith('infolog')
                            or f.endswith('errorlog')):
                        os.remove(os.path.join(logfiledir,f))
        self.capp.iter_files(g)

    def reset_tables(self, cfilename):
        """Reload dictionaries from file (to get updated data from analyzer)."""

        cfile = self.capp.get_file(cfilename)
        cfile.reinitialize_tables()
        cfile.reload_ppos()
        cfile.reload_spos()

    def _execute_cmd(self, CMD):
        try:
            print(CMD)
            result = subprocess.check_output(CMD)
            print(result.decode('utf-8'))
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def _create_file_primary_proofobligations_cmd_partial(self):
        cmd = [ self.canalyzer, '-summaries', self.chsummaries,
                    '-command', 'primary' ]
        if not (self.thirdpartysummaries is None):
            for s in self.thirdpartysummaries:
                cmd.extend(['-summaries',s])
        if not (self.contractpath is None):
            cmd.extend(['-contractpath',self.contractpath])

        if self.nofilter: cmd.append('-nofilter')
        if self.wordsize > 0: cmd.extend(['-wordsize',str(self.wordsize)])
        cmd.append(self.path)
        cmd.append('-cfile')
        return cmd

    def rungui(self,name,outputpath=None):
        semdir = os.path.dirname(self.path)
        analysisdir = os.path.dirname(semdir)
        if outputpath is None:
            outputpath = analysisdir
        cmd = [ self.gui, '-summaries', self.chsummaries,
                    '-output', outputpath,
                    '-name', name,
                    '-xpm', self.config.utildir,
                    '-analysisdir', analysisdir, '-contractpath',
                    self.contractpath ]
        print(cmd)
        try:
            result = subprocess.call(cmd,cwd=self.path,stdout=open(os.devnull,'w'),
                                        stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def create_file_primary_proofobligations(self,cfilename):
        """Call analyzer to create primary proof obligations for a single application file."""

        try:
            cmd = self._create_file_primary_proofobligations_cmd_partial()
            cmd.append(cfilename)
            if self.verbose:
                print('Creating primary proof obligations for ' + cfilename)
                print(str(cmd))
                result = subprocess.call(cmd,cwd=self.path,stderr=subprocess.STDOUT)
                print('\nResult: ' + str(result))
                self.capp.get_file(cfilename).predicatedictionary.initialize()
            else:
                result = subprocess.call(cmd,cwd=self.path,stdout=open(os.devnull, 'w'),
                                             stderr=subprocess.STDOUT)
            if result != 0:
                print('Error in creating primary proof obligations')
                exit(1)
            cfile = self.capp.get_file(cfilename)
            cfile.reinitialize_tables()
            cfile.reload_ppos()
            cfile.reload_spos()
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def create_app_primary_proofobligations(self, processes=1):
        """Call analyzer to create primary proof obligations for all application files."""

        if processes > 1:
            def f(cfile):
                cmd = self._create_file_primary_proofobligations_cmd_partial()
                cmd.append(cfile)
                self._execute_cmd(cmd)
            self.capp.iter_filenames_parallel(f, processes)
        else:
            def f(cfile):
                self.create_file_primary_proofobligations(cfile)
            self.capp.iter_filenames(f)

    def _generate_and_check_file_cmd_partial(self, domains):
        cmd = [ self.canalyzer, '-summaries', self.chsummaries,
                    '-command', 'generate_and_check',
                    '-domains', domains ]
        if not (self.thirdpartysummaries is None):
            for s in self.thirdpartysummaries:
                cmd.extend(['-summaries',s])
        if not (self.contractpath is None):
            cmd.extend(['-contractpath',self.contractpath])
        if self.nofilter: cmd.append('-nofilter')
        if self.wordsize > 0: cmd.extend(['-wordsize',str(self.wordsize)])
        if self.unreachability: cmd.append('-unreachability')
        if self.verbose: cmd.append('-verbose')
        cmd.append(self.path)
        cmd.append('-cfile')
        return cmd

    def generate_and_check_file(self,cfilename,domains):
        """Generate invariants and check proof obligations for a single file."""

        try:
            cmd = self._generate_and_check_file_cmd_partial(domains)
            cmd.append(cfilename)
            if self.verbose: 
                print('Generating invariants and checking proof obligations for '
                          + cfilename)
                print(cmd)
                result = subprocess.call(cmd,cwd=self.path,stderr=subprocess.STDOUT)
                print('\nResult: ' + str(result))
            else:
                result = subprocess.call(cmd,cwd=self.path,stdout=open(os.devnull,'w'),
                                             stderr=subprocess.STDOUT)
            if result != 0:
                print('Error in generating invariants or checking proof obligations')
                exit(1)
        except subprocess.CalledProcessError as args:
            print(args.output)
            print(args)
            exit(1)

    def generate_and_check_app(self, domains, processes=1):
        """Generate invariants and check proof obligations for application."""

        if processes > 1:
            def f(cfile):
                cmd = self._generate_and_check_file_cmd_partial(domains)
                cmd.append(cfile)
                self._execute_cmd(cmd)
            self.capp.iter_filenames_parallel(f, processes)
        else:
            def f(cfile):
                self.generate_and_check_file(cfile,domains)
            self.capp.iter_filenames(f)
        self.capp.iter_filenames(self.reset_tables)

            
if __name__ == '__main__':

    pass
