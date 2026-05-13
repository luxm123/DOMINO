import time
import json
import os

# --- ARTIFICIAL COLD START PARAMETERS ---
_IS_COLD = True
_LAST_INVOKE_TIME = 0
SIMULATED_TAU_SEC = 60  # 1 minute: more aggressive recycle window to force propagation

def simulate_work(duration_ms):
    """
    Simulate computation for a given duration in milliseconds.
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < duration_ms:
        _ = 1 + 1

def get_response(event, context, duration_ms, init_penalty_ms=5000):
    global _IS_COLD, _LAST_INVOKE_TIME
    
    now = time.time()
    is_warmup = event.get('warmup', False)
    
    # Identify cold start
    idle_time = now - _LAST_INVOKE_TIME if _LAST_INVOKE_TIME > 0 else 0
    should_sim_cold = _IS_COLD or (idle_time > SIMULATED_TAU_SEC)
    
    if should_sim_cold:
        # 1. ALWAYS execute initialization penalty if cold
        time.sleep(init_penalty_ms / 1000.0)
        _IS_COLD = False
    
    _LAST_INVOKE_TIME = time.time()

    # 2. ALWAYS execute simulation work if NOT a warmup request
    # This ensures Cold Latency = Init + Exec
    if not is_warmup:
        simulate_work(duration_ms)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'function_name': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown'),
            'duration_ms': duration_ms if not is_warmup else 0,
            'is_warmup': is_warmup,
            'was_cold': should_sim_cold,
            'request_id': context.aws_request_id
        })
    })
    }
