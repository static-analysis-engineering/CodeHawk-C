/* Issue 27 (a): a store into a bit-field of width w keeps the low w bits:
   the value is reduced modulo 2^w into [0, 2^w - 1] for an unsigned field
   (C11 6.3.1.3p2) and into [-2^(w-1), 2^(w-1) - 1] for a signed field
   (implementation-defined, 6.3.1.3p3; gcc: modulo 2^w). Previously the
   width was ignored. Not covered: promotion of bit-field operands to int
   (6.3.1.1p2), issue 27 (c). */

struct s { unsigned int f : 3; int g : 4; };
int arr[10];

/* p->f = 9 stores 1: index safe (previously a violation, index 11) */
void store_trunc(struct s *p) {
  p->f = 9;
  arr[p->f + 2] = 1;
}

/* p->f = 8 stores 0: not-zero violation (previously safe) */
int store_zero(struct s *p) {
  p->f = 8;
  int v = p->f;
  return 10 / v;
}

/* p->g = 12 stores -4 (gcc): index-lower-bound violation */
void store_signed(struct s *p) {
  p->g = 12;
  arr[p->g + 2] = 1;
}

/* in range: unchanged */
void store_inrange(struct s *p) {
  p->f = 5;
  arr[p->f] = 1;
}

/* any unsigned value: p->f in [0, 7] after the store, index safe */
void store_var(struct s *p, unsigned int u) {
  p->f = u;
  arr[p->f + 2] = 1;
}
