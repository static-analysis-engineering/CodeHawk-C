/* Issue 29: E1 >> k for a constant k, 0 <= k < N, is floor(E1 / 2^k)
   (C11 6.5.7p5; for a negative signed E1 the result is
   implementation-defined, GCC's arithmetic shift is used). It is
   translated as E1 DIV 2^k for E1 >= 0 and (E1 - (2^k - 1)) DIV 2^k for
   E1 < 0, DIV being C division (truncation). Previously only k <= 4 was
   translated (as E1 / 2^k, also for negative E1), other constant shifts
   were unconstrained, and the interval ceiling of an exact quotient was
   one too high (ceiling(4) == 5). */

int arr[8];

/* u <= 95: u >> 4 <= 5 (interval: ceiling(95/16) == 6), index safe */
void shr_bound(unsigned int u) {
  if (u <= 95) {
    unsigned int v = u >> 4;
    arr[v + 1] = 1;
  }
}

/* u <= 96: u >> 4 <= 6 (exact quotient, previously 7), index safe */
void shr_bound_exact(unsigned int u) {
  if (u <= 96) {
    unsigned int v = u >> 4;
    arr[v + 1] = 1;
  }
}

/* u <= 100: u >> 4 <= 6, but the interval division gives ceiling(100/16)
   == 7: index-upper-bound open */
void shr_bound_ceil(unsigned int u) {
  if (u <= 100) {
    unsigned int v = u >> 4;
    arr[v + 1] = 1;
  }
}

/* u >= 32: u >> 5 >= 1 (k = 5 was not translated): not-zero safe */
int shr_nonzero(unsigned int u) {
  if (u >= 32) {
    unsigned int v = u >> 5;
    return (int) (10 / v);
  }
  return 0;
}

/* u >> 30 <= 3 for a 32-bit u (interval: 4), index safe */
void shr_top(unsigned int u) {
  arr[u >> 30] = 1;
}

/* -9 >> 3 == -2 (floor; truncation would give -1): not-zero violation */
int shr_neg_const(void) {
  int a = -9;
  int b = a >> 3;
  return 10 / (b + 2);
}

/* s in [-100, -1]: s >> 2 in [-25, -1] (interval: [-26, -1]), never 0
   (truncation would give 0 for s in [-3, -1]): not-zero safe */
int shr_neg_var(int s) {
  if (s >= -100 && s <= -1) {
    int t = s >> 2;
    return 10 / t;
  }
  return 0;
}

/* s in [-100, 100]: s >> 2 in [-25, 25] (case split on the sign) */
void shr_mixed(int s) {
  if (s >= -100 && s <= 100) {
    int t = s >> 2;
    arr[(t + 28) / 8] = 1;
  }
}

/* variable shift amount: unconstrained, index-upper-bound open */
void shr_var(unsigned int u, unsigned int k) {
  if (k < 32) {
    arr[u >> k] = 1;
  }
}
