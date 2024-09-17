/* test chkc_preserves_memory attribute

   can be used to discharge proof obligations that memory has not been freed

   Note: does not yet work.
*/

int f_no_attr(void *p);

int f_attr(void *p) __attribute__ ((__chkc_preserves_memory__ (1)));

void *malloc(int len);


void test_no_attr() {

  void *p = malloc(10);

  f_no_attr(p);
  f_no_attr(p);

  return 0;
}


void test_attr() {

  void *p = malloc(10);

  f_attr(p);
  f_attr(p);

  return 0;
}
