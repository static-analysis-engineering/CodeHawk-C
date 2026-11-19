/* Regression test for the caveat in the FINDINGS section of the verification
   report: no violations, all proof obligations proven without assumptions,
   and no information missing; the report states absence of undefined
   behavior, within the limits of the system boundary. */

int proven(void) {
  int a[2];
  a[0] = 1;
  a[1] = 2;
  return a[0] + a[1];
}
