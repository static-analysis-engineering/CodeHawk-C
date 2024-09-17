/* test returns-nonnull attribute */

char *f_no_attr();

char *f_attr() __attribute__ ((__returns_nonnull__));

int atoi(char *p);

int test_no_attr() {

  char *p = f_no_attr();

  return atoi(p);
}


/* returns-nonnull property is used to discharge the not-null proof obligation
   for atoi.*/
int test_attr() {

  char *p = f_attr();

  return atoi(p);
}


int main(int argc, char **argv) {

  test_no_attr();
  test_attr();

  return 0;
}
