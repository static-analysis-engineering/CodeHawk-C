## Scripts to parse and analyze C projects

### Overview

- [chc_analyze_project.py](#chc_analyze_project)
- [chc_list_missing_summaries.py](#chc_list_missing_summaries)
- [chc_parse_project.py](#chc_parse_project)
- [chc_report_project.py](#chc_report_project)

### Short-cut names
Most scripts have as their first argument the path to the directory
that holds the Makefile. For all of these scripts the path name may
be replaced by a so-called *short-cut* name, which consists of two
identifiers separated by a colon, e.g., ```misc:file```, where the
first identifier is an index of a project file registered in the
```targets``` property of ```chc.util.Config``` and the second
identifier is the index of a project present in that project file.
An example of such a project file is [misc.json](https://github.com/kestreltechnology/CodeHawk-C-Targets-Misc/tree/master/targets/misc.json)
in the CodeHawk-C-Targets-Misc repository.

### Scripts

#### chc_analyze_project
Generates proof obligations, generates invariants and attempts to
discharge the proof obligations for each source file, followed by
an integration step (performed by the python code) that propagates
function api assumptions to all relevant call sites to create
supporting proof obligations.
- positional arguments:
  - *path*: absolute or relative path to directory that holds the semantics
    directory (or semantics_linux.tar.gz file), or short-cut name

- keyword arguments:
  - *--maxprocesses* value: number of source files to process in parallel
    (default: 1)
  - *--wordsize* value: architecture word size in bits (default: 32)
  - *--verbose*: show output from analyzer on console (recommended)
  - *--deletesemantics*: remove the semantics directory (if present) and
    unpack a fresh version of the semantics from the semantics_linux.tar.gz
    file (recommended)
  - *--analysisrounds* value: number of times to repeat the creation of
    supporting proof obligation and re-analysis.
  - *--contractpath* cpath: path to the directory that holds the
    application function contracts (default: same as ```path```)
  - *--candidate_contractpath* cpath: currently not used
  - *--logging* level: log level messages to be recorded
    (values allowed: DEBUG,INFO,WARNING,ERROR,CRITICAL)
    (default: WARNING)
  - *--logfilename* filename: name of the file to collect log messages
    (default: chc_logfile.txt in the ```path``` directory)	

[top](#overview)

#### chc_list_missing_summaries
Prints a list of functions, organized by header file, for which no
summary is available.
- positional arguments:
  - *path*: absolute or relative path to directory that holds the
    semantics directory, or short-cut name

- keyword arguments:
  - *--all*: show all functions for which no summary is available,
  including possibly application functions

[top](#overview)

#### chc_parse_project
Creates the semantic artifacts for a c application. It first runs
```bear make``` to record the actions taken by the Makefile, then
does a ```make clean``` to restore the original state, and finally
replays the recorded commands modified to apply the CIL parser on
the pre-processed files.
- positional arguments:
  - *path*: absolute or relative path to directory that holds the Makefile,
    or short-cut name
  
-  keyword arguments:
   - *--targetdir* directoryname: name of a directory to save the semantics
     files; default is ```path```.
   - *--maketarget* target: target to be given to the ```make``` command;
     default None
   - *--keepUnused*: keep variables that are not used
   - *--savesemantics*: save the semantic artefacts in a gzipped tar file
   - *--filter*: filter out files with filenames with absolute path
   - *--removesemantics*: remove existing semantics directory if present
   - *--platformwordsize* value: wordsize of target platform (32 or 64)

[top](#Overview)

#### chc_report_project
Prints a summary of the analysis results for a c application. Is successful
only after the analysis has been performed.
- positional arguments:
  - *path*: absolute or relative path to directory that holds the semantics
    directory, or short-cut name

- keyword arguments:
  - *--history*: include previous versions of the results

[top](#Overview)
