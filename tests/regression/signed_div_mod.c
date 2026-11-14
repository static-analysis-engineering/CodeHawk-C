/* Issue 32: C division truncates toward zero and the remainder has the sign
   of the dividend (C11 6.5.5p6): -7 / 2 == -3, -7 % 4 == -3. Previously
   constants were folded with Euclidean division (-7 / 2 == -4), x % b was
   assumed to be in [0, b - 1], and comparisons with x / b were rewritten as
   if the division were exact. */

int arr[10];

/* -7 / 2 == -3: not-zero violation (previously safe with b == -4) */
int div_neg_const(void) {
  int a = -7;
  int b = a / 2;
  return 10 / (b + 3);
}

/* -7 % 4 == -3: not-zero violation (previously safe with m == 1) */
int mod_neg_const(void) {
  int a = -7;
  int m = a % 4;
  return 10 / (m + 3);
}

/* x in [-10, 10]: x % 4 in [-3, 3]: index-lower-bound open (previously
   safe with m in [0, 3]) */
void mod_neg_var(int x) {
  if (x >= -10 && x <= 10) {
    int m = x % 4;
    arr[m] = 1;
  }
}

/* x in [0, 100]: x % 10 in [0, 9]: safe */
void mod_nonneg_var(int x) {
  if (x >= 0 && x <= 100) {
    arr[x % 10] = 1;
  }
}

/* x in [-100, -1]: x % 10 in [-9, 0]: arr[x % 10 + 9] safe */
void mod_neg_range(int x) {
  if (x >= -100 && x <= -1) {
    arr[x % 10 + 9] = 1;
  }
}

/* unsigned: u % 10 in [0, 9]: safe */
void mod_unsigned(unsigned int u) {
  arr[u % 10] = 1;
}

/* x % 1000 <= x for x in [0, 5]: safe */
void mod_small(int x) {
  if (x >= 0 && x <= 5) {
    arr[x % 1000] = 1;
  }
}

/* x / 4 >= 0 iff x >= -3 (truncation): x == -1 reaches the division:
   not-zero open (previously rewritten to x >= 0: safe) */
int div_cmp_then(void) {
  int r = 0;
  for (int x = -10; x <= 10; x++) {
    if (x / 4 >= 0) {
      r += 10 / (x + 1);
    }
  }
  return r;
}

/* x / 4 < 0 iff x <= -4: x + 2 != 0: safe (previously not rewritten) */
int div_cmp_else(void) {
  int r = 0;
  for (int x = -10; x <= 10; x++) {
    if (x / 4 < 0) {
      r += 10 / (x + 2);
    }
  }
  return r;
}

/* x / 4 <= 0 iff x <= 3: x == 3 reaches arr[x + 6] == arr[9]: safe;
   x / 4 > 0 iff x >= 4: arr[x - 4] safe */
void div_cmp_le(void) {
  for (int x = 0; x <= 13; x++) {
    if (x / 4 <= 0) {
      arr[x + 6] = 1;
    } else {
      arr[x - 4] = 1;
    }
  }
}
