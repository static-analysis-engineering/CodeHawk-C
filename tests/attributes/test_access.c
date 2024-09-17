/* test access attribute */

void f_no_attr(int *p, int len);

/* the access attribute specifies that the first argument must be able to
   be read, with a minimum size specified by the second argument. */
void f_attr(int *p, int len)  __attribute__((__access__ (read_only, 1, 2)));


void test_no_attr() {
  int buffer[12];

  f_no_attr(buffer, 12);
  f_no_attr(buffer, 20);
}


/* should show violation for the second call */
void test_attr() {
  int buffer[12];

  f_attr(buffer, 12);
  f_attr(buffer, 20);
}


int main(int argc, char **argv) {

  test_no_attr();
  test_attr();

  return 0;
}
