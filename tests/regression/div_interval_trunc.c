/* Issue 31b: CHIF DIV is C division, truncated toward zero (C11 6.5.5p6).
   The interval domain now evaluates it with truncation at the corners,
   which is exact for a divisor interval that excludes zero; previously it
   took floor for the lower and ceiling for the upper bound, one too wide
   whenever the divisor does not divide the bound. */

int arr[8];

/* x in [-7, 9]: x / 2 in [-3, 4] (was [-4, 5]): index safe */
void div_mixed(int x) {
  if (x >= -7 && x <= 9) {
    int q = x / 2;
    arr[q + 3] = 1;
  }
}

/* x in [-7, 9], d in [2, 3]: x / d in [-3, 4] (was [-4, 5]): index safe */
void div_mixed_var(int x, int d) {
  if (x >= -7 && x <= 9 && d >= 2 && d <= 3) {
    int q = x / d;
    arr[q + 3] = 1;
  }
}

/* x in [-9, 7], d in [-3, -2]: x / d in [-3, 4] (was [-4, 5]): index safe */
void div_neg_divisor(int x, int d) {
  if (x >= -9 && x <= 7 && d >= -3 && d <= -2) {
    int q = x / d;
    arr[q + 3] = 1;
  }
}

/* u <= 100: u / 16 <= 6 (was 7): index safe */
void div_unsigned(unsigned int u) {
  if (u <= 100) {
    arr[u / 16 + 1] = 1;
  }
}

/* x in [-15, -1]: x / 16 == 0 on every execution (was [-1, 0]):
   not-zero violation */
int div_neg_small(int x) {
  if (x >= -15 && x <= -1) {
    int q = x / 16;
    return 10 / q;
  }
  return 0;
}

/* x in [-16, -1]: x / 16 in [-1, 0]: not-zero open */
int div_neg_range(int x) {
  if (x >= -16 && x <= -1) {
    int q = x / 16;
    return 10 / q;
  }
  return 0;
}
