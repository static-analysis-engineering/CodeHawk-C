/* Regression test for issue 35: memory accesses whose type differs from the
   type of the accessed object, and pointer arithmetic on addresses.

   Previously *(char *)&e was translated as the int variable e itself, so the
   byte read in pun_read had value 0x01020304 != 4, the branch was proven
   unreachable and index-upper-bound(x) was proven safe with x == 0 (on
   x86-64, x == 12). Such accesses now have an unknown value (reads) or
   abstract the object (writes).

   Pointer arithmetic on a known address appended an index instead of
   shifting the last index: *(p + 1) with p = &a[0] was a variable distinct
   from a[1] (ptr_plus_write proved arr[a[1]] safe with a[1] == 0), and the
   field offset of (p + 1)->b was dropped.
 */

int arr[10];

int pun_read(void) {            /* index-upper-bound(x): open */
  int e = 0x01020304;
  int x = 0;
  if ((*(char *)(&e)) == 0x04) { x = 12; }
  return arr[x];
}

int pun_write(void) {           /* index-upper-bound(e): open */
  int e = 0;
  *(char *)(&e) = 12;
  return arr[e];
}

int pun_plus_read(void) {       /* open */
  int e = 0x0c000000;
  return arr[*((char *)(&e) + 3)];
}

int ptr_plus_write(void) {      /* index-upper-bound(a[1]): violation (12) */
  int a[4];
  int *p = &a[0];
  a[1] = 0;
  *(p + 1) = 12;
  return arr[a[1]];
}

struct pair { int a; int b; };

int ptr_plus_field(void) {      /* (p + 1)->a: safe (0); (p + 1)->b: violation (12) */
  struct pair s[2];
  struct pair *p = &s[0];
  s[1].a = 0;
  s[1].b = 12;
  return arr[(p + 1)->a] + arr[(p + 1)->b];
}

struct state { unsigned int timer; unsigned int credit; };

int void_arg_state(unsigned int elapsed, void *arg) {
  /* external memory reached through void *: typed by the access;
     uint-underflow safe by the guard */
  struct state *st = (struct state *)arg;
  if (st->timer > elapsed) {
    st->timer -= elapsed;
    return 1;
  }
  return 0;
}
