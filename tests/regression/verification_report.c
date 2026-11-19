/* Regression test for the verification report (issue 15, part A;
   chkc c-project verification-report).

   Boundary: ext_value and ext_ptr are called but neither defined nor
   summarized (unmodeled: effects havocked, preconditions not checked); fp is
   an indirect call; memset is a C standard library function with a
   summary (part of the analyzer's model).

   Open proof obligations by remedy:
   - call-site: the index proof obligations of lookup are delegated to its
     callers; the call site in use_lookup passes a value returned by
     ext_value, so the supporting proof obligations are open;
   - external-condition: *ext_ptr() needs a condition on the return value of
     ext_ptr (not-null), which only the user can provide;
   - program-postcondition: valid-mem(p) after the call to prog_fn needs a
     postcondition of prog_fn (preserves-all-memory);
   - global-state: g_arr[g_idx] depends on the value of the global g_idx.

   Findings: a[10] is a violation; (int)u with u >= 0xfffffffe is
   implementation-defined (C11 6.3.1.3p3).
 */
#include <string.h>

extern int ext_value(void);
extern int *ext_ptr(void);

int g_idx;
int g_arr[10];
int (*fp)(int);

static int lookup(int *a, int i) {
  return a[i];
}

int use_lookup(void) {
  int a[10];
  memset(a, 0, sizeof(a));
  return lookup(a, ext_value());
}

int external_condition(void) {
  int *p = ext_ptr();
  return *p;
}

void prog_fn(void) {
  g_idx = 0;
}

int program_postcondition(int *p) {
  prog_fn();
  return *p;
}

int global_state(void) {
  return g_arr[g_idx];
}

int indirect(void) {
  return fp(3);
}

int violation(void) {
  int a[10];
  a[10] = 0;
  return a[0];
}

int implementation_defined(int k) {
  unsigned int u = 0xffffffffu;
  if (k > 0) {
    u = 0xfffffffeu;
  }
  return (int)u;
}
