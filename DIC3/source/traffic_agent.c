#include "traffic_agent.h"
#include "traffic_model.h"

uint32_t ta_phase_seconds(uint32_t plan, uint32_t phase) {
    static const uint8_t lengths[3][6] = {
        {12,2,1,12,2,1}, {16,2,1,8,2,1}, {8,2,1,16,2,1}
    };
    return plan<3u && phase<6u ? lengths[plan][phase] : 0u;
}

int ta_snapshot_tick(const ta_snapshot_t *s, uint64_t *tick) {
    uint32_t i;
    uint64_t value;
    if ((s->status & (TA_STATUS_READY|TA_STATUS_FAULT|TA_STATUS_STARTUP))
            != TA_STATUS_READY || s->phase>=6u || s->active_plan>=3u
            || s->remaining==0u
            || s->remaining>ta_phase_seconds(s->active_plan,s->phase)) return 0;
    value=(uint64_t)s->cycle_count*30u;
    for(i=0;i<s->phase;i++) value+=ta_phase_seconds(s->active_plan,i);
    *tick=value+ta_phase_seconds(s->active_plan,s->phase)-s->remaining;
    return 1;
}

uint32_t ta_rule_plan(uint32_t qns,uint32_t qew,uint32_t ans,uint32_t aew,
                      uint64_t costs[3]) {
    uint32_t plan,phase,second,best=0;
    /* Exact rational fluid lookahead. Queue and accumulated area are scaled
     * by30; arrival inputs are measured COUNTS in the past30 seconds. */
    for(plan=0;plan<3;plan++) {
        uint64_t ns=(uint64_t)qns*30u,ew=(uint64_t)qew*30u,area=0;
        for(phase=0;phase<6;phase++) {
            for(second=0;second<ta_phase_seconds(plan,phase);second++) {
                ns+=ans; ew+=aew;
                if(phase==0) ns=ns>30u?ns-30u:0u;
                if(phase==3) ew=ew>30u?ew-30u:0u;
                area+=ns+ew;
            }
        }
        costs[plan]=area;
        if(plan && area<costs[best]) best=plan;
    }
    return best;
}

void ta_engine_init(ta_engine_t *s,uint32_t scenario,uint32_t seed,uint32_t policy) {
    uint32_t i;
    unsigned char *bytes=(unsigned char *)s;
    for(i=0;i<(uint32_t)sizeof(*s);i++) bytes[i]=0;
    s->policy=policy;
    if(policy>TA_POLICY_MODEL) s->error_flags=TA_ERROR_TELEMETRY;
    ta_synthetic_init(&s->source,scenario,seed);
}

static int coherent_transition(const ta_snapshot_t *a,const ta_snapshot_t *b) {
    if(a->phase==5u && a->remaining==1u)
        return a->cycle_count!=UINT32_MAX && b->cycle_count==a->cycle_count+1u
            && b->phase==0u && b->remaining==ta_phase_seconds(b->active_plan,0);
    if(b->cycle_count!=a->cycle_count || b->active_plan!=a->active_plan) return 0;
    if(a->remaining>1u)
        return b->phase==a->phase && b->remaining==a->remaining-1u;
    return b->phase==a->phase+1u
        && b->remaining==ta_phase_seconds(a->active_plan,b->phase);
}

static int consume_second(ta_engine_t *s,const ta_snapshot_t *board,
                          const uint32_t *external,int external_mode) {
    uint32_t arrivals[2],direction,active=2u;
    if(s->seconds==UINT32_MAX) {s->error_flags|=TA_ERROR_COUNTER_OVERFLOW;return 0;}
    /* Repeat the rate schedule without rewinding RNG/history or queue state.
     * Host evaluations stop at600s; the board can keep running autonomously. */
    if(external_mode) {
        if(!external) {s->error_flags|=TA_ERROR_INPUT_MISSING;return 0;}
        arrivals[0]=external[0];arrivals[1]=external[1];
        if(arrivals[0]>1u || arrivals[1]>1u) {
            s->error_flags|=TA_ERROR_TELEMETRY;return 0;
        }
    } else {
        if(s->source.second>=TA_SYNTHETIC_SECONDS) s->source.second=0;
        ta_synthetic_next(&s->source,&arrivals[0],&arrivals[1]);
    }
    if(board->phase==0u) active=0u;
    if(board->phase==3u) active=1u;
    for(direction=0;direction<2;direction++) {
        uint32_t tail;
        if(arrivals[direction]>1u) {s->error_flags|=TA_ERROR_TELEMETRY;return 0;}
        if(arrivals[direction] && s->length[direction]>=TA_QUEUE_CAPACITY) {
            s->error_flags|=TA_ERROR_QUEUE_OVERFLOW;return 0;
        }
        if(arrivals[direction]) {
            if(s->arrived==UINT32_MAX) {s->error_flags|=TA_ERROR_COUNTER_OVERFLOW;return 0;}
            tail=(s->head[direction]+s->length[direction])%TA_QUEUE_CAPACITY;
            s->arrival_second[direction][tail]=s->seconds;
            s->length[direction]++;
            s->arrived++;
        }
        if(active==direction && s->length[direction]) {
            s->total_wait_departed_seconds+=s->seconds
                -s->arrival_second[direction][s->head[direction]];
            s->head[direction]=(s->head[direction]+1u)%TA_QUEUE_CAPACITY;
            s->length[direction]--;
            s->departed++;
        }
        s->arrivals_30[direction]-=s->history[s->history_position][direction];
        s->history[s->history_position][direction]=(uint8_t)arrivals[direction];
        s->arrivals_30[direction]+=arrivals[direction];
    }
    s->queue_vehicle_seconds+=s->length[0]+s->length[1];
    s->history_position=(s->history_position+1u)%30u;
    if(s->history_length<30u) s->history_length++;
    s->seconds++;
    return 1;
}

static int engine_poll(ta_engine_t *s,const ta_snapshot_t *board,ta_decision_t *d,
                        const uint32_t *arrivals,int external_mode) {
    uint64_t tick;
    uint32_t best;
    if(s->error_flags) return -1;
    if(!ta_snapshot_tick(board,&tick)) {s->error_flags|=TA_ERROR_TELEMETRY;return -1;}
    if(!s->seen) {s->last=*board;s->last_tick=tick;s->seen=1;return 0;}
    if(tick==s->last_tick) {
        if(board->phase!=s->last.phase || board->remaining!=s->last.remaining
                || board->active_plan!=s->last.active_plan || board->cycle_count!=s->last.cycle_count) {
            s->error_flags|=TA_ERROR_TRANSITION;return -1;
        }
        return 0;
    }
    if(tick!=s->last_tick+1u) {s->error_flags|=TA_ERROR_TICK_GAP;return -1;}
    if(!coherent_transition(&s->last,board)) {s->error_flags|=TA_ERROR_TRANSITION;return -1;}
    s->last=*board;s->last_tick=tick;
    if(!s->synchronized) {
        if(board->phase!=0u || board->remaining!=ta_phase_seconds(board->active_plan,0)) return 0;
        s->synchronized=1;
    }
    if(!consume_second(s,board,arrivals,external_mode)) return -1;
    if(s->history_length<30u || board->phase!=5u || board->remaining!=1u) return 0;
    d->queue_ns=s->length[0]; d->queue_ew=s->length[1];
    d->arrivals_ns_30=s->arrivals_30[0];d->arrivals_ew_30=s->arrivals_30[1];
    d->observed_second=s->seconds-1u;d->expected_cycle=board->cycle_count;
    best=ta_rule_plan(d->queue_ns,d->queue_ew,d->arrivals_ns_30,d->arrivals_ew_30,
                      d->predicted_queue_cost_x30);
    d->plan_id=best;d->flags=0;
    if(s->policy==TA_POLICY_FIXED) d->plan_id=0;
    if(s->policy==TA_POLICY_MODEL) {
        if(!ta_model_in_domain(d->queue_ns,d->queue_ew,d->arrivals_ns_30,d->arrivals_ew_30)) {
            d->flags=TA_DECISION_DOMAIN_FALLBACK;s->fallbacks++;
        } else {
            d->plan_id=ta_model_predict(d->queue_ns,d->queue_ew,d->arrivals_ns_30,d->arrivals_ew_30);
            if(d->plan_id>2u) {d->plan_id=best;d->flags=TA_DECISION_INVALID_MODEL;s->fallbacks++;}
            else {d->flags=TA_DECISION_MODEL;s->model_decisions++;}
        }
    }
    s->decisions++;s->plan_counts[d->plan_id]++;
    return 1;
}

int ta_engine_poll(ta_engine_t *s,const ta_snapshot_t *board,ta_decision_t *d) {
    return engine_poll(s,board,d,0,0);
}
int ta_engine_poll_input(ta_engine_t *s,const ta_snapshot_t *board,
                         ta_decision_t *d,const uint32_t arrivals[2]) {
    return engine_poll(s,board,d,arrivals,1);
}
