/* Regression test for issue 40: uint-underflow for unsigned subtraction.

   e1 - e2 in an unsigned type wraps around iff e2 > e1 (C11 6.2.5p9), so the
   PO uint-underflow(e1, e2, minusa) can be discharged only from a relation
   between the two operands, for example LB(e1) >= UB(e2), or from e2 == 0.
   Previously a non-negative lower bound on e1 alone was accepted, so the
   subtraction in lb_first_only was proven safe (now open). The operands are
   return values of an external function, so the PO cannot be delegated to
   the function's API. lb_first_ub_too_large is open (b may exceed a); the
   remaining functions are safe.
 */

unsigned int ext_value(void);

unsigned int lb_first_only(void) {   /* open */
  unsigned int a = ext_value();
  unsigned int b = ext_value();
  if (a >= 5) {
    return a - b;
  }
  return 0;
}

unsigned int lb_first_ub_too_large(void) {   /* open */
  unsigned int a = ext_value();
  unsigned int b = ext_value();
  if (a >= 5 && b <= 6) {
    return a - b;
  }
  return 0;
}

unsigned int bounded_both(void) {   /* safe */
  unsigned int a = ext_value();
  unsigned int b = ext_value();
  if (a >= 5 && b <= 5) {
    return a - b;
  }
  return 0;
}

unsigned int second_zero(void) {   /* safe */
  unsigned int a = ext_value();
  unsigned int b = ext_value();
  if (b == 0) {
    return a - b;
  }
  return 0;
}

unsigned int constant_second(void) {   /* safe */
  unsigned int a = ext_value();
  if (a >= 3) {
    return a - 3;
  }
  return 0;
}
