/*
 * Reproducer for a CodeHawk-C integer-promotion failure seen in perlbench
 * ext/re/re_exec.c:S_isGCB.
 *
 * Perl combines two enum values with:
 *
 *     (GCB_ENUM_COUNT * before) + after
 *
 * The proof checker reconstructs this as arithmetic over int and enum types.
 * C's usual arithmetic conversions allow enum operands to participate in
 * integer arithmetic, but CH-C's get_integer_promotion only accepted TInt
 * operands and failed on int and enum.
 *
 * Ref Issue #71: https://github.com/static-analysis-engineering/CodeHawk-C/issues/71
 */

typedef enum {
    GCB_OTHER = 0,
    GCB_CR = 1,
    GCB_LF = 2,
    GCB_ENUM_COUNT = 14
} GCB_enum;

int enum_integer_promotion(GCB_enum before, GCB_enum after) {
    switch ((GCB_ENUM_COUNT * before) + after) {
    case (GCB_ENUM_COUNT * GCB_CR) + GCB_LF:
        return 1;
    default:
        return 0;
    }
}
