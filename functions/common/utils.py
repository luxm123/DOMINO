import time
import json
import os

def simulate_work(duration_ms):
    """
    Simulate computation for a given duration in milliseconds.
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < duration_ms:
        # Busy wait to simulate CPU work
        _ = 1 + 1

def get_response(event, context, duration_ms):
    """
    Common response formatter for Lambda functions.
    """
    # Check if it's a warmup call
    is_warmup = event.get('warmup', False)
    
    if not is_warmup:
        simulate_work(duration_ms)
    
    # Return structured data
    return {
        'statusCode': 200,
        'body': json.dumps({
            'function_name': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown'),
            'duration_ms': duration_ms if not is_warmup else 0,
            'is_warmup': is_warmup,
            'memory_limit_mb': context.memory_limit_in_mb,
            'request_id': context.aws_request_id
        })
    }
