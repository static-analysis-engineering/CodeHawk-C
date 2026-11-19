/* Issue 52: the array of a string literal has strlen + 1 elements, including
   the null terminator, and all of them are initialized (C11 6.4.5p6); a
   pointer may point one past the end of the array (C11 6.5.6p8). Reading
   strlen + 1 bytes from a literal is valid; reading more is a violation. */

#include <string.h>

/* reads "abc" including its null terminator (4 bytes): safe */
void copy_with_terminator(void) {
  char buf[8];
  memcpy(buf, "abc", 4);
}

/* reads 5 bytes from a 4-byte literal array: violation (ptr-upper-bound and
   initialized-range) */
void copy_past_literal(void) {
  char buf[8];
  memcpy(buf, "abc", 5);
}
