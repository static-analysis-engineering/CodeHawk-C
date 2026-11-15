/* Issue 28: conversions from and to an enumerated type are conversions from
   and to its compatible integer type (C11 6.7.2.2p4; CIL ekind, gcc's choice:
   unsigned int if no enumeration constant is negative). An object of
   enumerated type may hold any value of that type, not only the enumeration
   constants. Previously such casts got no correction (the value was taken
   unchanged) and only a cast PO that was proven by enumeration membership. */

int arr[10];

enum sgn { M = -1, A = 1 };          /* compatible type int */
enum uns { U0 = 0, U1 = 300 };       /* compatible type unsigned int */

/* lower bound of the cast delegated (x >= 0); index-upper-bound delegated */
void enum_to_uchar(enum sgn x) {
  unsigned char c = (unsigned char)x;
  arr[c] = 1;
}

/* the delegated cast lower bound is violated by M */
void call_m(void) { enum_to_uchar(M); }

/* (unsigned char)M == 255: index-upper-bound violation (previously c = -1,
   index safe) */
void enum_const_to_uchar(void) {
  enum sgn x = M;
  unsigned char c = (unsigned char)x;
  arr[c] = 1;
}

/* unsigned int to int: unsigned-to-signed cast PO delegated (previously
   proven because all enumeration constants fit into int) */
int uenum_to_int(enum uns x) {
  int i = (int)x;
  if (i < 0) return 1;
  return 0;
}

/* (enum sgn)4294967295u == -1 (gcc): not-zero(x + 1) violation (previously
   x = 4294967295, not-zero safe and a false int-overflow violation) */
int to_enum(void) {
  unsigned int u = 4294967295u;
  enum sgn x = (enum sgn)u;
  return 10 / (x + 1);
}
