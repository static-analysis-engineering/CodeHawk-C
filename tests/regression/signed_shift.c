/* Issue 29: signed left shift (C11 6.5.7p4): E1 << E2 with E1 of signed
   type is defined only if E1 >= 0 and E1 * 2^E2 is representable in the
   result type (the promoted type of E1). Proof obligations
   non-negative(E1) and int-overflow(E1, E2, op:shiftlt) are generated;
   previously only non-negative(E2) and width-overflow(E2) were. */

#include <stdint.h>

/* 2^30: safe */
int c_ok(void) { return 1 << 30; }

/* 2^31 > INT_MAX: int-overflow violation */
int c_ovf(void) { return 1 << 31; }

/* negative left operand: non-negative(-1) violation */
int c_neg(void) { return -1 << 1; }

/* k == 2^30, k << 1 == 2^31: int-overflow violation */
int v_ovf(int k) { k = 0x40000000; return k << 1; }

/* k <= 999: k << 4 <= 15984, safe */
int v_ok(int k) { if (k >= 0 && k < 1000) return k << 4; return 0; }

/* k unbounded above: delegated to the caller */
int v_open(int k) { if (k >= 0) return k << 4; return 0; }

/* k == -3: non-negative(k) violation (universal: upper bound negative) */
int v_neg(int k) { k = -3; return k << 2; }

/* uint8_t is promoted to int: b << 24 overflows for b >= 128 (delegated);
   b << 23 and b << 24 with b < 128 are safe */
int byte24(uint8_t b) { return b << 24; }
int byte23(uint8_t b) { return b << 23; }
int byte24ok(uint8_t b) { if (b < 128) return b << 24; return 0; }

/* variable shift amount: 15 << 26 <= INT_MAX, safe */
int varamt(int k, int n) {
  if (k >= 0 && k < 16 && n >= 0 && n < 27) return k << n;
  return 0;
}

/* delegation: deleg(1 << 29) violates the delegated condition at the call
   site (2^31), deleg(5) satisfies it */
int deleg(int k) { return k << 2; }
int caller(void) { return deleg(1 << 29) + deleg(5); }

/* unsigned: no int-overflow PO (reduced modulo 2^N) */
unsigned int ushl(unsigned int u) { return u << 4; }

/* 64-bit: 9 << 40 <= LLONG_MAX, safe */
long long ll(int k) { if (k >= 0 && k < 10) return (long long)k << 40; return 0; }

/* memory read without invariant: (int)p[0] << 8 <= 255 * 2^8, safe by the
   range of the promoted type uint8_t */
int rd(const uint8_t *p) { return (p[0] << 8) | p[1]; }
