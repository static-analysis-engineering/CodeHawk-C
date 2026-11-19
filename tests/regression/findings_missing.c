/* Regression test for the caveat in the FINDINGS section of the verification
   report: no violations and no open proof obligations, but information is
   missing: ext_effect is neither defined nor summarized (its preconditions
   are not checked). The report must not suggest that absence of undefined
   behavior is established. */

extern void ext_effect(void);

int missing(void) {
  ext_effect();
  return 0;
}
