/* Contracts from companion specification files (header companions).

   The sources carry no attributes. The parse step appends to
   companion_postconditions.i, after a marker line, the preprocessed
   companions found under cch_contracts (mirroring the source tree):
     - companion_postconditions.chk.h, the companion of the included
       project header companion_postconditions.h (contract of the static
       inline accessor hdr_state);
     - companion_postconditions.c.chk.h, the companion of this file
       (contracts of get_state and find_state).
   The companions contain attributed redeclarations of these functions;
   the attributes become contract conditions (as in
   attribute_postconditions.c): the postconditions are checked by
   return-site supporting proof obligations, and assumed by the callers.

   other_state has no companion entry: no postcondition. */

#include "companion_postconditions.h"

struct state table[4];

extern struct state *ext_lookup(int key);

/* provable */
static struct state *get_state(unsigned int i) {
  return &table[i & 3];
}

/* not established for a negative key: return-site proof obligation open */
static struct state *find_state(int key) {
  if (key < 0) {
    return ext_lookup(key);
  }
  return &table[key & 3];
}

/* no contract */
static struct state *other_state(unsigned int i) {
  return &table[i & 3];
}

int use_hdr_state(unsigned int i) {
  struct state *s = hdr_state(i);
  return s->count;
}

int use_get_state(unsigned int i) {
  struct state *s = get_state(i);
  return s->count;
}

int use_find_state(int key) {
  struct state *s = find_state(key);
  return s->count;
}

int use_other_state(unsigned int i) {
  struct state *s = other_state(i);
  return s->count;
}
