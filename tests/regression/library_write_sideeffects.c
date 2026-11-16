/* Regression test for issue 42: library functions that write through a
   pointer argument.

   Library function summaries are trusted to list all side effects of the
   function. 58 summaries of functions that write through a pointer
   argument (a deref-write precondition) had no block-write side effect, and
   others recorded the write only as initialization (memset, read, time); a
   few were wrong otherwise (strtok marked functional, sscanf without
   formatted input, no parameters for the variadic ioctl). The written
   object kept its value across the call, so in each function below except
   the last two index-upper-bound(x) was proven safe with x == 0 (now open).

   A block-write through a null pointer argument, an absent optional
   argument, or a non-pointer argument has no effect: guarded_args keeps
   x == 0 (safe), and does not lose the value of v.

   Initialization: a block write cannot make a location uninitialized, so
   initialized(buf[0]) after buf[0] = 0; snprintf (buf, ..) stays safe. (The
   former rule "value may be tainted by f" declared it a violation.) The
   4 violations are the casts of the strtol result to int.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>

int arr[10];

int write_snprintf(void) {           /* open */
  char buf[16];
  int x = 0;
  buf[0] = 0;
  snprintf(buf, sizeof(buf), "%s", "abc");
  if (buf[0] != 0) { x = 12; }
  return arr[x];
}

int write_strcpy(const char *src) {  /* open */
  char buf[16];
  int x = 0;
  buf[0] = 0;
  strcpy(buf, src);
  if (buf[0] != 0) { x = 12; }
  return arr[x];
}

int write_memset(void) {             /* open */
  char buf[16];
  int x = 0;
  buf[0] = 0;
  memset(buf, 'a', sizeof(buf));
  if (buf[0] != 0) { x = 12; }
  return arr[x];
}

int write_read(int fd) {             /* open */
  char buf[16];
  int x = 0;
  buf[0] = 0;
  if (read(fd, buf, sizeof(buf)) > 0) {
    if (buf[0] != 0) { x = 12; }
  }
  return arr[x];
}

int write_strtol_endptr(const char *s) {   /* open */
  char *end = 0;
  int x = 0;
  long v = strtol(s, &end, 10);
  if (end != 0) { x = 12; }
  return arr[x] + (int) v;
}

int write_sscanf(const char *s) {    /* open */
  int k = 0;
  int x = 0;
  sscanf(s, "%d", &k);
  if (k == 3) { x = 12; }
  return arr[x];
}

int write_time(void) {               /* open */
  time_t t = 0;
  int x = 0;
  time(&t);
  if (t != 0) { x = 12; }
  return arr[x];
}

int write_ioctl(int fd) {            /* open */
  int n = 0;
  int x = 0;
  ioctl(fd, FIONREAD, &n);
  if (n == 3) { x = 12; }
  return arr[x];
}

int write_strtok(void) {             /* open */
  char buf[8];
  int x = 0;
  buf[0] = 'a'; buf[1] = ','; buf[2] = 'b'; buf[3] = 0;
  strtok(buf, ",");
  if (buf[1] == 0) { x = 12; }
  return arr[x];
}

int guarded_args(const char *s, int fd) {   /* safe */
  int x = 0;
  int v = 5;
  long l = strtol(s, NULL, 10);
  time_t t = time(NULL);
  fcntl(fd, F_SETFL, O_NONBLOCK);
  ioctl(fd, FIONCLEX);
  if (v != 5) { x = 12; }
  return arr[x] + (int) l + (int) t;
}

int unchanged_by_strlen(const char *s) {   /* safe */
  char buf[4];
  int x = 0;
  buf[0] = 0;
  if (strlen(s) > 2) {
    if (buf[0] != 0) { x = 12; }
  }
  return arr[x];
}
