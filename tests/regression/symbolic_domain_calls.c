/* Regression test for issues 36(c) and 37: symbolic domains.

   Issue 37 (symbolic-sets domain, initialization): an lval that is not
   represented by a variable (here the fields of *G.ptr) is translated to a
   temporary; conditions in this domain are translated outside a transaction,
   so both fields became the same temporary, G.ptr->cnt >= G.ptr->max
   simplified to TRUE and the else branch was dead: x looked initialized after
   the join (uninit_after_condition: initialized(x) was safe, now open).
   init_fields (fields of external memory through a parameter) is open in
   both versions. In the numerical domain, the field offset of an access
   (q + 1)->a through the initial value q of a global pointer was dropped, so
   (gq + 1)->a and (gq + 1)->b were the same variable (ptr_plus_fields:
   index-upper-bound was a violation with a == 12; now safe with a == 0).

   Issue 36(c) (symbolic pointer-set domain, nullness): a call to a function
   without summary did not abstract the pointers it may write (out-parameter,
   global, lhs of an unresolved indirect call), so after r = 0; find_rec(&r)
   r was still null and the branch r != 0 was dead in that domain
   (out_param, global_pointer, indirect_lhs). The PO statuses in those
   branches do not change (the branches are now reachable);
   stale_null_deref: not-null(r) stays open.

   Type-punned accesses (issue 35) in the symbolic-sets domain: a write of
   one byte of an int was recorded as an assignment of the int, so
   initialized(e) was proven safe in partial_init (now open; the other bytes
   are indeterminate, C11 6.2.6.1).
 */

struct counts { unsigned int cnt; unsigned int max; };
struct glob { struct counts *ptr; } G;
struct pair { int a; int b; };
struct rec { int v; };

int arr[10];
struct rec *gp;
struct pair *gq;

void find_rec(struct rec **out, int k);
void ext_noargs(void);
struct rec *(*get_rec)(void);

int uninit_after_condition(void) {   /* initialized(x) open */
  int x;
  if (G.ptr->cnt >= G.ptr->max) {
    x = 1;
  }
  return x;
}

int init_fields(struct counts *p) {   /* initialized(x) open */
  int x;
  if (p->cnt >= p->max) {
    x = 1;
  }
  return x;
}

int partial_init(void) {   /* initialized(e) open */
  int e;
  *(char *)(&e) = 1;
  return e;
}

int ptr_plus_fields(void) {   /* index-upper-bound safe */
  (gq + 1)->a = 0;
  (gq + 1)->b = 12;
  return arr[(gq + 1)->a];
}

int out_param(int k) {
  struct rec *r = 0;
  find_rec(&r, k);
  if (r != 0) {
    return r->v;
  }
  return 0;
}

int stale_null_deref(int k) {   /* not-null(r) open */
  struct rec *r = 0;
  find_rec(&r, k);
  return r->v;
}

int global_pointer(void) {
  gp = 0;
  ext_noargs();
  if (gp != 0) {
    return gp->v;
  }
  return 0;
}

int indirect_lhs(void) {
  struct rec *r = 0;
  r = get_rec();
  if (r != 0) {
    return r->v;
  }
  return 0;
}
