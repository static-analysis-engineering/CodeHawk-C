/* Issue 41: translation of functions with gotos.
   (1) The last statement of a goto function was translated outside the
       CFG: a backward goto in the last statement was lost and its target
       was unreachable.
   (2) break/continue in a nested goto block (least common ancestor of a
       goto and its label below the function body) whose loop or switch
       encloses the block fell through to the statement after the block. */

int arr[10];

/* (1) the target of the backward goto is reachable; arr[i] is out of
   bounds on every execution */
int goto_backward(void) {
  int x;
  int i = 12;
  goto init;
 use:
  x = arr[i];
  return x;
 init:
  x = 1;
  goto use;
}

/* (1) x is initialized before the read */
int goto_backward_init(int i) {
  int x;
  goto init;
 use:
  if (i >= 0 && i < 10) {
    return arr[i] + x;
  }
  return x;
 init:
  x = 1;
  goto use;
}

/* (2) break leaves the loop: n == 5 is possible after the loop */
int nested_break(int n, int x) {
  while (n > 0) {
    if (n == 5) {
      if (x) goto L;
      break;
     L:
      x = 0;
    }
    n--;
  }
  return arr[n + 9];
}

/* (2) continue skips k = 0: k == 20 is possible after the loop */
int nested_continue(int n, int x) {
  int k = 0;
  while (n > 0) {
    n--;
    if (n == 5) {
      if (x) goto M;
      k = 20;
      continue;
     M:
      x = 0;
    }
    k = 0;
  }
  return arr[k];
}

/* (2) break leaves the switch: k == 20 is possible */
int nested_switch_break(int c, int x) {
  int k = 0;
  switch (c) {
  case 1:
    if (c == 1) {
      if (x) goto S;
      k = 20;
      break;
     S:
      k = 1;
    }
    k = 2;
    break;
  default:
    k = 3;
  }
  return arr[k];
}

/* break inside a loop within the goto block (stays within the block) */
int inner_loop_break(int n) {
  int k = 0;
  if (n > 0) {
    goto start;
   again:
    k = 1;
   start:
    while (1) {
      if (k > 0) break;
      goto again;
    }
  }
  return arr[k];
}
