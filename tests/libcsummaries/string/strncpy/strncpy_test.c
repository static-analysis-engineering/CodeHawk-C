#include <string.h>

char s[] = "this is a string";

int main(int argc, char **argv) {
  
  char dst1[10];

  strncpy(dst1, s, 10);
  strncpy(dst1, s, 20);

  return 0;
}
