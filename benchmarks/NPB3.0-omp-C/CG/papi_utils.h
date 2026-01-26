/* UnixBench/src/papi_utils.h */
#ifndef PAPI_UTILS_H
#define PAPI_UTILS_H

#include <stdio.h>
#include <stdlib.h>

#include "papi.h"

#define CVA6_INS 0x80000032
#define CVA6_CYC 0x8000003b

static int EventSet = PAPI_NULL;
static long long values[2];

void papi_init_and_start() {
  int retval = 0;
  if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT) exit(1);
  PAPI_create_eventset(&EventSet);

  PAPI_set_domain(PAPI_DOM_ALL);

  retval = PAPI_add_event(EventSet, CVA6_INS);
  if (retval != PAPI_OK) {
    fprintf(stderr, "Error adding event %s: %s\n", event_names[i],
            PAPI_strerror(retval));
    // Optional: Continue even if one fails, or exit
  }
  retval = PAPI_add_event(EventSet, CVA6_CYC);
  if (retval != PAPI_OK) {
    fprintf(stderr, "Error adding event %s: %s\n", event_names[i],
            PAPI_strerror(retval));
    // Optional: Continue even if one fails, or exit
  }
  /* retval = PAPI_add_event(EventSet, test); */
  PAPI_start(EventSet);
}

void papi_stop_and_print() {
  PAPI_stop(EventSet, values);
  printf("\n[PAPI] Instructions: %lld\n", values[0]);
  printf("[PAPI] Cycles:       %lld\n", values[1]);
  if (values[1] > 0)
    printf("[PAPI] IPC:          %.4f\n", (double)values[0] / values[1]);
}
#endif
