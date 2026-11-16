/* Regression test for issue 36(d): globals across calls.

   Global variables are accessible to every function, so a call may modify any
   global (address-taken or not) unless a contract protects it (a const
   global-variable contract, or XPreservesValue of the global in the callee's
   side effects/postconditions). Previously the value of a global was kept
   across a call to a function without summary, whether the callee writes it
   directly or through a callback, and an unresolved indirect call was omitted
   altogether (its lhs, argument regions and globals kept their values), so
   all index-upper-bound POs below except the last two were proven safe with
   index 0. A library function with a summary (strlen) is trusted not to write
   the program's globals; locals whose address is not taken are unaffected.
 */
#include <string.h>
int arr[10];
int g;
struct st { int a; int b; } gs;
int *gp;
void ext_foreach(void (*f)(int));
void ext_noargs(void);
static void cb(int k) { g = k; }

int callback_global(void) {     /* open */
  int x = 0;
  g = 0;
  ext_foreach(cb);
  if (g == 3) { x = 12; }
  return arr[x];
}

int direct_global(void) {       /* open */
  g = 0;
  ext_noargs();
  return arr[g];
}

int global_field(void) {        /* open */
  gs.b = 0;
  ext_noargs();
  return arr[gs.b];
}

int addr_taken_global(void) {   /* open */
  int x = 0;
  gp = &g;
  g = 0;
  ext_noargs();
  if (g == 3) { x = 12; }
  return arr[x];
}

int indirect_lhs(int (*fp)(void)) {   /* open: x = fp() */
  int x = 0;
  x = fp();
  return arr[x];
}

int indirect_global(void (*fp)(void)) {  /* open */
  g = 0;
  fp();
  return arr[g];
}

int library_call(const char *s) {  /* safe: strlen has a summary, cannot write g */
  g = 0;
  (void) strlen(s);
  return arr[g];
}

int local_unaffected(void) {    /* safe: non-address-taken local */
  int y = 0;
  ext_noargs();
  return arr[y];
}
