/*
 * Small reproducer for the CodeHawk-C my_regexec failure seen in SPEC
 * CPU2017 perlbench.
 *
 * The important shape is:
 *
 *     unsigned_len_arg(..., end - begin)
 *
 * where begin and end are both char pointers. In C, end - begin is pointer
 * subtraction with signed ptrdiff_t result. Passing it to an unsigned length
 * parameter creates the same kind of signed-to-unsigned-cast proof obligation
 * as perlbench's:
 *
 *     MgBYTEPOS(mg, sv, strbeg, strend - strbeg)
 *
 * CH-C generated a valid obligation for that cast, but then crashed while
 * reconstructing an API expression for the upper-bound invariant because it
 * treated the pointer difference as ordinary arithmetic XMinus and attempted
 * integer promotion on (char *) and (char *).
 *
 * Ref: https://github.com/static-analysis-engineering/CodeHawk-C/issues/75
 */

#include <stddef.h>

typedef unsigned long STRLEN;

static STRLEN consume_len(const char *base, STRLEN len) {
    return base[len] == '\0' ? len : len + 1;
}

STRLEN my_regexec_repro(const char *strbeg, const char *strend) {
    return consume_len(strbeg, strend - strbeg);
}

STRLEN my_regexec_repro_with_guard(const char *strbeg, const char *strend) {
    if (strend < strbeg) {
        return 0;
    }

    return consume_len(strbeg, strend - strbeg);
}

STRLEN my_regexec_source_workaround(const char *strbeg, const char *strend) {
    if (strend < strbeg) {
        return 0;
    }

    {
        STRLEN len = (STRLEN)(strend - strbeg);
        return consume_len(strbeg, len);
    }
}
