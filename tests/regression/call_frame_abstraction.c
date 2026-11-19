/* Regression test for issue 45: the call frame.

   A callee can change memory that it does not receive as an argument:
   memory reached through pointer parameters, return values or pointers stored
   in memory (external memory), and locals whose address escaped (stored in
   memory or passed to an earlier call). Previously only the regions directly
   addressed by the arguments and the globals were abstracted at a call
   without library summary, so the index proof obligations in the first seven
   functions were proven safe, also when the callee is defined in this file
   (ext_param_defined, escaped_defined). Now they are open.

   Not affected (still safe): locals whose address does not escape (only
   dereferenced directly, or passed to a library function with a summary such
   as memset, which is trusted not to keep the pointer), and external memory
   across a call to a library function with a summary.
 */
#include <string.h>
#include <sys/uio.h>

struct S { int n; int buf[10]; };
struct T { int *p; int n; };

extern void ext(struct S *s);
extern void ext_noargs(void);
extern void reg(int *p);
extern struct S *get(void);

struct S *gp;
int *gx;

static void mod(void) { gp->n = 100; }
static void modx(void) { *gx = 100; }

/* external memory through a parameter: open */
int ext_param(struct S *s) {
  if (s->n >= 0 && s->n < 10) { ext_noargs(); return s->buf[s->n]; }
  return 0;
}

/* the same with a defined callee that writes *s through an alias: open */
int ext_param_defined(struct S *s) {
  gp = s;
  if (s->n >= 0 && s->n < 10) { mod(); return s->buf[s->n]; }
  return 0;
}

/* external memory through a return value: open */
int ext_return(void) {
  struct S *q = get();
  if (q->n >= 0 && q->n < 10) { ext_noargs(); return q->buf[q->n]; }
  return 0;
}

/* local whose address escaped through an earlier call: open */
int escaped_call(void) {
  int a[10];
  int x = 0;
  reg(&x);
  x = 5;
  ext_noargs();
  a[x] = 1;
  return a[0];
}

/* local whose address escaped through a global, defined callee: open */
int escaped_defined(void) {
  int a[10];
  int x = 0;
  gx = &x;
  modx();
  a[x] = 1;
  return a[0];
}

/* depth 2: unmodeled library function writes through iov[0].iov_base: open */
int depth2_library(int fd) {
  int x = 0;
  int a[10];
  struct iovec iov[1];
  iov[0].iov_base = &x;
  iov[0].iov_len = sizeof(x);
  readv(fd, iov, 1);
  a[x] = 1;
  return a[0];
}

/* depth 2: through a pointer stored in a local struct: open */
int depth2_struct(void) {
  int x = 0;
  int a[10];
  struct T t;
  t.p = &x;
  t.n = 0;
  ext((struct S *)&t);
  a[x] = 1;
  return a[0];
}

/* local whose address is not taken: safe */
int local_kept(void) {
  int a[10];
  int x = 5;
  ext_noargs();
  a[x] = 1;
  return a[0];
}

/* address passed only to a summarized library function: safe */
int local_library_arg(void) {
  int a[10];
  int x;
  memset(&x, 0, sizeof(x));
  x = 3;
  ext_noargs();
  a[x] = 1;
  return a[0];
}

/* external memory across a summarized library call: safe */
int ext_param_library(struct S *s, char *b) {
  if (s->n >= 0 && s->n < 10) { memset(b, 0, 4); return s->buf[s->n]; }
  return 0;
}
