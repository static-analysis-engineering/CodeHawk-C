## id151Q

#### Discussion: Library function postconditions and macros

This program calls two library functions: assert and malloc. Proving the memory
safety of this program requires knowledge of the semantics of both of these
libary functions, in this case in particular the postconditions of these functions.
To obtain this information the analysis makes use of library function summaries
(provided in advance/summaries/cchsummaries.jar).

The malloc summary includes a postcondition that states that the return value
points to a newly allocated region of memory with size (in bytes) given by the
first argument, or the return value is NULL. Proof obligation 34 uses this information
to determine that the buffer access on line 60 violates its bounds. Similarly in
program id154.c (the safe version) the same information is used to prove the
buffer access safe.

The assert call is actually a macro that expands into a conditional expression that
calls a function __assert_fail. In particular, the call
```
assert (buf != NULL);
```
expands into
```
((buf != ((void *)0)) ? (void) (0) : __assert_fail ("buf != NULL", "id151.c", 57, __PRETTY_FUNCTION__))
```
which, by CIL, gets represented as
```
if ((caste(unsigned long,buf) != caste(unsigned long,caste((void *),0))))
  { }
else
  { __assert_fail("buf != NULL","id151.c",57, "main"); }
```
which explains the many proof obligations that get generated for this seemingly
simple instruction.

The __assert_fail function has postcondition _false_, that is, it does not return.
This means only the then branch, with condition buf != NULL, continues, based on
which proof obligation 31 (not-null(buf)) can be proven safe.



Results for id151.c:
```
Function main
--------------------------------------------------------------------------------
52  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv

  library calls:
   assert:__assert_fail -- 1
   stdlib:malloc -- 1
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
53  {
54    char * buf;
55
56    buf = (char *) malloc(10 * sizeof(char));
--------------------------------------------------------------------------------
<S>    1     56  int-underflow(10,sizeof(char),op:mult,ikind:iulong) (safe)
                  underflow is well defined for unsigned types
<S>    2     56  int-overflow(10,sizeof(char),op:mult,ikind:iulong) (safe)
                  overflow is well defined for unsigned types
<S>    3     56  pointer-cast(tmp,from:void,to:char) (safe)
                  cast to character type
<L>    4     56  initialized(tmp)     (safe)
                  assignedAt#56
--------------------------------------------------------------------------------
57    assert (buf != NULL);
--------------------------------------------------------------------------------
<S>    5     57  cast(buf,from:(char *),to:unsigned long) (safe)
                  casting a pointer to integer type unsigned long
<L>    6     57  initialized(buf)     (safe)
                  assignedAt#56
<S>    7     57  cast(caste((void *),0),from:(void *),to:unsigned long) (safe)
                  null-pointer cast
<S>    8     57  cast(0,from:int,to:(void *)) (safe)
                  null-pointer cast
<S>    9     57  not-null(str(main))  (safe)
                  string-literal
<S>   10     57  null-terminated(str(main)) (safe)
                  string literal
<S>   11     57  ptr-upper-bound(str(main),ntp(str(main)),op:pluspi,typ:char) (safe)
                  upperbound of constant string argument: main
<S>   12     57  initialized-range(str(main),len:ntp(str(main))) (safe)
                  constant string
<S>   13     57  not-null(str(id151.c)) (safe)
                  string-literal
<S>   14     57  null-terminated(str(id151.c)) (safe)
                  string literal
<S>   15     57  ptr-upper-bound(str(id151.c),ntp(str(id151.c)),op:pluspi,typ:char) (safe)
                  upperbound of constant string argument: id151.c
<S>   16     57  initialized-range(str(id151.c),len:ntp(str(id151.c))) (safe)
                  constant string
<S>   17     57  not-null(str(buf != NULL)) (safe)
                  string-literal
<S>   18     57  null-terminated(str(buf != NULL)) (safe)
                  string literal
<S>   19     57  ptr-upper-bound(str(buf != NULL),ntp(str(buf != NULL)),op:pluspi,typ:char) (safe)
                  upperbound of constant string argument: buf != NULL
<S>   20     57  initialized-range(str(buf != NULL),len:ntp(str(buf != NULL))) (safe)
                  constant string
<S>   21     57  valid-mem(str(buf != NULL)) (safe)
                  constant string is allocated by compiler
<S>   22     57  lower-bound(char,str(buf != NULL)) (safe)
                  constant string is allocated by compiler
<S>   23     57  upper-bound(char,str(buf != NULL)) (safe)
                  constant string is allocated by compiler
<S>   24     57  valid-mem(str(id151.c)) (safe)
                  constant string is allocated by compiler
<S>   25     57  lower-bound(char,str(id151.c)) (safe)
                  constant string is allocated by compiler
<S>   26     57  upper-bound(char,str(id151.c)) (safe)
                  constant string is allocated by compiler
<S>   27     57  valid-mem(str(main)) (safe)
                  constant string is allocated by compiler
<S>   28     57  lower-bound(char,str(main)) (safe)
                  constant string is allocated by compiler
<S>   29     57  upper-bound(char,str(main)) (safe)
                  constant string is allocated by compiler
--------------------------------------------------------------------------------
58
59    /*  BAD  */
60    buf[4105] = 'A';
--------------------------------------------------------------------------------
<L>   30     60  initialized(buf)     (safe)
                  assignedAt#56
<L>   31     60  not-null(buf)        (safe)
                  null has been explicitly excluded (either by assignment or by checking)
<L>   32     60  valid-mem(buf)       (safe)
                  all memory regions potentially pointed at are valid: NULL, addrof_heapregion_1
<S>   33     60  ptr-lower-bound(buf,4105,op:indexpi,typ:char) (safe)
                  add non-negative number:  value is 4105
<*>   34     60  ptr-upper-bound-deref(buf,4105,op:indexpi,typ:char) (violation)
                  increment is larger than or equal to the size of the memory region returned by malloc: violates (4105 < 10)
<S>   35     60  not-null((buf + 4105)) (safe)
                  arguments of pointer arithmetic are checked for null
<S>   36     60  valid-mem((buf + 4105)) (safe)
                  pointer arithmetic stays within memory region
<S>   37     60  lower-bound(char,(buf + 4105)) (safe)
                  result of pointer arithmetic is guaranteed to satisfy lowerbound by inductive hypothesis
<S>   38     60  upper-bound(char,(buf + 4105)) (safe)
                  result of pointer arithmetic is guaranteed to satisfy upperbound by inductive hypothesis
<S>   39     60  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```


Results for id154.c (safe version):
For brevity we omit the proof obligations for line 57, as they are the same as
above.

```
Function main
--------------------------------------------------------------------------------
52  int main(int argc, char *argv[])
--------------------------------------------------------------------------------
Api:
  parameters:
    int argc
    ((char *) *) argv

library calls:
   assert:__assert_fail -- 1
   stdlib:malloc -- 1
--------------------------------------------------------------------------------
Primary Proof Obligations:
--------------------------------------------------------------------------------
53  {
54    char * buf;
55
56    buf = (char *) malloc(10 * sizeof(char));
--------------------------------------------------------------------------------
<S>    1     56  int-underflow(10,sizeof(char),op:mult,ikind:iulong) (safe)
                  underflow is well defined for unsigned types
<S>    2     56  int-overflow(10,sizeof(char),op:mult,ikind:iulong) (safe)
                  overflow is well defined for unsigned types
<S>    3     56  pointer-cast(tmp,from:void,to:char) (safe)
                  cast to character type
<L>    4     56  initialized(tmp)     (safe)
                  assignedAt#56
--------------------------------------------------------------------------------
57    assert (buf != NULL);
--------------------------------------------------------------------------------
.......
--------------------------------------------------------------------------------
58
59    /*  OK  */
60    buf[9] = 'A';
--------------------------------------------------------------------------------
<L>   30     60  initialized(buf)     (safe)
                  assignedAt#56
<L>   31     60  not-null(buf)        (safe)
                  null has been explicitly excluded (either by assignment or by checking)
<L>   32     60  valid-mem(buf)       (safe)
                  all memory regions potentially pointed at are valid: NULL, addrof_heapregion_1
<S>   33     60  ptr-lower-bound(buf,9,op:indexpi,typ:char) (safe)
                  add non-negative number:  value is 9
<L>   34     60  ptr-upper-bound-deref(buf,9,op:indexpi,typ:char) (safe)
                  increment is less than the size of the memory region returned by malloc: satisfies (9 < 10)
<S>   35     60  not-null((buf + 9))  (safe)
                  arguments of pointer arithmetic are checked for null
<S>   36     60  valid-mem((buf + 9)) (safe)
                  pointer arithmetic stays within memory region
<S>   37     60  lower-bound(char,(buf + 9)) (safe)
                  result of pointer arithmetic is guaranteed to satisfy lowerbound by inductive hypothesis
<S>   38     60  upper-bound(char,(buf + 9)) (safe)
                  result of pointer arithmetic is guaranteed to satisfy upperbound by inductive hypothesis
<S>   39     60  cast(chr('A'),from:int,to:char) (safe)
                  casting constant value 65 to char
--------------------------------------------------------------------------------
```
