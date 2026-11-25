#ifndef TA_TRAFFIC_MODEL_H
#define TA_TRAFFIC_MODEL_H

#include <stdint.h>

#define TA_MODEL_QUEUE_MAX 120u
#define TA_MODEL_ARRIVALS_30_MAX 30u
#define TA_MODEL_FEATURE_COUNT 4u
#define TA_MODEL_NODE_COUNT 513u
#define TA_MODEL_MAX_DEPTH 10u
#define TA_MODEL_SHA256 "6c3ac987313535765d2fbdaf8deb1372b8ff22e137c9803e927801a246256262"

/* Inputs: current queues and PAST 30-second arrival counts (not rates).
 * Returns legal plan 0/1/2; out-of-domain inputs return balanced plan 0.
 * Domain checking lets the caller report this fallback explicitly.
 * No heap, floating point, operating system, network or runtime model load. */
int ta_model_in_domain(uint32_t queue_ns, uint32_t queue_ew,
                       uint32_t arrivals_ns_30, uint32_t arrivals_ew_30);
uint32_t ta_model_predict(uint32_t queue_ns, uint32_t queue_ew,
                          uint32_t arrivals_ns_30, uint32_t arrivals_ew_30);
uint32_t ta_model_storage_bytes(void);

#endif
