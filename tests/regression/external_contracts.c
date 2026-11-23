/* Issues 62 and 66: classification of the specifications of external
   functions in the verification report.

   A specification is complete when both its effects and its preconditions
   are declared (chkc_effects_unknown and chkc_requires_none declare them
   explicitly); a library summary is complete by construction. Preconditions
   are declared only by chkc_ attributes: gcc attributes from source headers
   (nonnull, format) are used, but do not declare the axis.

   complete:  ext_full    (chkc_preserves_all_memory; chkc_nonnull)
              ext_none    (chkc_preserves_all_memory; chkc_requires_none)
              ext_unknown (chkc_effects_unknown; chkc_requires_none)
   partial:   ext_len     (pure: effects; gcc nonnull does not count)
              ext_div     (const: effects; preconditions not declared)
              ext_printf  (gcc format does not count; effects not declared)
              ext_exit    (noreturn: neither)
   unmodeled: ext_plain
   stdlib:    strlen */

#include <string.h>

int ext_div(int x, int y) __attribute__((const));
unsigned long ext_len(const char *s) __attribute__((pure, nonnull(1)));
int ext_printf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
char *ext_full(char *p)
  __attribute__((chkc_nonnull(1), chkc_preserves_all_memory,
                 returns_nonnull));
int ext_none(int x)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory));
int ext_unknown(int x)
  __attribute__((chkc_requires_none, chkc_effects_unknown));
void ext_exit(int c) __attribute__((noreturn));
int ext_plain(int x);

int use(char *s, int a, int b) {
  int r = ext_div(a, 7);
  r += (int) ext_len(s);
  r += ext_printf("%d", r);
  s = ext_full(s);
  r += ext_none(a) + ext_unknown(b) + ext_plain(a);
  r += (int) strlen(s);
  if (r < 0) ext_exit(1);
  return r;
}
