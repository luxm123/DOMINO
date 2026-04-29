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

def run_scenarios(chain, count=200):
    client = LambdaClient()
    executor = WorkflowExecutor(client)
    logger = EventLogger(output_dir='data/exp1')
    
    # Scenario A: All Warm
    print("Running Scenario A: All Warm...")
    for _ in tqdm(range(count)):
        # Ensure warm by pinging
        for f in chain:
            client.invoke(f)
        res = executor.execute_chain(chain)
        logger.log_workflow('scenario_A', res)
        time.sleep(10) # Small gap
        
    # Scenario B: All Cold
    print("Running Scenario B: All Cold...")
    for _ in tqdm(range(count)):
        wait_for_recycle(30)
        res = executor.execute_chain(chain)
        logger.log_workflow('scenario_B', res)
        
    # Scenario C: Only A Cold
    print("Running Scenario C: Only A Cold...")
    for _ in tqdm(range(count)):
        # Pre-warm B and C
        client.invoke(chain[1])
        client.invoke(chain[2])
        
        wait_for_recycle(30) # But wait enough for A to be cold? 
        # Actually, to make ONLY A cold, we need to keep B and C warm while A is cold.
        # This is tricky because wait_for_recycle(30) makes EVERYTHING cold.
        # Better: wait 30 min, then pre-warm B and C, then immediately run chain.
        # But A must be cold. So we wait 30 min, pre-warm B/C, and A is still cold.
        
        client.invoke(chain[1])
        client.invoke(chain[2])
        
        res = executor.execute_chain(chain, ping_others=True) # ping_others keeps B/C warm during A
        logger.log_workflow('scenario_C', res)

    # Scenario D: Only B Cold
    print("Running Scenario D: Only B Cold...")
    for _ in tqdm(range(count)):
        # Pre-warm A and C
        client.invoke(chain[0])
        client.invoke(chain[2])
        
        wait_for_recycle(30)
        
        # Pre-warm A and C
        client.invoke(chain[0])
        client.invoke(chain[2])
        
        res = executor.execute_chain(chain, ping_others=True)
        logger.log_workflow('scenario_D', res)

if __name__ == "__main__":
    config = load_config('config/aws_config.yaml')
    chain = ['function_a', 'function_b', 'function_c']
    run_scenarios(chain)
