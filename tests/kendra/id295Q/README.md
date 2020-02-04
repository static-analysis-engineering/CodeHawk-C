## id295Q

### Discussion: open proof obligations
The results shown below indicate an open proof obligation (17) for ptr-upper-bound
for id295.c; the same proof obligation for id298.c (the safe version) is proven safe.
The reason for the open proof obligation is that we do not (at present) prove the
absence of other null-terminating character in the string, and thus the string may
be shorter than indicated by the null-terminator position at the end of the array.
Note that sufficient information is available: we can derive this information from
the memset semantics. Proving absence of change of these values, however, requires
more expensive dataflow analysis that is currently not performed.

Open proof obligations in the report are accompanied by some of the invariants
generated for that location, which may assist in identifying the information that
is missing to enable discharge of the proof obligation.

Results for id295.c:

```
Function main
--------------------------------------------------------------------------------
51  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv

library calls:
   string:memset -- 1
   string:strcpy -- 1
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
52  {
53    char src[4106];
54    char buf[10];
55
56    memset(src, 'A', 4106);
--------------------------------------------------------------------------------
<L>    1     56  not-null(caste((void *),&(src))) (safe)
                  address of stack variable src is not null
<S>    2     56  ptr-upper-bound(caste((void *),&(src)),caste(size_t,4106),op:pluspi,typ:void) (safe)
                  adding 4106 to the start of an array of length 4106
<S>    3     56  pointer-cast(&(src),from:char,to:void) (safe)
                  cast to void pointer
<S>    4     56  valid-mem(caste((void *),&(src))) (safe)
                  address of a variable is a valid memory region
<S>    5     56  lower-bound(void,caste((void *),&(src))) (safe)
                  address of a variable
<S>    6     56  upper-bound(void,caste((void *),&(src))) (safe)
                  address of a variable
<S>    7     56  signed-to-unsigned-cast(4106,from:iint,to:iulong) (safe)
                  constant value 4106 fits in type unsigned long
--------------------------------------------------------------------------------
57    src[4106 - 1] = '\0';
--------------------------------------------------------------------------------
<S>    8     57  index-lower-bound(4105) (safe)
                  index value 4105 is non-negative
<S>    9     57  index-upper-bound(4105,bound:4106) (safe)
                  index value 4105 is less than bound 4106
<S>   10     57  cast(chr(''),from:int,to:char) (safe)
                  casting constant value 0 to char
--------------------------------------------------------------------------------
58
59    /*  BAD  */
60    strcpy(buf, src);
--------------------------------------------------------------------------------
<L>   11     60  not-null(caste((char *),&(src))) (safe)
                  address of stack variable src is not null
<L>   12     60  null-terminated(caste((char *),&(src))) (safe)
                  null value was set in array src at offset 4105
<L>   13     60  ptr-upper-bound(caste((char *),&(src)),ntp(caste((char *),&(src))),op:pluspi,typ:char) (safe)
                  null-terminator in array src is present at position 4105 which is less than the size of src: 4106
<L>   14     60  initialized-range(caste((char *),&(src)),len:ntp(caste((char *),&(src)))) (safe)
                  initialized by memset with 4106 bytes
<S>   15     60  no-overlap(caste((char *),&(buf)),caste((char *),&(src))) (safe)
                  addresses of two distinct arrays: buf and src
<L>   16     60  not-null(caste((char *),&(buf))) (safe)
                  address of stack variable buf is not null

<?>   17     60  ptr-upper-bound(caste((char *),&(buf)),ntp(caste((char *),&(src))),op:pluspi,typ:char) (open)
                  --
                  argv: sx:(argv_4_)#init:nv[aux-argv:nv[lv:argv:((char *) *)  id295.c:51]_init]
                  argc: sx:(argc_2_)#init:nv[aux-argc:nv[lv:argc:int  id295.c:51]_init]
                  src[4105]: iv:0
                  check_(ppo:17:3): sx:(2)address:nv[aux-memory-address:&buf:nv[lv:buf:char[10]  id295.c:54]]
                  src:sv[lv:src:char[4106]  id295.c:53] : syms:initialized-range_memset_4106
                  src[4105]:sv[lv:src:char[4106]  id295.c:53[4105]] : syms:assignedAt#57
<S>   18     60  pointer-cast(&(buf),from:char,to:char) (safe)
                  source and target type are the same
<S>   19     60  valid-mem(caste((char *),&(buf))) (safe)
                  address of a variable is a valid memory region
<S>   20     60  lower-bound(char,caste((char *),&(buf))) (safe)
                  address of a variable
<S>   21     60  upper-bound(char,caste((char *),&(buf))) (safe)
                  address of a variable
<S>   22     60  pointer-cast(&(src),from:char,to:char) (safe)
                  source and target type are the same
<S>   23     60  valid-mem(caste((char *),&(src))) (safe)
                  address of a variable is a valid memory region
<S>   24     60  lower-bound(char,caste((char *),&(src))) (safe)
                  address of a variable
<S>   25     60  upper-bound(char,caste((char *),&(src))) (safe)
                  address of a variable
--------------------------------------------------------------------------------
```

Results for id298.c:
```
Function main
--------------------------------------------------------------------------------
51  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv

  library calls:
   string:memset -- 1
   string:strcpy -- 1
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
52  {
53    char src[10];
54    char buf[10];
55
56    memset(src, 'A', 10);
--------------------------------------------------------------------------------
<L>    1     56  not-null(caste((void *),&(src))) (safe)
                  address of stack variable src is not null
<S>    2     56  ptr-upper-bound(caste((void *),&(src)),caste(size_t,10),op:pluspi,typ:void) (safe)
                  adding 10 to the start of an array of length 10
<S>    3     56  pointer-cast(&(src),from:char,to:void) (safe)
                  cast to void pointer
<S>    4     56  valid-mem(caste((void *),&(src))) (safe)
                  address of a variable is a valid memory region
<S>    5     56  lower-bound(void,caste((void *),&(src))) (safe)
                  address of a variable
<S>    6     56  upper-bound(void,caste((void *),&(src))) (safe)
                  address of a variable
<S>    7     56  signed-to-unsigned-cast(10,from:iint,to:iulong) (safe)
                  constant value 10 fits in type unsigned long
--------------------------------------------------------------------------------
57    src[10 - 1] = '\0';
--------------------------------------------------------------------------------
<S>    8     57  index-lower-bound(9) (safe)
                  index value 9 is non-negative
<S>    9     57  index-upper-bound(9,bound:10) (safe)
                  index value 9 is less than bound 10
<S>   10     57  cast(chr(''),from:int,to:char) (safe)
                  casting constant value 0 to char
--------------------------------------------------------------------------------
58
59    /*  OK  */
60    strcpy(buf, src);
--------------------------------------------------------------------------------
<L>   11     60  not-null(caste((char *),&(src))) (safe)
                  address of stack variable src is not null
<L>   12     60  null-terminated(caste((char *),&(src))) (safe)
                  null value was set in array src at offset 9
<L>   13     60  ptr-upper-bound(caste((char *),&(src)),ntp(caste((char *),&(src))),op:pluspi,typ:char) (safe)
                  null-terminator in array src is present at position 9 which is less than the size of src: 10
<L>   14     60  initialized-range(caste((char *),&(src)),len:ntp(caste((char *),&(src)))) (safe)
                  initialized by memset with 10 bytes
<S>   15     60  no-overlap(caste((char *),&(buf)),caste((char *),&(src))) (safe)
                  addresses of two distinct arrays: buf and src
<L>   16     60  not-null(caste((char *),&(buf))) (safe)
                  address of stack variable buf is not null
<L>   17     60  ptr-upper-bound(caste((char *),&(buf)),ntp(caste((char *),&(src))),op:pluspi,typ:char) (safe)
                  null-terminator in array src is present at position 9 which is less than the size of buf: 10
<S>   18     60  pointer-cast(&(buf),from:char,to:char) (safe)
                  source and target type are the same
<S>   19     60  valid-mem(caste((char *),&(buf))) (safe)
                  address of a variable is a valid memory region
<S>   20     60  lower-bound(char,caste((char *),&(buf))) (safe)
                  address of a variable
<S>   21     60  upper-bound(char,caste((char *),&(buf))) (safe)
                  address of a variable
<S>   22     60  pointer-cast(&(src),from:char,to:char) (safe)
                  source and target type are the same
<S>   23     60  valid-mem(caste((char *),&(src))) (safe)
                  address of a variable is a valid memory region
<S>   24     60  lower-bound(char,caste((char *),&(src))) (safe)
                  address of a variable
<S>   25     60  upper-bound(char,caste((char *),&(src))) (safe)
                  address of a variable
--------------------------------------------------------------------------------
```
