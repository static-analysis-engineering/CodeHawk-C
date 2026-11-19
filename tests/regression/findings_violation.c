/* Regression test for the caveat in the FINDINGS section of the verification
   report: a violation (a[10]), no open proof obligations, and no
   information missing; the list of violations is complete, so the report
   has no caveat. */

int violation(void) {
  int a[10];
  a[10] = 0;
  return 0;
}
