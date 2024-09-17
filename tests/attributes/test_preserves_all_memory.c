/* test chkc_preserves_all_memory attribute

   can be used to discharge proof obligations that memory has not been freed
*/

int f_no_attr(void *p);

int f_attr(void *p) __attribute__ ((__chkc_preserves_all_memory__));

void *malloc(int len);


void test_no_attr() {

  void *p = malloc(10);

  f_no_attr(p);
  f_no_attr(p);

  return 0;
}


/* the valid-mem proof obligation is discharged based on the guarantee that
   the first call to f_attr does not free p. */
void test_attr() {

  void *p = malloc(10);

  f_attr(p);
  f_attr(p);

  return 0;
}
