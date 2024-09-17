/* test of the chkc_not_null attribute on the value of a global variable */

extern int *g_no_attr;

extern int *g_attr __attribute__ ((__chkc_not_null__));

void f(int *p) __attribute__ ((__nonnull__ (1)));


void test_no_attr() {

  f(g_no_attr);
}


void test_attr() {

  f(g_attr);
}


int main(int argc, char **argv) {

  test_no_attr();
  test_attr();

  return 0;
}
