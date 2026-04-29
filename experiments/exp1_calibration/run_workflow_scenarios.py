import sys
import os
import time
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.lambda_client import LambdaClient
from orchestrator.workflow_executor import WorkflowExecutor
from orchestrator.event_logger import EventLogger
from experiments.common.utils import load_config, wait_for_recycle

def wait_with_ping(client, minutes, ping_functions):
    """
    Wait for some functions to go cold while keeping others warm.
    """
    print(f"  Waiting for {minutes} minutes (keeping {ping_functions} warm)...")
    for _ in range(minutes):
        for func in ping_functions:
            client.invoke(func, payload={'warmup': True})
        time.sleep(60) # Ping every minute

def run_scenarios(chain, count=20):
    client = LambdaClient()
    executor = WorkflowExecutor(client)
    logger = EventLogger(output_dir='data/exp1')
    
    # Scenario A: All Warm
    print("Running Scenario A: All Warm...")
    for _ in tqdm(range(count)):
        # Ensure warm by pinging
        for f in chain:
            client.invoke(f, payload={'warmup': True})
        res = executor.execute_chain(chain)
        logger.log_workflow('scenario_A', res)
        time.sleep(5) 
        
    # Scenario B: All Cold
    print("Running Scenario B: All Cold...")
    for _ in tqdm(range(count)):
        wait_for_recycle(30)
        res = executor.execute_chain(chain)
        logger.log_workflow('scenario_B', res)
        
    # Scenario C: Only A Cold
    print("Running Scenario C: Only A Cold...")
    for _ in tqdm(range(count)):
        # Keep B and C warm for 30 mins while A goes cold
        wait_with_ping(client, 30, [chain[1], chain[2]])
        
        # Now A should be cold, B and C warm
        res = executor.execute_chain(chain, ping_others=True) 
        logger.log_workflow('scenario_C', res)

    # Scenario D: Only B Cold
    print("Running Scenario D: Only B Cold...")
    for _ in tqdm(range(count)):
        # Keep A and C warm for 30 mins while B goes cold
        wait_with_ping(client, 30, [chain[0], chain[2]])
        
        # Now B should be cold, A and C warm
        res = executor.execute_chain(chain, ping_others=True)
        logger.log_workflow('scenario_D', res)

if __name__ == "__main__":
    config = load_config('config/aws_config.yaml')
    chain = ['function_a', 'function_b', 'function_c']
    run_scenarios(chain)
