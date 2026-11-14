/* Issue 29: unsigned left shift is reduced modulo 2^N (C11 6.5.7p4).
   Previously E1 << E2 was evaluated over the unbounded integers, which
   proved divisions by zero safe (shl_wrap, shl_wrap_const: v == 2^36 instead
   of 0), and constant folding in xsimplify overflowed the OCaml int for
   values >= 2^62. */

int arr[10];

/* v == 0: not-zero violation (previously safe with v == 64424509440) */
int shl_wrap(unsigned int u) {
  unsigned int v;
  u = 0xF0000000u;
  v = u << 4;
  return 10 / v;
}

/* same, constant folded */
int shl_wrap_const(void) {
  unsigned int v = 0xF0000000u << 4;
  return 10 / v;
}

/* no wrap: v == 2 * u <= 4, the access is safe */
void shl_nowrap(unsigned int u) {
  if (u < 3) {
    unsigned int v = u << 1;
    arr[v + 3] = 1;
  }
}

/* may wrap: index-upper-bound open */
void shl_maywrap(unsigned int u) {
  unsigned int v = u << 1;
  arr[v] = 1;
}

/* variable shift amount: result in [0, UINT_MAX], index-upper-bound open */
void shl_var(unsigned int u, unsigned int k) {
  if (k < 32) {
    unsigned int v = u << k;
    arr[v] = 1;
  }
}

/* 2^63 << 1 == 0 modulo 2^64: not-zero violation */
int shl_wrap_64(void) {
  unsigned long long w = 0x8000000000000000ULL << 1;
  return 10 / (int) w;
}

/* 2^61 << 2 == 2^63 (exceeds the OCaml int): w != 0, not-zero safe */
int shl_large_64(void) {
  unsigned long long w = 0x2000000000000000ULL << 2;
  return 10 / (w != 0);
}
