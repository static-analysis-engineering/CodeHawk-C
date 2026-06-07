/* Tests for cchanalyze/cCHPOCheckInitialized.ml */


int gl_inv_001(void) {

  int i = 5;

  return i;
}


typedef struct mystruct_s {
  int fld1;
  int fld2;
} mystruct;


int gl_inv_002(void) {

  mystruct s = {.fld1 = 5, .fld2 = 3 };

  return s.fld1;
}


int gl_inv_003(int k) {

  int i;

  if (k > 0) {
    i = 5;
  } else {
    i = 3;
  }

  return i;
}


int gl_inv_bounded_xpr_001(int k) {

  int i;
  int *p = &i;

  if (k > 5) {
    i = 5;
  } else {
    i = 3;
  }

  return *p;
}


int gl_inv_xpr_001(void) {

  int i = 5;

  int *p = &i;

  return *p;
}


int gl_inv_xpr_002(void) {

  int i = 5;

  int *p = &i;

  i = 8;

  return *p;
}


int gl_inv_xpr_003(void) {

  int i;

  int *p = &i;

  *p = 8;

  return i;
}


int gl_stackvar_001(int k) {

  int i;
  int *p = &i;

  if (k > 5) {
    i = 5;
  } else {
    i = k;
  }

  return *p;
}
