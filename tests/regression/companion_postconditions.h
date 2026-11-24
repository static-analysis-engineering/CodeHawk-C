/* Header for companion_postconditions.c; the static inline accessor
   hdr_state gets its contract from the header companion
   cch_contracts/companion_postconditions.chk.h */

#ifndef COMPANION_POSTCONDITIONS_H
#define COMPANION_POSTCONDITIONS_H

struct state {
  int enable;
  int count;
};

extern struct state table[4];

static inline struct state *hdr_state(unsigned int i) {
  return &table[i & 3];
}

#endif
