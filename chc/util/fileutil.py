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

import calendar
import json
import os
import subprocess
import shutil
import time
import xml.etree.ElementTree as ET

import chc.util.xmlutil as UX

from chc.util.Config import Config

class CHError(Exception):

    def wrap(self):
        lines = []
        lines.append('*' * 80)
        lines.append(self.__str__())
        lines.append('*' * 80)
        return '\n'.join(lines)

class CHCError(CHError):

    def __init__(self,msg):
        CHError.__init__(self,msg)

class CHCParserNotFoundError(CHCError):

    def __init__(self,location):
        CHCError.__init__(self,'C Parser executable not found at ' + location)

class CHCAnalyzerNotFoundError(CHCError):

    def __init__(self,location):
        CHCError.__init__(self,'C Analyzer executable not found at ' + location)

class CHCFileNotFoundError(CHCError):

    def __init__(self,filename):
        CHCError.__init__(self,'File ' + filename + ' not found')
        self.filename =  filename

class CHCSingleCFileNotFoundError(CHCError):

    def __init__(self,filenames):
        CHCError.__init__(self,'Requested file not found')
        self.filenames = filenames

    def __str__(self):
        lines = []
        lines.append('Requested file not found; filenames available: ')
        iines.append('-' * 80)
        for n in self.filenames:
            lines.append('  ' +  n)
        return '\n'.join(lines)

class CHCDirectoryNotFoundError(CHCError):

    def __init__(self,dirname):
        CHCError.__init__(self,'Directory ' + dirname + ' not found')
        self.dirname = dirname

class CHCArtifactsNotFoundError(CHCError):

    def __init__(self,path):
        CHCError.__init__(self,'Artifacts directory not found in ' + path)
        self.path = path

    def __str__(self):
        return ('Directory ' + path + ' is expected to have a directory named '
                    + ' chcartifacts or ktadvance (legacy)')


def get_xnode(filename,rootnode,desc,show=True):
    if os.path.isfile(filename):
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            return root.find(rootnode)
        except ET.ParseError as args:
            print('Problem in ' + filename)
            print(args)
    else:
        if show: print(desc + ' ' + filename + ' not found')

def create_backup_file(filename):
    if os.path.isfile(filename):
        timestamp = calendar.timegm(time.gmtime())
        backupfilename = filename + '_' + str(timestamp)
        shutil.copy(filename,backupfilename)

# ------------------------------------------------------------------------------

def get_chc_artifacts_path(path):
    dirname = os.path.join(path,'chcartifacts')
    if os.path.isdir(dirname):
        return dirname
    dirname = os.path.join(path,'ktadvance')    # legacy name
    if os.path.isdir(dirname):
        return dirname
    raise CHCArtifactsNotFoundError(path)

def get_targetfiles_filename(path):
    return os.path.join(path,'target_files.xml')

def get_functionindex_filename(path):
    return os.path.join(path,'functionindex.json')

def save_functionindex(path,d):
    filename = get_functionindex_filename(path)
    with open(filename,'w') as fp:
        json.dump(d,fp)

def load_functionindex(path):
    filename = get_functionindex_filename(path)
    if os.path.isfile(filename):
        with open(filename,'r') as fp:
            return json.load(fp)
    return {}

def get_targetfiles_xnode(path):
    filename = get_targetfiles_filename(path)
    return get_xnode(filename,'c-files','File that holds the names of source files')

def get_targetfiles_list(path):
    result = []
    node = get_targetfiles_xnode(path)
    if not node is None:
        for f in node.findall('c-file'):
            lines.append((f.get('id'),f.get('name')))
    return result

def get_global_definitions_filename(path):
    return os.path.join(path,'globaldefinitions.xml')

def archive_project_summary_results(path):
    if os.path.isdir(path):
        filename = os.path.join(path,'summaryresults.json')
        if os.path.isfile(filename):
            with open(filename) as fp:
                d = json.load(fp)
                if 'timestamp' in d:
                    dtime = d['timestamp']
                else:
                    dtime = 0
                newfilename = 'summaryresults_' + str(dtime) + '.json'
                newfilename = os.path.join(path,newfilename)
                with open(newfilename,'w') as fp:
                    json.dump(d,fp)
                

def save_project_summary_results(path,d):
    archive_project_summary_results(path)
    with open(os.path.join(path,'summaryresults.json'),'w') as fp:
        json.dump(d,fp)

def save_project_summary_results_as_xml(path, d):
    xml_file = os.path.join(path, 'summaryresults.xml')
    tags = d['tagresults']
    ppos = tags['ppos']
    spos = tags['spos']
    files = d['fileresults'] 
    file_ppos = files['ppos']
    file_spos = files['spos']

    xml_root = ET.Element("xml-root")
    tagresults = ET.SubElement(xml_root, 'tagresults')
    ppos_xml = ET.SubElement(tagresults, 'ppos')
    spos_xml = ET.SubElement(tagresults, 'spos')
    fileresults = ET.SubElement(xml_root, 'fileresults')
    file_ppos_xml = ET.SubElement(fileresults, 'ppos')
    file_spos_xml = ET.SubElement(fileresults, 'spos')

    for key in ppos:
        ppo_type = ET.SubElement(ppos_xml, "ppo")
        ppo_type.set("name", key)
        for val in ppos[key]:
            stat = ppos[key][val]
            ppo_type.set(val, str(stat))

    for key in spos:
        spo_type = ET.SubElement(spos_xml, "spo")
        spo_type.set("name", key)
        for val in spos[key]:
            stat = spos[key][val]
            spo_type.set(val, str(stat))

    for key in file_ppos:
        ppo_file = ET.SubElement(file_ppos_xml, "ppo")
        ppo_file.set("name", key)
        stats_dict = file_ppos[key]
        for stats in stats_dict:
            ppo_file.set(stats, str(stats_dict[stats]))

    for key in file_spos:
        spo_file = ET.SubElement(file_spos_xml, "spo")
        spo_file.set("name", key)
        stats_dict = file_spos[key]
        for stats in stats_dict:
            spo_file.set(stats, str(stats_dict[stats]))

    tree = ET.ElementTree(xml_root)
    tree.write(xml_file)

def read_project_summary_results(path):
    if os.path.isdir(path):
        filename = os.path.join(path,'summaryresults.json')
        if os.path.isfile(filename):
            with open(filename) as fp:
                d = json.load(fp)
                return d
        else:
            print('Warning: ' + filename + ' not found: summarize results first')
    else:
        print('Warning: ' + path + ' not found: please check path name')

def read_project_summary_results_history(path):
    result = []
    if os.path.isdir(path):
        for fname in os.listdir(path):
            if fname.startswith('summaryresults'):
                fname = os.path.join(path,fname)
                with open(fname) as fp:
                    result.append(json.load(fp))
    return result

def get_global_declarations_xnode(path):
    filename = get_global_definitions_filename(path)
    return get_xnode(filename,'globals','Global type dictionary file',show=False)

def get_global_dictionary_xnode(path):
    filename = get_global_definitions_filename(path)
    gnode = get_xnode(filename,'globals','Global type declarations file',show=False)
    if not gnode is None:
        return gnode.find('dictionary')
        
# ------------------------------------------------------------------- files ----

def get_cfilenamebase(cfilename):
    if cfilename.endswith('.c'): return cfilename[:-2]
    return cfilename

def get_cfile_filename(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_cfile.xml')

def get_cfile_xnode(path,cfilename):
    filename = get_cfile_filename(path,cfilename)
    return get_xnode(filename,'c-file','C source file')

def get_cfile_dictionaryname(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_cdict.xml')

def get_cfile_dictionary_xnode(path,cfilename):
    filename = get_cfile_dictionaryname(path,cfilename)
    return get_xnode(filename,'cfile','C dictionary file')

def get_cfile_predicate_dictionaryname(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_prd.xml')

def get_cfile_predicate_dictionary_xnode(path,cfilename):
    filename = get_cfile_predicate_dictionaryname(path,cfilename)
    return get_xnode(filename,'po-dictionary','PO predicate dictionary file',show=False)

def get_cfile_assignment_dictionaryname(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_cgl.xml')

def get_cfile_assignment_dictionary_xnode(path,cfilename):
    filename = get_cfile_assignment_dictionaryname(path,cfilename)
    return get_xnode(filename,'assignment-dictionary','Global assignments dictionary file',show=False)

def get_cfile_interface_dictionaryname(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_ixf.xml')

def get_cfile_interface_dictionary_xnode(path,cfilename):
    filename = get_cfile_interface_dictionaryname(path,cfilename)
    return get_xnode(filename,'interface-dictionary','Interface objects dictionary file',show=False)

def save_cfile_interface_dictionary(path,cfilename,xnode):
    filename = get_cfile_interface_dictionaryname(path,cfilename)
    header = UX.get_xml_header(filename,'interfacedictionary')
    header.append(xnode)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(header)))

def get_cfile_contexttablename(path,cfilename):
    cfilename = get_cfilenamebase(cfilename)
    return os.path.join(path,cfilename + '_ctxt.xml')

def get_cfile_contexttable_xnode(path,cfilename):
    filename = get_cfile_contexttablename(path,cfilename)
    return get_xnode(filename,'c-contexts','C contexts file',show=False)

def get_cfile_directory(path,cfilename):
    return os.path.join(path,get_cfilenamebase(cfilename))

def get_cfile_logfiles_directory(path,cfilename):
    logpath = os.path.join(path,'logfiles')
    return os.path.join(logpath,get_cfilenamebase(cfilename))

def get_cxreffile_filename(path,cfilename):
    if cfilename.endswith('.c'):
        cfilename = cfilename[:-2]
    return os.path.join(path,cfilename + '_gxrefs.xml')

def get_cxreffile_xnode(path,cfilename):
    filename = get_cxreffile_filename(path,cfilename)
    return get_xnode(filename,'global-xrefs','File with global cross references',show=False)

def get_global_invs_filename(path,cfilename,objectname):
    if cfilename.endswith('.c'):
        cfilename = cfilename[:-2]
    objectname = '' if objectname == 'all' else '_' + objectname 
    return os.path.join(path,cfilename + objectname + '_ginvs.xml')

def get_cfile_usr_filename(path,cfilename):
    return os.path.join(path,(get_cfilenamebase(cfilename) + '_usr.xml'))

# ----------------------------------------------------------------- functions --

def get_cfun_basename(path,cfilename,fname):
    cfilename = get_cfilenamebase(cfilename)
    cfiledir = os.path.join(path,cfilename)
    basename = os.path.basename(cfilename)
    return os.path.join(cfiledir,basename + '_' + fname)

def get_cfun_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_cfun.xml')

def get_cfun_xnode(path,cfilename,fname):
    filename = get_cfun_filename(path,cfilename,fname)
    return get_xnode(filename,'function','C source function file')

def get_api_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_api.xml')

def get_api_xnode(path,cfilename,fname):
    filename = get_api_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Function api file',show=False)

def save_api(path,cfilename,fname,xnode):
    filename = get_api_filename(path,cfilename,fname)
    header = UX.get_xml_header(filename,'api')
    header.append(xnode)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(header)))

def get_vars_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_vars.xml')

def get_vars_xnode(path,cfilename,fname):
    filename = get_vars_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Function variable dictionary',show=False)

def get_invs_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_invs.xml')

def get_invs_xnode(path,cfilename,fname):
    filename = get_invs_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Function invariants',show=False)

def get_pod_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_pod.xml')

def get_pod_xnode(path,cfilename,fname):
    filename = get_pod_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Function proof obligation types',show=False)

def get_ppo_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_ppo.xml')

def get_ppo_xnode(path,cfilename,fname):
    filename = get_ppo_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Primary proof obligations file')

def get_spo_filename(path,cfilename,fname):
    return (get_cfun_basename(path,cfilename,fname) + '_spo.xml')

def get_spo_xnode(path,cfilename,fname):
    filename = get_spo_filename(path,cfilename,fname)
    return get_xnode(filename,'function','Secondary proof obligations file',show=False)

def save_spo_file(path,cfilename,fname,cnode):
    filename = get_spo_filename(path,cfilename,fname)
    header = UX.get_xml_header(filename,'spos')
    header.append(cnode)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(header)))

def save_pod_file(path,cfilename,fname,cnode):
    filename = get_pod_filename(path,cfilename,fname)
    header = UX.get_xml_header(filename,'pod')
    header.append(cnode)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(header)))

def get_results_filenames(path,cfilename,fname):
    result = [
        get_ppo_filename(path,cfilename,fname),
        get_spo_filename(path,cfilename,fname),
        get_pev_filename(path,cfilename,fname),
        get_sev_filename(path,cfilename,fname),
        get_api_filename(path,cfilename,fname),
        get_invs_filename(path,cfilename,fname) ]
    return result

# --------------------------------------------------------------- source code --

def get_src_filename(path,cfilename):
    return os.path.join(path,cfilename)

def get_srcfile_lines(path,cfilename):
    filename = get_src_filename(path,cfilename)
    with open(filename,'r') as fp:
        return fp.readlines()

# --------------------------------------------------------------- contracts ----

def has_contracts(path,cfilename):
    filename = os.path.join(path,cfilename + '_c.xml')
    return os.path.isfile(filename)

def has_candidate_contracts(path,cfilename):
    filename = os.path.join(path,cfilename + '_cc.xml')
    return os.path.isfile(filename)

def get_contracts(path,cfilename):
    filename = os.path.join(path,cfilename + '_c.xml')
    return get_xnode(filename,'cfile','Contract file',show=True)

def get_candidate_contracts(path,cfilename):
    filename = os.path.join(path,cfilename + '_cc.xml')
    return get_xnode(filename,'cfile','Contract file',show=True)

def has_global_contract(path):
    filename = os.path.join(path,'globaldefs.json')
    return os.path.isfile(filename)

def has_global_xml_contract(path):
    filename = os.path.join(path,'globaldefs.xml')
    return os.path.isfile(filename)

def get_global_contract(path):
    filename = os.path.join(path,'globaldefs.json')
    if os.path.isfile(filename):
        with open(filename,'r') as fp:
            return json.load(fp)
    return {}

def get_global_xml_contract(path):
    filename = os.path.join(path,'globaldefs.xml')
    return get_xnode(filename,'global-definitions','Global contract file')

def _save_contracts_file_aux(path,filename,cnode):
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    root = UX.get_xml_header('cfile','cfile')
    root.append(cnode)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(root)))

def save_contracts_file(path,cfilename,cnode):
    filename = os.path.join(path,cfilename + '_c.xml')
    _save_contracts_file_aux(path,filename,cnode)

def save_global_xml_contract(path,cnode):
    filename = os.path.join(path,'globaldefs.xml')
    root = UX.get_xml_header('codehawk-contract-file','codehawk-contract-file')
    root.append(cnode)
    if os.path.isfile(filename):
        create_backup_file(filename)
    with open(filename,'w') as fp:
        fp.write(UX.doc_to_pretty(ET.ElementTree(root)))

def save_candidate_cotracts_file(path,cfilename,cnode):
    filename = os.path.join(path,cfilename + '_cc.xml')
    _save_contracts_file_aux(path,filename,cnode)

# ------------------------------------------------------------ exported --------

def save_cx_file(path,cfilename,d):
    cxdir = os.path.join(path,'exportfiles')
    if not os.path.isdir(cxdir):
        os.makedirs(cxdir)
    filename = os.path.join(cxdir,cfilename + '_cx.json')
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    with open(filename,'w') as fp:
        json.dump(d,fp,indent=3)

# ------------------------------------------------------------ projects --------

def get_testdata_dict():
    testdatapath = os.path.join(Config().testdir,'testdata')
    testdatafile = os.path.join(testdatapath,'testprojects.json')
    if os.path.isfile(testdatafile):
        with open(testdatafile,'r') as fp:
            testdata = json.load(fp)
            return testdata
    return {}

def get_project_path(path):
    testdir = Config().testdir
    testdata = get_testdata_dict()
    if path in testdata:
        return  os.path.join(testdir,str(testdata[path]['path']))
    else:
        return os.path.abspath(path)

def get_project_logfilename(path):
    testdir = Config().testdir
    testdata = get_testdata_dict()
    if path in testdata:
        logpath = os.path.join(testdir,str(testdata[path]['path']))
        logfile = os.path.join(logpath,path + '.chc_analysis_log')
        return logfile
    else:
        logfile = os.path.join(path,'log.chc_analysis_log')
        return logfile

def list_test_applications():
    testdata = get_testdata_dict()
    lines = []
    lines.append('*' * 80)
    lines.append('Test applications currently provided:')
    lines.append('-' * 80)
    maxlen = max(len(name) for name in testdata) + 5
    for name in sorted(testdata):
        lines.append(name.ljust(maxlen) + testdata[name]['path'])
    lines.append('*' * 80)
    return '\n'.join(lines)
    


# ------------------------------------------------------------ kendra tests ----

def get_kendra_path(): return Config().kendradir

def get_kendra_testpath(testname):
    dirname = os.path.join(get_kendra_path(),testname)
    if not os.path.isdir(dirname):
        raise CHCDirectoryNotFoundError(dirname)
    return dirname

def get_kendra_testpath_byid(testid):
    testname = 'id' + str(testid) + 'Q'
    testpath = get_kendra_testpath(testname)
    if os.path.isdir(testpath):
        return testpath
    raise CHCDirectoryNotFoundError(testpath)

def get_kendra_cpath(cfilename):
    if cfilename.endswith('.c'):
        testid = int(cfilename[2:-2])
        testbase  = (((testid - 115) / 4) * 4) + 115
        return get_kendra_testpath_byid(testbase)
    else:
        raise CHCFileNotFoundError(cfilename)

# ------------------------------------------------------------ zitser tests ----

def get_zitser_path(): return Config().zitserdir

def get_zitser_summaries():
    path = get_zitser_path()
    summarypath = os.path.join(path,'testcasesupport')
    summarypath = os.path.join(summarypath,'zitsersummaries')
    return os.path.join(summarypath,'zitsersummaries.jar')

def get_zitser_testpath(testname):
    return os.path.join(get_zitser_path(),testname)

# ------------------------------------------------------------ juliet tests ----

def get_juliet_path():
    sardpath = os.path.join(Config().testdir,'sard')
    return os.path.abspath(os.path.join(sardpath,'juliet_v1.3'))

def get_juliet_testcases_list():
    path = get_juliet_path()
    filename = os.path.join(path,'juliettestcases.json')
    if os.path.isfile(filename):
        with open(filename) as fp:
            return json.load(fp)

def get_juliet_summaries():
    path = get_juliet_path()
    summarypath = os.path.join(path,'testcasesupport')
    summarypath = os.path.join(summarypath,'julietsummaries')
    return os.path.join(summarypath,'julietsummaries.jar')

def get_juliet_testpath(testname):
    return os.path.join(get_juliet_path(),testname)

def save_juliet_test_summary(testname,d):
    path = get_juliet_testpath(testname)
    with open(os.path.join(path,'jsummaryresults.json'),'w') as fp:
        json.dump(d,fp,sort_keys=True)

def read_juliet_test_summary(testname):
    path = get_juliet_testpath(testname)
    if os.path.isdir(path):
        filename = os.path.join(path,'jsummaryresults.json')
        if os.path.isfile(filename):
            with open(filename) as fp:
                d = json.load(fp)
            return d

def get_juliet_reference(testname):
    path = get_juliet_testpath(testname)
    scorekey = os.path.join(path,'scorekey.json')
    if os.path.isfile(scorekey):
        with open(scorekey,'r') as fp:
            d = json.load(fp)
        return d

# ----------------------------------------------------------- itc tests  ------

def get_itc_path():
    sardpath = os.path.join(Config().testdir,'sard')
    return os.path.abspath(os.path.join(sardpath,'itc'))

def get_itc_testpath(testname):
    return os.path.join(get_itc_path(),testname)

# ----------------------------------------------------------- cgc tests  ------

def get_cgc_path():
    return os.path.join(Config().testdir,'cgc')

def make_cgc_challenge_path(testname,targetname):
    challengepath = os.path.join(get_cgc_path(),'challenges')
    testpath = os.path.join(challengepath,testname)
    if not os.path.isdir(testpath): os.mkdir(testpath)
    tgtpath = os.path.join(testpath,targetname)
    if not os.path.isdir(tgtpath): os.mkdir(tgtpath)
    return tgtpath

def get_cgc_challenge_path(testname,targetname):
    challengepath = os.path.join(get_cgc_path(),'challenges')
    testpath = os.path.join(challengepath,testname)
    tgtpath = os.path.join(testpath,targetname)
    return tgtpath

def get_cgc_challenges():
    challenges = os.path.join(get_cgc_path(),'challenges.json')
    with open(challenges,'r') as fp:
        tests = json.load(fp)
        if not tests is None:
            return tests['challenges']
    return {}

def get_cgc_test_targets(t):
    challenges = get_cgc_challenges()
    if t in challenges:
        return challenges[t]['targets']
    else:
        return []

def read_cgc_summary_results(testname,targetname):
    path = get_cgc_challenge_path(testname,targetname)
    if os.path.isdir(path):
        filename = os.path.join(path,'summaryresults.json')
        if os.path.isfile(filename):
            with open(filename) as fp:
                d = json.load(fp)
            return d

def get_cgc_summaries():
    cgcpath = get_cgc_path()
    summarypath = os.path.join(cgcpath,'cgcsummaries')
    return os.path.join(summarypath,'cgcsummaries.jar')

# ---------------------------------------------------- functional tests  ------

def get_functional_tests_path():
    return os.path.join(Config().testdir,'functional')

def get_functional_testpath(testpath):
    return os.path.join(get_functional_tests_path(),testpath)

# ---------------------------------------------------- workshop files  ------

def get_workshop_path():
    return os.path.join(Config().testdir,'workshop')

def get_workshop_list():
    filename =  os.path.join(get_workshop_path(),'workshop.json')
    if os.path.isfile(filename):
        with open(filename) as fp:
            workshoplist = json.load(fp)
            return workshoplist

def get_workshop_file_data(project,wfile):
    wspath = get_workshop_path()
    workshoplist = get_workshop_list()
    if not workshoplist is None:
        if project in workshoplist:
            projectlist = workshoplist[project]
            if wfile in projectlist:
                wsdata = projectlist[wfile]
                filedata = {}
                filedata['summaries'] = []
                filedata['file'] = wsdata['file']
                filedata['path'] = os.path.join(wspath,wsdata['path'])
                for s in wsdata['summaries']:
                    filedata['summaries'].append(os.path.join(wspath,s))
                return filedata
            else:
                print('*' * 80)
                print('Workshop file: ' + wfile + ' not foound in project: ' + project + '.')
                print('Available files are in project: ' + project + ' are:')
                print('-' * 80)
                for name in projectlist:
                    print(name.ljust(8) + ': ' + projectlist[name]['path'] + ', ' + projectlist[name]['file'])
                print('-' * 80)
                exit(0)
        else:
            print('*' * 80)
            print('Workshop project: ' + project + ' not found.')
            print('Available workshop projects are:')
            print('-' * 80)
            for name in workshoplist:
                print(name)
            print('-' * 80)
            exit(0)

# ------------------------------------------------------------ my cfiles ------

def get_my_cfiles(testname):
    config = Config()
    if testname in config.mycfiles:
        testdata = config.mycfiles[testname]
        return (testdata['path'],testdata['file'])
    

# ------------------------------------------------------------ svcomp ----------

def get_svcomp_path():
    return Config().svcompdir

def get_svcomp_testpath(testname):
    svcomppath = get_svcomp_path()
    return os.path.join(os.path.join(svcomppath,'c'),testname)

def get_svcomp_srcpath(testname):
    return get_svcomp_testpath(testname)

def unpack_src_i_tar_file(testname):
    path = get_svcomp_testpath(testname)
    os.chdir(path)
    srctar = testname + '_src_i.tar.gz'
    if os.path.isfile(srctar):
        cmd = [ 'tar', 'xfz', srctar ]
        result = subprocess.call(cmd,cwd=path,stderr=subprocess.STDOUT)
        if result != 0:
            print('Error in ' + ' '.join(cmd))
            return False
        else:
            print('Successfully extracted ' + srctar)
    else:
        print('File ' + srctar + ' not found')
        return False
    return True

# ------------------------------------------------------------ unzip tar file --

def unpack_tar_file(path,deletesemantics=False):
    linuxtargzfile = 'semantics_linux.tar.gz'
    mactargzfile = 'semantics_mac.tar.gz'
    os.chdir(path)

    if os.path.isfile(linuxtargzfile):
        targzfile = linuxtargzfile
    elif os.path.isfile(mactargzfile):
        targzfile = mactargzfile
    elif os.path.isdir('semantics') and not deletesemantics:
        return True
    else:
        return False

    if os.path.isdir('semantics'):
        if deletesemantics:
            print('Removing existing semantics directory')
            shutil.rmtree('semantics')
        else:
            return True

    if os.path.isfile(targzfile):
        cmd = [ 'tar', 'xfz', targzfile ]
        result = subprocess.call(cmd,cwd=path,stderr=subprocess.STDOUT)
        if result != 0:
            print('Error in ' + ' '.join(cmd))
            return False
        # else:
            # print('Successfully extracted ' + targzfile)
    return os.path.isdir('semantics')
        

if __name__ == '__main__':

    config = Config()

    testdir = config.testdir

    print('\nkendra paths:')
    print('-' * 80)
    for id in range(115,119):
        id = 'id' + str(id) + '.c'
        try:
            print('  ' + id + ': ' + get_kendra_cpath(id))
        except CHError as e:
            print(str(e.wrap()))
            exit(1)

    print('\nzitser paths:')
    print('-' * 80)
    for id in [ 'id1283', 'id1310' ]:
        print('  ' + id + get_zitser_testpath(id))

    try:
        print(get_kendra_testpath('id115Q'))
    except CHCError as e:
        print(str(e.wrap()))
                  
