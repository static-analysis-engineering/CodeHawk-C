/* Attributes on application functions (functions defined in the analyzed
   file) are contract conditions (codehawk branch attributeassumptions,
   cCHFileContract.get_application_function_attributes).

   A postcondition from an attribute is a conjecture: it is checked by a
   return-site supporting proof obligation in the function itself, and
   assumed (post-condition assumption) by the primary proof obligations of
   its callers. Previously only attributes on functions that were declared
   but not defined in the file were read.

   The attribute must follow the declarator: a function attribute before the
   declaration specifiers is attached by CIL to the base type of the return
   type, not to the function (analyzer issue #59), and has no effect. */

#include <stddef.h>

struct state {
  int enable;
  int count;
};

static struct state table[4];

/* provable: the address of a global array element is not null */
static struct state *get_state(unsigned int i) __attribute__((returns_nonnull));

static struct state *get_state(unsigned int i) {
  return &table[i & 3];
}

/* not established: returns the result of an external function without a
   summary for a negative key (the return-site proof obligation stays open;
   callers still assume the postcondition, so their proofs depend on an open
   conjecture). A literal `return NULL;` is not used here: it is currently
   proven not-null as an "absolute address" (analyzer issue #60, unsound). */
extern struct state *ext_lookup(int key);

static struct state *find_state(int key) __attribute__((returns_nonnull));

static struct state *find_state(int key) {
  if (key < 0) {
    return ext_lookup(key);
  }
  return &table[key & 3];
}

/* leading attribute (issue #59): attached to struct state, not to the
   function; no postcondition */
__attribute__((returns_nonnull)) static struct state *lead_state(unsigned int i) {
  return &table[i & 3];
}

/* callers: the not-null proof obligations on the returned pointers are
   proven by the post-condition assumption for get_state and find_state,
   and stay open for lead_state */
int use_get_state(unsigned int i) {
  struct state *s = get_state(i);
  return s->count;
}

int use_find_state(int key) {
  struct state *s = find_state(key);
  return s->count;
}

int use_lead_state(unsigned int i) {
  struct state *s = lead_state(i);
  return s->count;
}
