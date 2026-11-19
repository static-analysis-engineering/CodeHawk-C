/* Issue 50: an lval with a non-constant index (a[i], s->arr[i]) does not
   denote a single location. A read of it is an unknown value, a condition on
   it constrains nothing, and a write to it may change every element of the
   same array (but not other fields of the same struct).

   Previously all elements a[i] shared one variable (a[variable-index]) that
   was read and constrained as a single value, and an element accessed
   through a pointer (s->arr[i]) was named by the index expression itself
   and kept its facts after i changed; a write to a[i] of a local array
   whose address is not taken did not change a[0]. */

#include <stddef.h>

static int incs[4] = { 1, 4, 13, 40 };
int garr[10];

/* bzip2 mainSimpleSort: the loop-exit fact incs[hp] >= bigN held for every
   element, also after hp--, so i > hi and the deref of ptr was unreachable
   (pepr) */
int exit_fact_after_decrement(int lo, int hi, int *ptr) {
  int bigN = hi - lo + 1, hp = 0, h, i;
  if (bigN < 2 || bigN > 40) return 0;
  while (incs[hp] < bigN) hp++;
  hp--;
  h = incs[hp];
  i = lo + h;
  if (i > hi) return 1;
  return *ptr;                       /* reachable */
}

struct S { int arr[8]; };

/* s->arr[i] after i++ is a different element: the deref of p was
   unreachable (intervals, pepr) */
int element_after_increment(struct S *s, int i, int *p) {
  if (i < 0 || i >= 7) return 0;
  if (s->arr[i] < 5) {
    i++;
    if (s->arr[i] >= 5) return *p;   /* reachable */
  }
  return 4;
}

/* a write to a[i] may change a[0] (i == 0): the index of garr is not known;
   previously a[0] == 20 survived the write and index-upper-bound was a
   violation */
int write_changes_constant_element(int i) {
  int a[10];
  a[0] = 20;
  if (i < 0 || i >= 10) return 0;
  a[i] = 3;
  return garr[a[0]];                 /* index bounds open */
}

struct B { int n; unsigned char buf[16]; };

/* a write to s->buf[s->n] does not change the field s->n: both index
   bounds of buf are safe */
int write_keeps_other_field(struct B *s, int k) {
  s->n = 0;
  while (k > 0 && s->n < 16) {
    s->buf[s->n] = 1;
    s->n++;
    k--;
  }
  return s->n;
}

/* a write to s->buf[i] may change s->buf[0]: the deref of p is reachable
   (i == 0) */
int write_changes_same_field(struct B *s, int i, int *p) {
  s->buf[0] = 1;
  if (i < 0 || i >= 16) return 0;
  s->buf[i] = 2;
  if (s->buf[0] == 2) return *p;     /* reachable */
  return 1;
}
