## Scripts to analyze the Juliet Test Suite test cases

### Overview

- chc_analyze_juliettest.py
- chc_check_config.py
- chc_investigate_ppos.py
- chc_juliet_dashboard.py
- chc_list_juliettests.py
- chc_project_dashboard.py
- chc_report_juliettest.py
- chc_report_juliettest_file.py
- chc_report_requests.py
- chc_score_juliettest.py

### Test identification

All scripts that target individual test cases take a ```cwe``` and
a ```test``` argument. The ```cwe``` argument is expected to be of
the form ```CWExxx``` where xxx indicates the number of the CWE,
e.g., ```CWE121```. The ```test``` argument should be the name of
the functional variant of the test case. For example for the test
case
```
CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_ncpy
```
the ```test``` argument should be given as
```
CWE193_char_alloca_ncpy
```
