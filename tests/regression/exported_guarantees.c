/* Verification pass, system-boundary guarantees: functions declared
   chkc_exported belong to the external unit of their module; in the module
   that defines them their postconditions are guarantees, checked by primary
   proof obligations at the return sites (PPOguarantee), instead of the
   supporting return-site proof obligations used for other functions.

   get_s:   exported, returns_nonnull: 1 guarantee, proven; declared side
            effect preserves-all-memory reported as not checked
   find_s:  exported, returns_nonnull: 2 guarantees, 1 proven (&g), 1 open
            (result of lookup, which has no specification)
   read_x:  exported, chkc_nonnull(1): assumed in this module, the
            dereference is proven
   local_s: not exported, returns_nonnull: 2 return-site supporting proof
            obligations (1 proven, 1 open), no guarantees */

struct S { int x; };
static struct S g;

struct S *get_s(void)
  __attribute__((chkc_exported, returns_nonnull, chkc_preserves_all_memory));
struct S *find_s(int i) __attribute__((chkc_exported, returns_nonnull));
int read_x(struct S *p) __attribute__((chkc_exported, chkc_nonnull(1)));
struct S *local_s(int i) __attribute__((returns_nonnull));

extern struct S *lookup(int i);

struct S *get_s(void) { return &g; }

struct S *find_s(int i) {
  if (i == 0) return &g;
  return lookup(i);
}

int read_x(struct S *p) { return p->x; }

struct S *local_s(int i) {
  if (i == 0) return &g;
  return lookup(i);
}
