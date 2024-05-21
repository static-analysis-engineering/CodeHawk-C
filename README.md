# CodeHawk-C
Sound Static Analysis of C for Memory Safety (Undefined Behavior)

### Quick start

The CodeHawk-C Analyzer consists of two parts:
- A python front end (this repository) through which all user interaction
  is performed, and
- An ocaml abstract-interpretation engine that powers the analysis.

To use the CodeHawk-C Analyzer first clone or download the ocaml application
from
```
https://github.com/static-analysis-engineering/codehawk
```
and build according to the accompanying instructions given there.
Then copy the following files from that build:
```
codehawk/CodeHawk/CHC/cchcil/parseFile
codehawk/CodeHawk/CHC/cchcmdline/canalyzer
```
to the following location in this repository:
```
CodeHawk-C/chc/bin/linux/
```
or
```
CodeHawk-C/chc/bin/macOS
```
depending on the platform where the executables were built.
Alternatively, you can edit the path to these two executables directly
in chc/util/Config.py or chc/util/ConfigLocal.py, so there is no need
to copy them or update them with each new version of the ocaml analyzer.

Set the python path and path:
```
export PYTHONPATH=$HOME/CodeHawk-C
export PATH=$HOME/CodeHawk-C/chc/cmdline:$PATH
```
and check whether all the components are in place with:
```
> chkc info
```
which should show something like:
```
================================================================================
Analyzer configuration:
-----------------------
  platform : linux
  parser   : /home/user/codehawk/CodeHawk/CHC/cchcil/parseFile (found)
  analyzer : /home/user/codehawk/CodeHawk/CHC/cchcmdline/canalyzer (found)

  summaries: /home/user/CodeHawk-C/chc/summaries/cchsummaries.jar (found)
```

Interaction with the analyzer is primarily through the command-line interpreter
**chkc**. Two modes are available:
1. **Single c-file:** A single c-file can be analyzed and investigated with the
   sequence of commands:
   ```
   > chkc c-file parse <filename>
   > chkc c-file analyze <filename>
   > chkc c-file report-file <filename>
   ```
   The first command preprocesses the file with gcc; the preprocessed file (.i file)
   is then parsed with **parseFile** (a wrapper for goblint-cil,
   https://opam.ocaml.org/packages/goblint-cil/).
   The second command analyzes the parsed artifacts, and the third command (and
   several others) allow inspection of the results.

2. **Multiple c-files:** For this case it is expected that the source files are
   ready to be parsed, and that the specific build sequence is encoded in a
   compile_commands.json file, a standard format that is produced by many build
   systems these days. Alternatively, if a project comes with a Makefile only,
   the utility **bear** can be used to produce a compile_commands.json file like
   so:
   ```
   > bear make
   ```
   The compile_commands.json file must be present in the top directory of
   the project.

   When this is in place, the project can be analyzed with the sequence of
   commands:
   ```
   > chkc c-project parse <projectdirectory> <projectname>
   > chkc c-project analyze <projectdirectory> <projectname>
   > chkc c-project report <projectdirectory> <projectname>
   ```
   Other commands are available to inspect the results for individual file
   or functions.


A quick test of whether the analyzer works as expected is to run the
regression tests:
```
> chkc kendra test-sets
```
This command analyzes a subset of a larger collection of buffer-overflow
testcases published by NIST (https://samate.nist.gov/SARD/test-suites/89),
originally developed by Kendra Kratkiewicz and Richard Lippmann at MIT
Lincoln Laboratory (2005) (https://samate.nist.gov/SSATTM_Content/papers/Taxonomy%20of%20Buffer%20Overflows%20-%20Kratkiewicz%20-%20Lippmann%20.pdf). More commands
are available to further inspect the results from the kendra tests.


In all cases the status of proof obligations
generated can be output on the source code, with indicators with the following
meaning:
```
  <S> : (safe:statement) the proof obligation was discharged based on
        information belonging to the statement itself (and possibly function
        and/or global declarations);
  <L> : (safe:local) the proof obligation was discharged based on local
        invariants generated for the function (without assumptions on
        the values of arguments);
  <A> : (conditionally safe:api) the proof obligation was discharged by
        making assumptions on the arguments passed to the function; these
        assumptions are added to the function api assumptions (listed at
        the top of the function) and are imposed as supporting proof
		obligations on all callers of the function;
  <*> : (violation) the proof obligation was shown to be false. This
        usually means the proof obligation is false for all possible
        computations (universally false). In some cases, it may
		indicate the existence of a (presumably tainted) value that
		falsifies the proof obligation (existentially false).
  <?> : (unknown) the analyzer was not able to either prove or disprove
        the proof obligation. In some cases a diagnostic message may
        provide an indication of what information is lacking for the
		proof.
```


### Acknowledgment
The development of the CodeHawk C Source Code Analyzer was sponsored
in part by the Department of Homeland Security and the Air Force
Research Laboratory under contract
\#FA8750-12-C-0277. The content of the information does not
necessarily reflect the position or policy of the Government and
no official endorsement should be inferred.
  
  
  
