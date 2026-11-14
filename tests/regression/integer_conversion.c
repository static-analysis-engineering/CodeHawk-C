/* Issue 21: integer conversions (C11 6.3.1.3) are not the identity on
   unbounded integers. The analyzer models the conversion result: reduction
   modulo 2^N for unsigned targets, GCC's documented reduction modulo 2^N for
   (implementation-defined) out-of-range signed targets, and 0/1 for _Bool.
   Previously the cast was the identity, which made the analysis unsound
   (narrow_index: arr[v] treated as dead code) or imprecise (the others). */

#include <stdint.h>

int arr[10];

/* (uint16_t)-1 == 65535: arr[v] is out of bounds (violation) */
int narrow_index(void) {
  int x = -1;
  uint16_t v = (uint16_t)x;
  if (v < 10) {
    return 0;
  }
  arr[v] = 1;
  return 1;
}

/* GCC: (int32_t)0xc400000aU == -1006632950 < 0, so arr[s] is unreachable */
int status_sign(void) {
  int32_t s = (int32_t)0xc400000aU;
  if (s >= 0) {
    arr[s] = 1;
    return 1;
  }
  return 0;
}

/* GCC: (int)(2^32 + 3) == 3: arr[i] is safe */
int narrow_long(void) {
  long l = 4294967296L + 3L;
  int i = (int)l;
  arr[i] = 1;
  return 0;
}

/* (_Bool)2 == 1: arr[b + 8] is arr[9], safe */
int bool_conv(void) {
  _Bool b = (_Bool)2;
  arr[b + 8] = 1;
  return 0;
}

/* widening conversion: no correction, the guard is kept: safe */
void widen(unsigned char c) {
  int i = c;
  if (i < 10) {
    arr[i] = 0;
  }
}
