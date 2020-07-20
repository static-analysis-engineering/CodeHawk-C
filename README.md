# CodeHawk-C
Sound Static Analysis of C for Memory Safety (Undefined Behavior)

### Quick start

#### System requirements
- **Platform:** macOS or Linux
  The CodeHawk C Source Code Analyzer consists of two parts that are
  run separately, and may be run on different platforms:
  - *parser* (```parseFile```); this program is an extension of the
    CIL parser front end developed by George Necula and his students
    at UC Berkeley (and now available on
	[GitHub](https://github.com/cil-project/cil)). 
  - *analyzer* (```canalyzer```); this program generates the proof
	obligations, and performs invariant generation by abstract
	interpretation, which are then used to discharge the proof
	obligations.
  Both programs are provided in executable form for macOS and linux.
- **Bear**: The front=end parser makes use of the utility ```bear```,
  available from
  [GitHub](https://github.com/rizsotto/Bear/tree/master/libear)
  or from package managers. This utility records the actions of the
  Makefile when compiling an application; the recording is used to
  emit the necessary artifacts for analysis
- **Other dependencies:** All interactions with the analyzer are
  performed via python scripts, so python is required. The analyzer
  and python environment make use
  of JAR files, which requires a working Java installation.

#### General use guidelines

An analysis consists of two phases that may be performed on different
platforms:
1. **Parsing:** This phase takes as input the original source code, a
   Makefile (if there is more than one source file), and, in case of
   library includes, the library header files resident on the system.
   This phase produces as output a set of XML files that completely
   capture the semantics of the application; these files are the sole
   input of the Analysis phase.

   Because of the dependency on the resident system library header
   files, it is generally recommended to perform this phase on a Linux
   system, because of its more standard library environment than macOS
   (the CIL parser may also have some issues with some of the syntax
   of the macOS header files).
   
2. **Analysis:** This phase takes as input the XML files produced by
   the parsing phase. As long as the source code is not modified, the
   analysis can be run multiple times without have to repeat the
   parsing step. The Analysis step can be run on either macOS or
   Linux, independently of where the parsing step was performed, as it
   operates solely on the XML files produced and is not dependent on
   any external programs of library headers.

#### Getting started

All interactions with the parser and analyzer are performed via python
scripts. Separate sets of scripts are provided for different use cases.

- **Regression tests:** A first quick test of how (and whether) the
  parser and analyzer work
  as expected is to run the regression tests included in this
  repository:
  ```
  > git clone https://github.com/kestreltechnology/CodeHawk-C
  > export PYTHONPATH=$HOME/CodeHawk-C
  > cd CodeHawk-C/chc/cmdline/kendra
  > python chc_test_kendrasets.py
  ```
  If everything works okay this should produce an output like
  [this](tests/kendra/example_output/test_kendrasets.txt).

- **Single C file:** To analyze an application consisting of
  a single C file (without Makefile), located at, say,
  cfiletest/test.c, first parse the file:
  ```
  > export PYTHONPATH=$HOME/CodeHawk-C
  > cd CodeHawk-C/chc/cmdline/c_file
  > python chc_parse_file.py ~/cfiletest/test.c
  ```
  This produces, in the the same directory as test.c, a
  preprocessed version of the c file, ```test.i``` and a
  directory called ```semantics``` that has two subdirectories:
  1. ```chcartifacts```, which holds all of the semantic artifacts
     necessary for analysis, and
  2. ```sourcefiles```, the original c file and the preprocessed
     version, with extension ```i```.

  Now the file can be analyzed:
  ```
  > python chc_analyze_file.py ~/cfiletest ctest.c
  ```
  Notice that this script requires two separate arguments: the
  parent directory of the ```semantics``` directory and the name
  of the c file.

  The analyzer saves all of its results in the
  ```semantics/chcartifacts``` directory. To view a summary of the
  results:
  ```
  > python chc_report_file.py ~/cfiletest ctest.c
  ```
  To view the full results, including proof obligations and invariants for
  proof obligations that were not automatically discharged:
  ```
  > python chc_report_file.py ~/cfiletest ctest.c --showcode
  ```
  Proof obligations are shown with indicators with the following
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
- **C project (with Makefile)** To analyze a larger C application that
  consists of multiple source files and whose compilation is
  accomplished by a Makefile, first make sure that the application
  builds by invoking ```make```. If necessary, perform a
  ```.configure``` step to produce the Makefile and/or
  system-dependent header files. Do a ```make clean``` before
  performing the parsing step, to make sure the compilation of all
  source files is recorded:
  ```
  > export PYTHONPATH=$HOME/CodeHawk-C
  > cd CodeHawk-C/chc/cmdline/c_project
  > python chc_parse_project.py <path>
  ```
  where ```<path>``` indicates the name of the top-level directory that
  holds the Makefile. This step produces in the same directory a
  directory named```semantics``` with two subdirectories:
  1. ```chcartifacts```, which holds all of the semantic artifacts
     necessary for analysis, and
  2. ```sourcefiles```, which holds all of the original source files
     (.c files) and their preprocessed versions (.i files), organized
     in the same directory structure as the original c application.

  When analyzing a legacy project that will not be modified it is
  convenient to save the semantic artifacts in a tar file. This tar
  file can then be shared with others to facilitate a collaborative
  analysis with the guarantee that all have the same starting point
  (different computers may have different installations of linux,
  and/or gcc, resulting in different header files and different
  proof obligations). To create the tar file add the following
  command-line option to the parsing step:
  ```
  > python chc_parse_project.py <path> --savesemantics
  ```
  This will produce the file ```semantics_linux.tar.gz```. It is
  recommended to always generate this file, to enable restarting
  the analysis with a clean slate, without having to reparse the
  application.

  To analyze the project:
  ```
  > python chc_analyze_project.py <path> --verbose
  ```
  This step will first generate the proof obligations for each source file,
  then generate invariants for each source file, and attempt to
  discharge the proof obligations. All of these actions are local to
  each source file. If during the proof obligation discharge any api
  assumptions were generated, the  python infrastructure will collect
  these assumptions and generate supporting proof  obligations for
  all call sites. These are added to the set of proof obligations, and
  the analysis is run again on all individual source files. This
  sequence is repeated a number of times (default: 3).

  Depending on the size of the application this step can take from a
  few minutes to several hours.

  To view a summary of the results:
  ```
  > python chc_report_project.py <path>
  ```
  To view more comprehensive results for a single file:
  ```
  > python chc_report_project_file.py <path> <filename> --showcode
  ```
  where ```<filename>``` should include the full path relative to
  the ```<path>``` directory.

  More scripts are available in the ```chc/cmdline/c_project```
  directory to investigate the open proof obligations or generate
  suggestions for contract conditions. A more detailed description
  of these scripts is given [here](chc/cmdline/c_project/README.md).


- **Juliet Test Suite** A separate repository,
  [CodeHawk-C-Targets-Juliet](https://github.com/kestreltechnology/CodeHawk-C-Targets-Juliet),
  has been prepared with a large number of C-language test cases from
  the Juliet Test Suite (originally developed by NSA's Center for
  Assured Software and now maintained by NIST). Scripts customized for
  these tests are provided in
  [chc/cmdline/juliet](chc/cmdline/juliet/README.md).

  To run these tests, first obtain the repository:
  ```
  > git clone https://github.com/kestreltechnology/CodeHawk-C-Targets-Juliet.git
  ```
  and set the path in chc/util/ConfigLocal.py
  (if not present, copy from ConfigLocal.template)
  in the targets property, e.g.,
  ```
    juliettargets_home = os.path.expanduser('~')
    config.targets = {
       "juliet": os.path.join(juliettargets_home,
	                            "CodeHawk-C-Targets-Juliet/targets/juliettestcases.json")
        }
  ```
  (modify juliettargets_home to reflect your local path to the
  CodeHawk-C-Targets-Juliet repository).

  To check the configuration and analyze one of the tests:
  ```
  > export PYTHONPATH=$HOME/CodeHawk-C
  > cd CodeHawk-C/chc/cmdline/juliet
  > python chc_check_config.py
  > python chc_analyze_juliettest.py CWE121 CWE129_large
  > python chc_score_juliettest.py CWE121 CWE129_large
  > python chc_report_juliettest.py CWE121 CWE129_large
  ```
  Analysis of individual tests takes a few minutes or less than a
  minute if using multiple cores (use the --maxprocesses commandline
  argument to indicate the number of processors). More detailed
  descriptions of the scripts available for the Juliet tests are
  available [here](chc/cmdline/juliet/README.md).

### Source code
This repository contains the source code of the python infrastructure
that invokes the parser and analyzer and interprets and reports the
results. The source code for the parser and analyzer (written in
OCaml) is provided on GitHub at
[https://github.com/kestreltechnology/codehawk](https://github.com/kestreltechnology/codehawk) 
in the CodeHawk/CHC directory.

### Related repositories
Pre-parsed analysis targets are provided in separate repositories:
- [CodeHawk-C-Targets-Misc](https://github.com/kestreltechnology/CodeHawk-C-Targets-Misc):
  miscellaneous small c applications to demonstrate the use of
  function contracts and the analysis in general
- [CodeHawk-C-Targets-Juliet](https://github.com/kestreltechnology/CodeHawk-C-Targets-Juliet):
  Juliet Test Suite v1.3 test cases (from NIST)


### Acknowledgment
The development of the CodeHawk C Source Code Analyzer was sponsored
in part by the Department of Homeland Security and the Air Force
Research Laboratory under contract
\#FA8750-12-C-0277. The content of the information does not
necessarily reflect the position or policy of the Government and
no official endorsement should be inferred.
  
  
  
