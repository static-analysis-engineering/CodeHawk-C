/* Issue 51: in the sym_pointersets domain, a pointer copied from a value
   that may be null keeps the null region. Previously the copy of a pointer
   parameter (f = (F *)b, with the orakel value of b a memory address) got
   only the region of the address, and an unknown pointer value only an
   uninterpreted region, so f == NULL was infeasible and the then-branch
   unreachable (sym_pointersets), including the write through err, which is
   reachable. */

#include <stddef.h>

typedef struct { int lastErr; } F;

/* bzip2 BZ_SETERR in BZ2_bzWriteClose64 */
void copy_of_parameter(int *err, void *b) {
  F *f = (F *)b;
  if (f == NULL) {
    if (err != NULL) *err = 1;       /* reachable */
    return;
  }
  f->lastErr = 0;
}

/* an unknown pointer value (from an integer) may be null */
void unknown_pointer_value(int *err, long n) {
  F *f = (F *)n;
  if (f == NULL) {
    if (err != NULL) *err = 1;       /* reachable */
    return;
  }
  f->lastErr = 0;
}
