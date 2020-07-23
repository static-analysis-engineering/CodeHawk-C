#include "../time_h.h"

int main(int argc, char **argv) {

  time_t b;
  struct tm *t;
  int sec;
  int min;
  int hour;
  int mday;
  int mon;
  int year;
  int wday;
  int yday;

  b = time(NULL);
  t = localtime(&b);
  if (t==NULL) return NULL;  

  sec = t->tm_sec+1;
  sec = t->tm_sec-1;

  min = t->tm_min+1;
  min = t->tm_min-1;

  hour = t->tm_hour+1;
  hour = t->tm_hour-1;

  mday = t->tm_mday+1;
  mday = t->tm_mday-1;

  mon = t->tm_mon+1;
  mon = t->tm_mon-1;

  year = t->tm_year; /* no bounds specified */

  wday = t->tm_wday+1;
  wday = t->tm_wday-1;

  yday = t->tm_yday+1;
  yday = t->tm_yday-1;

  return 0;
}
  

