import time
import json
import os

# --- ARTIFICIAL COLD START PENALTY ---
# This global variable persists as long as the container is warm.
# If it's True, it means this is a fresh container (Cold Start).
_IS_COLD = True

def simulate_work(duration_ms):
    """
    Simulate computation for a given duration in milliseconds.
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < duration_ms:
        # Busy wait to simulate CPU work
        _ = 1 + 1

def get_response(event, context, duration_ms):
    global _IS_COLD
    is_warmup = event.get('warmup', False)
    
    # Identify if this is a real cold start
    actual_cold = _IS_COLD
    
    # Simulate heavy initialization penalty (e.g., loading a large ML model)
    # only for the very first call to this container.
    if actual_cold:
        # Artificial penalty: 3 seconds
        time.sleep(3)
        _IS_COLD = False
    
    if not is_warmup:
        simulate_work(duration_ms)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'function_name': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown'),
            'duration_ms': duration_ms if not is_warmup else 0,
            'is_warmup': is_warmup,
            'was_cold': actual_cold, # Report back if it was a cold start
            'memory_limit_mb': context.memory_limit_in_mb,
            'request_id': context.aws_request_id
        })
    }
