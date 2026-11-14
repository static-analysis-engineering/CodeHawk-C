/* Word size regression test (CodeHawk-C analyzer issue: parse/analysis word
   size mismatch). The analyzer must use the machine model the file was
   parsed for (recorded in <name>.cch/a/target_platform.json):
   - LP64  (-m64): sizeof(unsigned long) == 8
   - ILP32 (-m32): sizeof(unsigned long) == 4
   Copied values are not read, to keep the initialized checks out of it. */

#include <string.h>
#include <stdint.h>

unsigned long gl;

/* safe on LP64 and ILP32: uint64_t is 8 bytes on both */
void copy_uint64(void) {
  unsigned char buf[8] = {0};
  uint64_t v;
  memcpy(&v, buf, 8);
}

/* safe on LP64; ptr-upper-bound violation on ILP32 (8 bytes into 4) */
void copy_ulong8(void) {
  unsigned char buf[8] = {0};
  unsigned long v;
  memcpy(&v, buf, 8);
}

/* the array length is folded by the parser (CIL), with the machine model of
   the parse platform: safe on LP64, ptr-upper-bound violation on ILP32
   (with CIL's host model, an ILP32 parse would fold sizeof(long) to 8) */
void copy_long_array(void) {
  unsigned char src[8] = {0};
  char buf[sizeof(long)];
  memcpy(buf, src, 8);
}

/* unsigned long -> unsigned int may lose value on LP64: must not be proven
   safe from the type range (nothing is known about gl) */
unsigned int narrow_ulong(void) {
  return (unsigned int) gl;
}
