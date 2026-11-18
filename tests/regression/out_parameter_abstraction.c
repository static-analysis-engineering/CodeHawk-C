/* Regression test for issue 36: objects whose address is passed to a callee
   without known side effects must be abstracted at the call.

   Previously only arguments of the exact form &lval / lval (array) were
   abstracted, and only the variable for lval itself, so that
   - (void *)&c and (void *)buf (the usual form for read-like functions),
   - a pointer variable holding an address (p = &v; f(p)),
   - the fields of a struct passed as &s
   kept their values across the call, and the index POs below were proven safe
   with x == 0 although the callee may make x == 12.

   field_sibling: s.b was kept across ext_int(&s.a) as not reachable from the
   argument. Since issue 45 the whole of s is abstracted: its address escapes
   to ext_int, and a pointer to the first member, suitably converted, points
   to the structure object (C11 6.7.2.1p15), so the callee may write s.b.
 */

int arr[10];
int ext_read(int fd, void *buf, int n);
void ext_set(int *p);
struct pair { int a; int b; };
void ext_pair(struct pair *p);
void ext_int(int *p);

int void_out(int fd) {          /* (void *)&c: index-upper-bound(x) open */
  char c = 0;
  ext_read(fd, &c, 1);
  int x = 0;
  if (c == ',') { x = 12; }
  return arr[x];
}

int ptr_copy(void) {            /* p = &v; ext_set(p): open */
  int v = 0;
  int *p = &v;
  ext_set(p);
  int x = 0;
  if (v == 3) { x = 12; }
  return arr[x];
}

int struct_out(void) {          /* fields of &s: open */
  struct pair s;
  s.a = 0;
  ext_pair(&s);
  int x = 0;
  if (s.a == 3) { x = 12; }
  return arr[x];
}

int field_out(void) {           /* &s.a: open */
  struct pair s;
  s.a = 0; s.b = 0;
  ext_int(&s.a);
  int x = 0;
  if (s.a == 3) { x = 12; }
  return arr[x];
}

int array_out(int fd) {         /* (void *)buf: open */
  char buf[4];
  buf[0] = 0;
  ext_read(fd, buf, 4);
  int x = 0;
  if (buf[0] == 'a') { x = 12; }
  return arr[x];
}

int field_sibling(void) {       /* s escapes to ext_int: open */
  struct pair s;
  s.a = 0; s.b = 3;
  ext_int(&s.a);
  return arr[s.b];
}
