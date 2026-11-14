/* Issue 22: a proof obligation is a violation only if the property fails on
   every execution that reaches the statement, or if there is a witness (a
   value that can be chosen, e.g., a tainted input). Interval bounds are
   over-approximations: a bound that violates the property need not be
   attained. With the type ranges of int parameters known, the analyzer
   reported violations for:
   - narrow:   (char)ch                      signed-to-signed-cast-lb
   - fill:     memset(buf, 0, n), int n      ptr-upper-bound (lower bound of n
               negative; upper bound INT_MAX exceeds the buffer)
   - divide:   x / d, unsigned d             not-zero (lower bound 0)
   - loop:     index i <= 10 into int[10]    index-upper-bound (upper bound 10)
   All of these are open: there is no witness, and the bound need not be
   attained (for loop it is, but the analysis has no witness for it).
   always_negative is a real violation: n is -1 on every execution. */

#include <stdlib.h>
#include <string.h>

char narrow(int ch) {
  return (char)ch;
}

void fill(int n) {
  char *buf = malloc(16);
  if (buf == NULL) return;
  memset(buf, 0, n);
  free(buf);
}

unsigned int divide(unsigned int x, unsigned int d) {
  return x / d;
}

int arr[10];

void loop(void) {
  for (int i = 0; i <= 10; i++) {
    arr[i] = 0;
  }
}

void always_negative(void) {
  char buf[16];
  int n = -1;
  memset(buf, 0, n);
}
