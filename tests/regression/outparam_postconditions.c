/* Out-parameter postconditions with an error discriminator (#73). */

typedef struct { unsigned int Value; } msgid_t;
typedef int status_t;

/* success (return >= 0): *id initialized; error (return < 0): nothing */
status_t get_id(const void *msg, msgid_t *id)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory,
                 chkc_error_returns_lt(0), chkc_initializes(2)));

/* unconditional: *v initialized */
void get_val(int *v)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory,
                 chkc_initializes(1)));

/* no out-parameter postcondition */
status_t get_plain(int *v)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory));

unsigned int use_checked(const void *msg) {
  msgid_t id;
  status_t s = get_id(msg, &id);
  if (s != 0) {
    return 0;
  }
  return id.Value;          /* safe: success outcome */
}

unsigned int use_checked_ge(const void *msg) {
  msgid_t id;
  if (get_id(msg, &id) >= 0) {
    return id.Value;        /* safe: success outcome */
  }
  return 0;
}

unsigned int use_unchecked(const void *msg) {
  msgid_t id;
  (void) get_id(msg, &id);
  return id.Value;          /* open: error outcome not excluded */
}

unsigned int use_error(const void *msg) {
  msgid_t id;
  status_t s = get_id(msg, &id);
  if (s < 0) {
    return id.Value;        /* open: error outcome */
  }
  return 0;
}

int use_val(void) {
  int v;
  get_val(&v);
  return v;                 /* safe: unconditional */
}

int use_plain(void) {
  int v;
  status_t s = get_plain(&v);
  if (s != 0) return 0;
  return v;                 /* open: no postcondition */
}

/* error iff return == -1 */
int get_eq(int *v)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory,
                 chkc_error_returns_eq(-1), chkc_initializes(1)));

typedef struct { msgid_t inner; int count; } nested_t;

int get_nested(nested_t *n)
  __attribute__((chkc_requires_none, chkc_preserves_all_memory,
                 chkc_error_returns_lt(0), chkc_initializes(1)));

/* the status is overwritten: the success outcome is not established */
unsigned int use_reassigned(const void *msg) {
  msgid_t id;
  status_t s = get_id(msg, &id);
  s = 0;
  if (s == 0) {
    return id.Value;        /* open */
  }
  return 0;
}

/* eq discriminator: success iff return != -1 */
int use_eq(void) {
  int v;
  if (get_eq(&v) != -1) {
    return v;               /* safe */
  }
  return 0;
}

int use_eq_zero(void) {
  int v;
  if (get_eq(&v) == 0) {
    return v;               /* safe: 0 != -1 */
  }
  return 0;
}

/* nested struct: all scalar leaves */
int use_nested(void) {
  nested_t n;
  if (get_nested(&n) < 0) return 0;
  return n.count + (int) n.inner.Value;   /* safe (both) */
}

/* join of a success path and a locally initialized path */
unsigned int use_join(const void *msg, int b) {
  msgid_t id;
  if (b) {
    if (get_id(msg, &id) < 0) return 0;
  } else {
    id.Value = 7;
  }
  return id.Value;          /* safe */
}

/* join of a success path and an error path */
unsigned int use_join_error(const void *msg, int b) {
  msgid_t id;
  status_t s;
  if (b) {
    s = get_id(msg, &id);
    if (s < 0) return 0;
  } else {
    s = get_id(msg, &id);
  }
  return id.Value;          /* open */
}

/* loop: the last call succeeded */
unsigned int use_loop(const void *msg, int n) {
  msgid_t id;
  status_t s = -1;
  int i;
  for (i = 0; i < n; i++) {
    s = get_id(msg, &id);
  }
  if (s >= 0) {
    return id.Value;        /* safe: s >= 0 implies a call was made and succeeded */
  }
  return 0;
}

/* out-argument not of the form &lval: not covered */
unsigned int use_ptr(const void *msg, msgid_t *p) {
  if (get_id(msg, p) < 0) return 0;
  return p->Value;          /* open (external memory) */
}

/* initialized before the call, status ignored (cFE *_VerifyCmdLength):
   the error outcome keeps the prior state */
unsigned int use_prior(const void *msg) {
  msgid_t id = { 0 };
  (void) get_id(msg, &id);
  return id.Value;          /* safe (locally: prior state) */
}

/* initialized before the call on one path only */
unsigned int use_prior_partial(const void *msg, int b) {
  msgid_t id;
  if (b) {
    id.Value = 1;
  }
  (void) get_id(msg, &id);
  return id.Value;          /* open */
}
