/* Issue 43: consolidated status. A proof obligation discharged by an api
   assumption (a precondition delegated to the callers) is safe locally; it is
   proven only if the supporting proof obligations at all call sites are
   proven, transitively. Otherwise it is safe under assumptions on the
   environment (external linkage, address taken), or pending (a supporting
   proof obligation is open or fails). The status of each individual proof
   obligation is not changed. */

#include <stdlib.h>
#include <string.h>

int garr[10];

extern int ext_get(void);

/* static, only call site safe: proven */
static int read_static(int i) {
  return garr[i];
}

/* external linkage: callers outside the program are not checked: env */
int read_extern(int i) {
  return garr[i];
}

/* static, call site argument unknown: pending (open) */
static int read_open(int i) {
  return garr[i];
}

/* static, call site out of bounds: pending (finding) */
static int read_bad(int i) {
  return garr[i];
}

/* static, address taken: indirect callers have no call-site proof
   obligations: env */
static int read_addr(int i) {
  return garr[i];
}

int (*read_fp)(int) = read_addr;

/* mutual recursion, only external entry safe: proven (fixpoint) */
static int rec_a(int i, int n);

static int rec_b(int i, int n) {
  if (n > 0) {
    return rec_a(i, n - 1);
  }
  return garr[i];
}

static int rec_a(int i, int n) {
  return rec_b(i, n);
}

/* valid-mem(p) after memset rests on the library summary of memset
   (preserves-all-memory); memset is a C standard library function, whose
   summary is part of the analyzer's model of C: proven */
int lib_post(void) {
  int r;
  char *p = malloc(8);
  if (p == NULL) {
    return 0;
  }
  memset(p, 0, 8);
  r = p[0];
  free(p);
  return r;
}

/* valid-mem(p) after ext_pure rests on its declared attribute pure
   (preserves-all-memory); ext_pure is not a standard library function:
   lib */
extern int ext_pure(int x) __attribute__((pure));

int attr_post(void) {
  int r;
  char *p = malloc(8);
  if (p == NULL) {
    return 0;
  }
  p[0] = 1;
  if (ext_pure(3) > 0) {
    r = p[0];
  } else {
    r = 0;
  }
  free(p);
  return r;
}

int main(void) {
  int v = ext_get();
  read_static(3);
  read_extern(5);
  read_open(v);
  read_bad(12);
  rec_a(4, 2);
  lib_post();
  attr_post();
  return 0;
}
