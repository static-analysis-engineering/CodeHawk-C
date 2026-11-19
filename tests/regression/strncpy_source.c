/* Issue 3: strncpy reads characters from its source up to and including the
   null character, at most n (C11 7.24.2.4p2): the source need not have n
   readable bytes. The library summary requires
   deref-read(s2, min(n, nullterminator-pos(s2) + 1)): the read is in bounds
   and initialized if either the first n bytes are, or s2 is null-terminated
   within its object. */

#include <string.h>

struct rec {
  char name[8];   /* fixed-size field, not necessarily null-terminated */
};

/* string literal shorter than n: safe (literal is null-terminated) */
void copy_literal(void) {
  char buf[32];
  strncpy(buf, "Unknown", sizeof(buf) - 1);
  buf[sizeof(buf) - 1] = '\0';
}

/* source is a parameter: the condition with the min length is delegated to
   the callers (not the stronger condition on n alone) */
static void copy_param(char *dst, const char *src) {
  strncpy(dst, src, 31);
  dst[31] = '\0';
}

/* call-site proof obligations for the delegated condition: safe for string
   literals shorter than n */
void call_copy_param(void) {
  char buf[32];
  copy_param(buf, "ES_BG_TASK");
  copy_param(buf, "--UNOWNED--");
}

/* non-terminated fixed-size source, n equal to its size: the bound is
   delegated with its min length; a caller can discharge it by the first
   alternative (n bytes within the source object) without null termination */
void copy_field(struct rec *r) {
  char buf[8];
  strncpy(buf, r->name, sizeof(r->name));
}
