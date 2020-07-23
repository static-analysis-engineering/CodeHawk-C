# 122 "/usr/include/x86_64-linux-gnu/bits/types.h"
typedef long int __clock_t;
typedef long int __time_t;
typedef int __clockid_t;
typedef void * __timer_t;
typedef long int __syscall_slong_t;
typedef long int __suseconds_t;
typedef int __pid_t;

# 98 "/usr/include/x86_64-linux-gnu/sys/types.h"
typedef __pid_t pid_t;

# 216 "/usr/lib/gcc/x86_64-linux-gnu/5/include/stddef.h"
typedef long unsigned int size_t;

# 57 "/usr/include/time.h"
typedef __clock_t clock_t;
typedef __time_t time_t;
typedef __clockid_t clockid_t;
typedef __timer_t timer_t;

# 120 "/usr/include/time.h"
struct timespec
  {
    __time_t tv_sec;
    __syscall_slong_t tv_nsec;
  };

# 30 "/usr/include/x86_64-linux-gnu/bits/time.h"
struct timeval
  {
    __time_t tv_sec;
    __suseconds_t tv_usec;
  };

# 55 "/usr/include/x86_64-linux-gnu/sys/time.h"
struct timezone
  {
    int tz_minuteswest;
    int tz_dsttime;
  };
typedef struct timezone *__restrict __timezone_ptr_t;

# 71 "/usr/include/x86_64-linux-gnu/sys/time.h"
extern int gettimeofday (struct timeval *__restrict __tv,
    __timezone_ptr_t __tz) __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__nonnull__ (1)));

extern int settimeofday (const struct timeval *__tv,
    const struct timezone *__tz)
     __attribute__ ((__nothrow__ , __leaf__));

extern int adjtime (const struct timeval *__delta,
      struct timeval *__olddelta) __attribute__ ((__nothrow__ , __leaf__));

enum __itimer_which
  {
    ITIMER_REAL = 0,
    ITIMER_VIRTUAL = 1,
    ITIMER_PROF = 2
  };

struct itimerval
  {
    struct timeval it_interval;
    struct timeval it_value;
  };

typedef int __itimer_which_t;

extern int getitimer (__itimer_which_t __which,
        struct itimerval *__value) __attribute__ ((__nothrow__ , __leaf__));

extern int setitimer (__itimer_which_t __which,
        const struct itimerval *__restrict __new,
        struct itimerval *__restrict __old) __attribute__ ((__nothrow__ , __leaf__));

extern int utimes (const char *__file, const struct timeval __tvp[2])
     __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__nonnull__ (1)));

extern int lutimes (const char *__file, const struct timeval __tvp[2])
     __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__nonnull__ (1)));

extern int futimes (int __fd, const struct timeval __tvp[2]) __attribute__ ((__nothrow__ , __leaf__));


# 131 "/usr/include/time.h" 3 4
struct tm
{
  int tm_sec;
  int tm_min;
  int tm_hour;
  int tm_mday;
  int tm_mon;
  int tm_year;
  int tm_wday;
  int tm_yday;
  int tm_isdst;
  long int tm_gmtoff;
  const char *tm_zone;
};

struct itimerspec
  {
    struct timespec it_interval;
    struct timespec it_value;
  };

struct sigevent;

# 186 "/usr/include/time.h"
extern clock_t clock (void) __attribute__ ((__nothrow__ , __leaf__));

extern time_t time (time_t *__timer) __attribute__ ((__nothrow__ , __leaf__));

extern double difftime (time_t __time1, time_t __time0)
     __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__const__));

extern time_t mktime (struct tm *__tp) __attribute__ ((__nothrow__ , __leaf__));

extern size_t strftime (char *__restrict __s, size_t __maxsize,
   const char *__restrict __format,
   const struct tm *__restrict __tp) __attribute__ ((__nothrow__ , __leaf__));

# 236 "/usr/include/time.h"
extern struct tm *gmtime (const time_t *__timer) __attribute__ ((__nothrow__ , __leaf__));

extern struct tm *localtime (const time_t *__timer) __attribute__ ((__nothrow__ , __leaf__));

extern struct tm *gmtime_r (const time_t *__restrict __timer,
       struct tm *__restrict __tp) __attribute__ ((__nothrow__ , __leaf__));

extern struct tm *localtime_r (const time_t *__restrict __timer,
          struct tm *__restrict __tp) __attribute__ ((__nothrow__ , __leaf__));

extern char *asctime (const struct tm *__tp) __attribute__ ((__nothrow__ , __leaf__));

extern char *ctime (const time_t *__timer) __attribute__ ((__nothrow__ , __leaf__));

extern char *asctime_r (const struct tm *__restrict __tp,
   char *__restrict __buf) __attribute__ ((__nothrow__ , __leaf__));


extern char *ctime_r (const time_t *__restrict __timer,
        char *__restrict __buf) __attribute__ ((__nothrow__ , __leaf__));

extern char *__tzname[2];
extern int __daylight;
extern long int __timezone;
extern char *tzname[2];
extern void tzset (void) __attribute__ ((__nothrow__ , __leaf__));
extern int daylight;
extern long int timezone;
extern int stime (const time_t *__when) __attribute__ ((__nothrow__ , __leaf__));

extern time_t timegm (struct tm *__tp) __attribute__ ((__nothrow__ , __leaf__));

extern time_t timelocal (struct tm *__tp) __attribute__ ((__nothrow__ , __leaf__));

extern int dysize (int __year) __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__const__));

# 334 "/usr/include/time.h"
extern int nanosleep (const struct timespec *__requested_time,
        struct timespec *__remaining);

extern int clock_getres (clockid_t __clock_id, struct timespec *__res) __attribute__ ((__nothrow__ , __leaf__));

extern int clock_gettime (clockid_t __clock_id, struct timespec *__tp) __attribute__ ((__nothrow__ , __leaf__));

extern int clock_settime (clockid_t __clock_id, const struct timespec *__tp)
     __attribute__ ((__nothrow__ , __leaf__));

extern int clock_nanosleep (clockid_t __clock_id, int __flags,
       const struct timespec *__req,
       struct timespec *__rem);

extern int clock_getcpuclockid (pid_t __pid, clockid_t *__clock_id) __attribute__ ((__nothrow__ , __leaf__));

extern int timer_create (clockid_t __clock_id,
    struct sigevent *__restrict __evp,
    timer_t *__restrict __timerid) __attribute__ ((__nothrow__ , __leaf__));

extern int timer_delete (timer_t __timerid) __attribute__ ((__nothrow__ , __leaf__));

extern int timer_settime (timer_t __timerid, int __flags,
     const struct itimerspec *__restrict __value,
     struct itimerspec *__restrict __ovalue) __attribute__ ((__nothrow__ , __leaf__));

extern int timer_gettime (timer_t __timerid, struct itimerspec *__value)
     __attribute__ ((__nothrow__ , __leaf__));

extern int timer_getoverrun (timer_t __timerid) __attribute__ ((__nothrow__ , __leaf__));

extern int timespec_get (struct timespec *__ts, int __base)
     __attribute__ ((__nothrow__ , __leaf__)) __attribute__ ((__nonnull__ (1)));

#define NULL ((void *)0)
