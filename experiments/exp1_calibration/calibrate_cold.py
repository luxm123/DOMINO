import sys
import os
import numpy as np
import time
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.lambda_client import LambdaClient
from orchestrator.event_logger import EventLogger
from experiments.common.utils import load_config, wait_for_recycle

def calibrate_cold(functions, count=30, recycle_wait=30):
    client = LambdaClient()
    logger = EventLogger(output_dir='data/exp1')
    
    # Load warm params first (need mu and sigma to identify cold start)
    # For simplicity, we'll assume they are calculated or passed
    # In a real run, you'd load from model_params.yaml
    
    for func in functions:
        print(f"Calibrating cold start for {func}...")
        measurements = []
        
        for i in range(count):
            print(f"  Iteration {i+1}/{count} for {func}")
            wait_for_recycle(recycle_wait)
            
            res = client.invoke(func)
            if res['status'] == 'success':
                data = {
                    'iteration': i,
                    'lambda_duration_ms': res['lambda_duration_ms'],
                    'step_latency_ms': res['duration_ms']
                }
                measurements.append(data)
                print(f"    Duration: {res['lambda_duration_ms']}ms")
                
                # Log after each measurement in case of interruption
                logger.log_calibration(func, 'cold', [data])
            else:
                print(f"    Error: {res.get('error_type', 'unknown error')}")
            
    print("Cold start calibration finished.")

if __name__ == "__main__":
    config = load_config('config/aws_config.yaml')
    functions = config.get('functions', ['function_a', 'function_b', 'function_c'])
    # Reduce count for testing or use default 30
    calibrate_cold(functions, count=30)
