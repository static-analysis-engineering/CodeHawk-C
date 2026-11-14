/* Issue 21: unsigned arithmetic (+, -, *, unary -) and integer conversions
   nested in larger expressions, conditions and proof-obligation arguments
   are reduced modulo 2^N (C11 6.2.5p9, 6.3.1.3). Previously they were
   evaluated over the unbounded integers, which proved out-of-bounds accesses
   safe (index_wrap, rhs_wrap, neg_wrap: "index: -1") and reported false
   violations (mult_wrap: b == 2^32). */

#include <stdint.h>

int arr[10];

/* condition: u - 1 == UINT_MAX, the test is false; arr[u + 10] is reached
   and out of bounds */
int cond_wrap(void) {
  unsigned int u = 0;
  if (u - 1 < 10) {
    return 0;
  }
  arr[u + 10] = 1;
  return 1;
}

/* index: (u - 1) / 2 == 2^31 - 1: out of bounds */
int index_wrap(void) {
  unsigned int u = 0;
  return arr[(u - 1) / 2];
}

/* index with a parameter: u == 0 gives UINT_MAX: not safe */
int param_index_wrap(unsigned int u) {
  if (u > 5) {
    return 0;
  }
  return arr[u - 1];
}

/* nested in an assignment: (u - 1) / 2 == 2^31 - 1 */
int rhs_wrap(void) {
  unsigned int u = 0;
  unsigned int v = (u - 1) / 2;
  if (v < 10) {
    return 0;
  }
  arr[v] = 1;
  return 1;
}

/* multiplication: 65536 * 65536 == 0 */
int mult_wrap(void) {
  unsigned int a = 65536;
  unsigned int b = a * a;
  if (b < 10) {
    arr[b] = 1;
    return 1;
  }
  return arr[b];
}

/* unsigned negation: -1U == UINT_MAX */
int neg_wrap(void) {
  unsigned int u = 1;
  unsigned int v = -u;
  if (v < 10) {
    return 0;
  }
  arr[v] = 1;
  return 1;
}

/* cast nested in a condition: (uint8_t)300 == 44 */
int cast_cond(void) {
  int x = 300;
  if ((uint8_t)x > 100) {
    return 0;
  }
  arr[x - 291] = 1;   /* x - 291 == 9: safe */
  return 1;
}

/* no wrap: the guards keep the nested subtraction in range */
int nowrap(unsigned int u) {
  if (u >= 1 && u <= 10) {
    return arr[u - 1];
  }
  return 0;
}
