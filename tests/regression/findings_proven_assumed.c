/* Regression test for the caveat in the FINDINGS section of the verification
   report: no violations, all proof obligations proven, some under the
   assumption that callers outside the analyzed code establish the
   preconditions of proven_assumed (p valid); the report states absence of
   undefined behavior, including the assumptions. */

int proven_assumed(int *p) {
  return *p;
}
