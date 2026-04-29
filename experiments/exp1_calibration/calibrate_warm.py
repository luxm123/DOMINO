import sys
import os
import numpy as np
import pandas as pd
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.lambda_client import LambdaClient
from orchestrator.event_logger import EventLogger
from experiments.common.utils import load_config

def calibrate_warm(functions, count=50, warmup_count=10):
    client = LambdaClient()
    logger = EventLogger(output_dir='data/exp1')
    
    results = {}
    
    for func in functions:
        print(f"Calibrating warm duration for {func}...")
        
        # 1. Warm up the instance
        print(f"  Warming up {func} ({warmup_count} times)...")
        for _ in range(warmup_count):
            client.invoke(func)
        
        # 2. Measure warm duration
        print(f"  Measuring {func} ({count} times)...")
        measurements = []
        for i in tqdm(range(count)):
            res = client.invoke(func)
            if res['status'] == 'success':
                measurements.append({
                    'iteration': i,
                    'lambda_duration_ms': res['lambda_duration_ms'],
                    'step_latency_ms': res['duration_ms']
                })
        
        # Save to logger
        logger.log_calibration(func, 'warm', measurements)
        
        # Calculate stats
        durations = [m['lambda_duration_ms'] for m in measurements]
        mu = np.mean(durations)
        sigma = np.std(durations)
        results[func] = {'mu': mu, 'sigma': sigma}
        print(f"  {func}: mu={mu:.2f}ms, sigma={sigma:.2f}ms")
    
    return results

if __name__ == "__main__":
    config = load_config('config/aws_config.yaml')
    functions = config.get('functions', ['function_a', 'function_b', 'function_c'])
    calibrate_warm(functions)
