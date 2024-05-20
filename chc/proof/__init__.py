"""Proof obligations and their proofs.

There are two types of proof obligations:

- primary proof obligations (ppo's)
- supporting proof obligations (spo's)

All proof obligations are expressed as assertions over program variables
using a set of custom predicates.

**Primary proof obligations** are generated on the source for all constructs
that can possibly result in undefined behavior. An example is:

``*p = 0;``

would generate the primary proof obligation

``not-null(p)``

Primary proof obligations are generated up front and the set of primary proof
obligations remains fixed after that.

**Supporting proof obligations** are generated in support of assumptions
generated (or added by the user) to discharge primary proof obligations (or
other supporting proof obligations). Consider for example:

``f(int *p){ *p = 0; }``

The only way (without changing the code) to discharge the ``not-null(p)``
proof obligation is to assume that the parameter ``p`` is not null. Thus
this assumption is (automatically) generated on api of the function f.
This, in turn, results in supporting proof obligations being generated
for each call site, e.g., the call

``f(q);``

will cause the supporting proof obligation:

``not-null(q)``

to be (automatically) generated.

The set of supporting proof obligations grows over the course of the analysis
as new assumptions are introduced, new supporting proof obligations to justify
these assumptions may have to be generated, which in turn need to be discharged
themselves, providing thus a bottom-up context-sensitivity.
"""
