import sys
import os
import time
import pandas as pd
import threading
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.lambda_client import LambdaClient
from orchestrator.dag_executor import DAGExecutor, WarmupStrategy
from orchestrator.event_logger import EventLogger

# Workflow Definitions
WORKFLOWS = {
    'chain': {
        'start_node': 'v_a',
        'nodes': {
            'v_a': {'next': ['v_b']},
            'v_b': {'next': ['v_c']},
            'v_c': {'next': []}
        }
    },
    'fanout': {
        'start_node': 'i_a',
        'nodes': {
            'i_a': {'next': ['i_b', 'i_c']},
            'i_b': {'next': ['i_d']},
            'i_c': {'next': ['i_d']},
            'i_d': {'next': []}
        }
    },
    'branch': {
        'start_node': 'e_a',
        'nodes': {
            'e_a': {'next': ['e_b', 'e_c'], 'prob': [0.5, 0.5]},
            'e_b': {'next': ['e_d']},
            'e_c': {'next': ['e_d']},
            'e_d': {'next': []}
        }
    }
}

def run_experiment_2(count=200):
    client = LambdaClient()
    executor = DAGExecutor(client)
    logger = EventLogger(output_dir='data/exp2')
    
    strategies = [
        WarmupStrategy.VANILLA,
        WarmupStrategy.KEEP_ALIVE,
        WarmupStrategy.ORION,
        WarmupStrategy.DOMINO
    ]
    
    all_funcs = ["v_a", "v_b", "v_c", "i_a", "i_b", "i_c", "i_d", "e_a", "e_b", "e_c", "e_d"]
    
    for wf_name, dag in WORKFLOWS.items():
        print(f"\n--- Running Workflow: {wf_name} ---")
        
        for strategy in strategies:
            print(f"  Strategy: {strategy}")
            
            if strategy == WarmupStrategy.KEEP_ALIVE:
                executor.start_keep_alive(all_funcs)
            
            for i in tqdm(range(count)):
                # Force cold start for all functions in the DAG except for Keep-Alive
                if strategy != WarmupStrategy.KEEP_ALIVE:
                    # Get nodes involved in current DAG
                    nodes_to_reset = list(dag['nodes'].keys())
                    # Parallel reset to save time
                    threads = []
                    for node in nodes_to_reset:
                        t = threading.Thread(target=client.force_cold_start, args=(node,))
                        t.start()
                        threads.append(t)
                    for t in threads:
                        t.join()

                res = executor.execute_dag(dag, strategy=strategy)
                logger.log_workflow(f"exp2_{wf_name}_{strategy}", res)
                time.sleep(1) # Gap between runs
                
            if strategy == WarmupStrategy.KEEP_ALIVE:
                executor.stop_keep_alive_service()
                
            print(f"  Finished {strategy}")

if __name__ == "__main__":
    # You can reduce count for a quick test
    run_experiment_2(count=200)
