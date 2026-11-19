/* Regression test for the caveat in the FINDINGS section of the verification
   report: no violations, but open proof obligations (g_arr[g_idx] depends on
   the value of the global g_idx); no information is missing. The report
   must not suggest that absence of undefined behavior is established. */

int g_idx;
int g_arr[10];

int open_global(void) {
  return g_arr[g_idx];
}
