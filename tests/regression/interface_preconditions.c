/* Verification pass, interface preconditions: the declared preconditions
   of an exported function are part of the interface of the module.
   - sum (exported, chkc_nonnull(1)): not-null(p) is discharged by the
     declared precondition (consolidated: trust-interface); the conditions
     it would need beyond that (not-null(q) for the call get_x(q), and the
     initializedness of p->x and q->x) cannot be delegated: they stay open
     and are reported as missing preconditions (remedy missing-precondition);
   - get_x (static, not exported) delegates not-null(r) to its callers as
     before; its proof obligation depends on the open call-site supporting
     proof obligation in sum;
   - use_ok, use_null: calls to an exported function in the defining file
     check the declared precondition by a primary proof obligation (as at
     calls from other files and modules), proven for &g, a violation for a
     null pointer; no call-site supporting proof obligations are created. */

struct S { int x; };
static struct S g;

int sum(struct S *p, struct S *q) __attribute__((chkc_exported, chkc_nonnull(1)));

static int get_x(struct S *r) { return r->x; }   /* not exported: delegates */

int sum(struct S *p, struct S *q) {
  return p->x + get_x(q);
}

int use_ok(void) { return sum(&g, &g); }
int use_null(struct S *a) { return sum((struct S *)0, a); }
