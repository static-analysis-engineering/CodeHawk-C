/* test attribute nonnull */

void f_no_attr(int *p);

void f_attr(int *p)  __attribute__ ((__nonnull__ (1)));

void *malloc(int len);


void test_no_attr() {
  int buffer[12];

  f_no_attr(buffer);

  int *p = malloc(12);

  f_no_attr(p);
}


/* Adds two proof obligation for not-null, one of which can be discharged
   against the data type, the other one is open, because malloc may return
   NULL. */
void test_attr() {
  int buffer[12];

  f_attr(buffer);

  int *p = malloc(12);

  f_attr(p);
}


int main(int argc, char **argv) {

  test_no_attr();
  test_attr();

  return 0;
}
