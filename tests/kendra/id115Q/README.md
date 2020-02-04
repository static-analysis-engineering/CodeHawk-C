#### id115Q

Results for id115.c (violation):
```
Function main
--------------------------------------------------------------------------------
50  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
51  {
52    char buf[10];
53
54
55    /*  BAD  */
56    buf[4105] = 'A';
--------------------------------------------------------------------------------
<S>    1     56  index-lower-bound(4105) (safe)
                  index value 4105 is non-negative
<*>    2     56  index-upper-bound(4105,bound:10) (violation)
                  index value 4105 violates upper bound 10
<S>    3     56  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```

Results for id118.c (safe):
```
Function main
--------------------------------------------------------------------------------
50  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
51  {
52    char buf[10];
53
54
55    /*  OK  */
56    buf[9] = 'A';
--------------------------------------------------------------------------------
<S>    1     56  index-lower-bound(9) (safe)
                  index value 9 is non-negative
<S>    2     56  index-upper-bound(9,bound:10) (safe)
                  index value 9 is less than bound 10
<S>    3     56  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```
