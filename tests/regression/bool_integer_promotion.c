/* Ref Issue #69: https://github.com/static-analysis-engineering/CodeHawk-C/issues/69 */

typedef unsigned long UV;

void grow(UV len, UV offset, _Bool add_one) {
    UV bytes = (len + offset + add_one) * sizeof(UV);
    (void)bytes;
}
