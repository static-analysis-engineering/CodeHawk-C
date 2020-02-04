## id263Q

#### Discussion: postconditions
The safety of the array access in these programs depends on the value returned
by function1. In this case the transfer function of function1 is very simple
and can be expressed exactly by the postcondition, which is generated automatically
and advertised in the api of function1. Using this postcondition the main
function obtains the return value by simply substituting the argument value,
and can thus discharge the proof obligation, resulting in a violation for
id263.c and a safe access for id266.c, as shown below.

Results of id263.c:
```
Function function1
--------------------------------------------------------------------------------
50  int function1(int arg1)
--------------------------------------------------------------------------------
Api:
  parameters:
    int arg1

  postcondition guarantees:
   post-expr(eq,return-val,arg-val(par-1))
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
51  {
52    return arg1;
--------------------------------------------------------------------------------
<S>    1     52  initialized(arg1)    (safe)
                  arg1 is a function parameter
--------------------------------------------------------------------------------

Function main
--------------------------------------------------------------------------------
55  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
56  {
57    char buf[10];
58
59
60    /*  BAD  */
61    buf[function1(4105)] = 'A';
--------------------------------------------------------------------------------
<L>    1     61  index-lower-bound(tmp) (safe)
                  index value is non-negative: 4105
<*>    2     61  index-upper-bound(tmp,bound:10) (violation)
                  index value, 4105, is greater than or equal to length, 10
<L>    3     61  initialized(tmp)     (safe)
                  assignedAt#61
<S>    4     61  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```

Results for id266.c:

```
Function function1
--------------------------------------------------------------------------------
50  int function1(int arg1)
--------------------------------------------------------------------------------
Api:
  parameters:
    int arg1

  postcondition guarantees:
   post-expr(eq,return-val,arg-val(par-1))
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
51  {
52    return arg1;
--------------------------------------------------------------------------------
<S>    1     52  initialized(arg1)    (safe)
                  arg1 is a function parameter
--------------------------------------------------------------------------------

Function main
--------------------------------------------------------------------------------
55  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
56  {
57    char buf[10];
58
59
60    /*  OK  */
61    buf[function1(9)] = 'A';
--------------------------------------------------------------------------------
<L>    1     61  index-lower-bound(tmp) (safe)
                  index value is non-negative: 9
<L>    2     61  index-upper-bound(tmp,bound:10) (safe)
                  index value, 9, is less than length, 10
<L>    3     61  initialized(tmp)     (safe)
                  assignedAt#61
<S>    4     61  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```
