/* Issue 15 (Part A): a proof obligation whose condition fails gets the status
   of the category of behavior that results: violation (undefined behavior),
   implementation-defined (conversion to a signed type of a value that is not
   representable, C11 6.3.1.3p3), or value-wrap-around (unsigned arithmetic,
   C11 6.2.5p9; conversion to an unsigned type, C11 6.3.1.3p2). All proof
   obligations are generated and checked at every analysis level; the level
   (chkc report --analysis-level) only selects what is reported. */

#include <stdint.h>

int arr[10];

/* undefined behavior: index-upper-bound violation */
int ub_index(void) {
  int i = 12;
  return arr[i];
}

/* implementation-defined: unsigned-to-signed-cast */
int impl_unsigned_to_signed(void) {
  unsigned int u = 0xc400000aU;
  return (int)u;
}

/* implementation-defined: signed-to-signed-cast-ub */
int8_t impl_signed_narrow(void) {
  int x = 300;
  return (int8_t)x;
}

/* value wrap-around: signed-to-unsigned-cast-lb */
unsigned int wrap_negative_to_unsigned(void) {
  int x = -1;
  return (unsigned int)x;
}

/* value wrap-around: unsigned-to-unsigned-cast */
uint8_t wrap_unsigned_narrow(void) {
  unsigned int u = 300;
  return (uint8_t)u;
}

/* value wrap-around: uint-underflow */
unsigned int wrap_underflow(void) {
  unsigned int a = 0;
  return a - 1;
}

/* value wrap-around: uint-overflow */
unsigned int wrap_overflow(void) {
  unsigned int a = 4294967295U;
  return a + 1;
}
