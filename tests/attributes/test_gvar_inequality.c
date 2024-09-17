/* tests the inequality attributes for global variables:
   - chkc_le
   - chkc_lt
   - chkc_ge
   - chkc_gt

   These attributes can be used to enforce a global bounds on the value
   of a global variable; they will generate proof obligations and can be
   used in the discharge of other proof obligations.
*/

#define BUFSIZE 12

int g_no_attr;

int g_attr
__attribute__ ((__chkc_lt__ (BUFSIZE))) __attribute__ ((__chkc_ge__ (0)));

int buffer[BUFSIZE];


void test_no_attr() {

  buffer[g_no_attr] = 0;
}


/* attributes are used to discharge the index-lower and index-upper-bound
   proof obligations. */
void test_attr() {

  buffer[g_attr] = 0;
}


int main(int argc, char **argv) {

  g_no_attr = 10;
  g_attr = 10;

  test_no_attr();
  test_attr();

  return 0;
}
