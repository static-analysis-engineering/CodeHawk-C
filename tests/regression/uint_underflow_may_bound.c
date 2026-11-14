/* A universal uint-underflow violation of e1 - e2 requires
   UB(e1) - LB(e2) < 0; the checker compared UB(e1) - UB(e2), and reported
   a violation for a in [10, 20], b in [0, 100] (a - b is safe for b <= a). */

unsigned int sub_may(unsigned int a, unsigned int b) {
  if (a >= 10 && a <= 20 && b <= 100) {
    return a - b;
  }
  return 0;
}

/* UB(a) - LB(b) == 20 - 30 < 0: violation on every execution */
unsigned int sub_must(unsigned int a, unsigned int b) {
  if (a <= 20 && b >= 30 && b <= 100) {
    return a - b;
  }
  return 0;
}
