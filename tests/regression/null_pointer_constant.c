/* Issue 60: not-null of a null pointer constant (C11 6.3.2.3p3) was proven
   safe as an "absolute address in memory", and so was any integer variable
   converted to a pointer. Now:
   - 0 converted to a pointer (directly, via void *, via NULL, via a pointer
     typedef) is a violation of not-null: deref_null_literal,
     deref_null_macro, write_null, deref_null_typedef, and the return site of
     ret_null that returns null although it guarantees returns_nonnull;
   - a nonzero constant is an absolute address: deref_absolute (safe);
   - an integer variable converted to a pointer is not evidence of a
     non-null pointer: deref_int_var (delegated to the callers),
     deref_int_positive (open; its range is not derived syntactically);
   - deref_null_var (p = NULL; p->f) stays open;
   - offset_of: offsetof (gcc: __builtin_offsetof, translated by CIL into
     (size_t) &((struct s *) 0)->f) gets no proof obligations: no
     violation. */

#include <stddef.h>
struct s { int f; };

int deref_null_literal(void) {
  return ((struct s *)0)->f;
}

int deref_null_macro(void) {
  return ((struct s *)NULL)->f;
}

void write_null(void) {
  *(int *)0 = 1;
}

int deref_null_var(void) {
  struct s *p = NULL;
  return p->f;
}

typedef struct s *sptr_t;

int deref_null_typedef(void) {
  return ((sptr_t)0)->f;
}

int deref_absolute(void) {
  return ((struct s *)0x40000000)->f;
}

int deref_int_var(unsigned long a) {
  return ((struct s *)a)->f;
}

int deref_int_positive(unsigned long a) {
  return ((struct s *)(a | 1UL))->f;
}

struct s *ret_null(int c) __attribute__((chkc_exported, returns_nonnull));
static struct s g;
struct s *ret_null(int c) {
  if (c) return &g;
  return (struct s *)(void *)0;
}

size_t offset_of(void) {
  return offsetof(struct s, f);
}
