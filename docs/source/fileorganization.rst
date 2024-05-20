CodeHawk-C File Organization
============================

C Applications are analyzed by individual compilation unit (cfile called here)
by the OCaml analyzer in multiple rounds. After each round, the results of those
analyses are integrated by the python interface. This integration includes the
generation of supporting proof obligations that reach across compilation units,
and making available return value assumptions, by request. These new proof
obligations and assumptions are added to the results files to be consumed by the
OCaml analyzer. This process continues until stabilization, or when a specified
maximum number of rounds is reached.

In the following descriptions we use the abbreviations:

* **ppo**    primary proof obligation
* **spo**    supporting proof obligation

The various intermediate files passed between the OCaml analyzer and python are
the following.

At the file level:
------------------
  
**<filename>_cfile.xml**
  global declarations:  created by cchcil upon parsing the C source code; never
  modified
  
**<filename>_cdict.xml**
  dictionary of types and expressions. Originally created by cchcil upon
  parsing the C source code, but updated by cchlib in subsequent rounds
  
**<filename>_ctxt.xml**
  dictionary of contexts used in expressing locations created and updated
  by cchcil
    
**<filename>_prd.xml**
  dictionary of predicates used in expressing proof obligations, created and
  updated by cchpre
    
**<filename>_ixf.xml**
  dictionary of interface predicates used in expressing assumptions and
  guarantees external to functions
    
**<filename>_cgl.xml**
  dictionary of assignments to global variables
    
**<filename>_gxrefs.xml**
  association table that relates file identifiers of variables (varinfo's)
  and structs (compinfo's) to global identifiers, to facilitate communication
  and exchange of assumptions/guarantees between different files.

At the function level (all prefixed with <filename_functionname>:
-----------------------------------------------------------------

**_cfun.xml**
  function semantics, as produced by CIL, created by
  cchcil upon parsing the C source code, never modified
  
**_ppo.xml**
  primary proof obligations for the function, generated
  once by cchpre, not updated afterwards
  
**_spo.xml**
  supporting proof obligations for the function,
  primarily generated and updated by the python side
  
**_pod.xml**
  dictionary for assumptions, ppos, and spos, initially
  created by cchpre, and updated by both cchpre and the
  python side as new spos are added in each round.
  
**_api.xml**
  external assumptions and guarantees from other functions,
  global variables, and possibly user-provided contracts.
  
**_vars.xml**
  variable and expression dictionary containing all
  variables and expressions used in the invariants
  
**_invs.xml**
  invariant dictionary containing all location invariants
  (with locations specified by context)
