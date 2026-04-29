import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.lambda_client import LambdaClient
from orchestrator.event_logger import EventLogger
from experiments.common.utils import load_config

def measure_tau(function_name, max_wait_minutes=60):
    client = LambdaClient()
    logger = EventLogger(output_dir='data/exp1')
    
    print(f"Measuring recycle window (tau) for {function_name}...")
    
    # 1. Trigger a warm instance
    client.invoke(function_name)
    start_time = time.time()
    
    measurements = []
    
    # 2. Ping every 1 minute until cold start occurs
    for m in range(1, max_wait_minutes + 1):
        time.sleep(60)
        res = client.invoke(function_name)
        
        elapsed = (time.time() - start_time) / 60
        duration = res.get('lambda_duration_ms', 0)
        
        measurements.append({
            'minutes_elapsed': elapsed,
            'duration_ms': duration
        })
        
        print(f"  {elapsed:.1f} min: {duration}ms")
        
        # We'd need mu/sigma here to confirm cold start definitively,
        # but a large jump (e.g., > 2x) is usually a good indicator
        # This is a simplified check
        if duration > 1000: # Assuming warm is much less than 1000ms
            print(f"  Detected cold start at {elapsed:.1f} minutes.")
            break
            
    logger.log_calibration(function_name, 'tau', measurements)
    return elapsed

if __name__ == "__main__":
    config = load_config('config/aws_config.yaml')
    func = config.get('functions', ['function_a'])[0]
    measure_tau(func)
