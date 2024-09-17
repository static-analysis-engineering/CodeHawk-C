/* test_malloc attribute

   The malloc attribute allows discharge of the allocation-base proof
   obligation for free.

   Note: this test should show the discharge of the no-overlap requirement
   for memcpy. It does not do so yet.
*/

void *f_no_attr(int len);

void *f_attr(int len) __attribute__ ((__malloc__));

void *memcpy(void *dst, const void *src, int len);


void test_no_attr() {

  char *p = (char *) f_no_attr(10);
  char *q = (char *) f_no_attr(10);

  if (p && q) {
    memcpy(q, p, 10);
  }

  free(p);
  free(q);
}


void test_attr() {

  char *p = (char *) f_attr(10);
  char *q = (char *) f_attr(10);

  if (p && q) {
    memcpy(q, p, 10);
  }

  free(p);
  free(q);
}


int main(int argc, char **argv) {

  test_no_attr();
  test_attr();

  return 0;
}
