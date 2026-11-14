/* Unsigned 64-bit constants >= 2^63 are stored by the parser as int64 in
   two's-complement form (0xffffffffffffffffUL as -1, 0x8000000000000000UL as
   -2^63, with an unsigned ikind). The analyzer must read them as 2^64 - 1 and
   2^63; read as -1 and -2^63, the index-upper-bound obligations below are
   (unsoundly) proven safe ("index: -1 and bound: 10 satisfy (-1 < 10)").
   Both accesses are out of bounds on every execution. */

int arr[10];

int max_index(void) {
  unsigned long x = 0xffffffffffffffffUL;
  arr[x] = 1;
  return 0;
}

int high_bit_index(void) {
  unsigned long y = 0x8000000000000000UL;
  arr[y] = 1;
  return 0;
}

int small_index(void) {
  unsigned long z = 9UL;
  arr[z] = 1;
  return 0;
}
