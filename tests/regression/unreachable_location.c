/* Issue 25: a proof obligation at a location that some domain proves
   unreachable is not discharged by unreachability and is not checked against
   the remaining domains' facts (unless the analyzer runs with
   -unreachability, as for Juliet): it stays open with an explicit
   'unreachable' diagnostic and is reported separately. Statement-local
   checks (which use no invariants) are still performed. */

int arr[10];

/* intervals, pepr and symbolic sets prove the then-branch unreachable; the
   linear-equalities fact s == -5 made index-lower-bound(s) a violation */
int plain_const(void) {
  int s = -5;
  if (s >= 0) {
    arr[s] = 1;
  }
  return 0;
}

/* intervals prove the inner branch unreachable; the pepr facts delegated
   both index proof obligations to the api (a spurious precondition on every
   caller) */
int param_dead(int n) {
  if (n < 0) {
    if (n > 3) {
      arr[n] = 1;
    }
  }
  return 0;
}

/* statement-local checks still apply at an unreachable location:
   index-lower-bound(3) and index-upper-bound(3,10) are safe */
int stmt_valid_dead(int n) {
  if (n < 0) {
    if (n > 3) {
      arr[3] = n;
    }
  }
  return 0;
}

/* reachable code is not affected */
int reachable(int n) {
  if (n >= 0 && n < 10) {
    return arr[n];
  }
  return 0;
}
