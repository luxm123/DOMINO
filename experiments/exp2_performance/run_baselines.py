import sys
import os
import time
import argparse
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

def run_experiment_2(count=200, workflows=None, strategies=None, keep_alive_interval=30, keep_alive_bootstrap_sec=12):
    client = LambdaClient()
    executor = DAGExecutor(client)
    logger = EventLogger(output_dir='data/exp2')
    
    if workflows is None:
        workflows = WORKFLOWS

    if strategies is None:
        strategies = [
            WarmupStrategy.VANILLA,
            WarmupStrategy.KEEP_ALIVE,
            WarmupStrategy.ORION,
            WarmupStrategy.DOMINO
        ]
    
    all_funcs = ["v_a", "v_b", "v_c", "i_a", "i_b", "i_c", "i_d", "e_a", "e_b", "e_c", "e_d"]
    
    for wf_name, dag in workflows.items():
        print(f"\n--- Running Workflow: {wf_name} ---")
        
        for strategy in strategies:
            print(f"  Strategy: {strategy}")
            
            # --- Resume Logic: Check if we already have data ---
            csv_path = f"data/exp2/exp2_{wf_name}_{strategy}.csv"
            existing_count = 0
            if os.path.exists(csv_path):
                try:
                    df_existing = pd.read_csv(csv_path)
                    existing_count = len(df_existing)
                except:
                    existing_count = 0
            
            if existing_count >= count:
                print(f"  Already finished {existing_count} runs for {strategy}. Skipping.")
                continue
            elif existing_count > 0:
                print(f"  Resuming {strategy} from {existing_count}/{count}...")

            if strategy == WarmupStrategy.KEEP_ALIVE:
                warm_nodes = list(dag['nodes'].keys())
                for node in warm_nodes:
                    client.invoke(node, payload={'warmup': True}, async_invoke=False)
            
            for i in tqdm(range(existing_count, count)):
                # Force cold start for all functions in the DAG except for Keep-Alive
                if strategy != WarmupStrategy.KEEP_ALIVE:
                    # Get nodes involved in current DAG
                    nodes_to_reset = list(dag['nodes'].keys())
                    
                    # DOMINO Fix: Use serial reset instead of parallel to avoid AWS ResourceConflictException.
                    # AWS Lambda does not allow concurrent UpdateFunctionConfiguration calls on the same account/region easily.
                    for node in nodes_to_reset:
                        success = client.force_cold_start(node)
                        if not success:
                            print(f"  Warning: Failed to reset {node} after retries.")
                    
                    # Give AWS a moment to stabilize after updates
                    # Increased to 30s to ensure the new "cold" fleet is truly ready.
                    time.sleep(30)
                else:
                    warm_nodes = list(dag['nodes'].keys())
                    for node in warm_nodes:
                        client.invoke(node, payload={'warmup': True}, async_invoke=False)

                res = executor.execute_dag(dag, strategy=strategy)
                logger.log_workflow(f"exp2_{wf_name}_{strategy}", res)
                time.sleep(1) # Gap between runs
                
            print(f"  Finished {strategy}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--workflow", type=str, default="all", choices=["all"] + list(WORKFLOWS.keys()))
    parser.add_argument("--strategy", type=str, default="all", choices=["all", "vanilla", "keep_alive", "orion", "domino"])
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    selected_workflows = WORKFLOWS if args.workflow == "all" else {args.workflow: WORKFLOWS[args.workflow]}
    selected_strategies = (
        [WarmupStrategy.VANILLA, WarmupStrategy.KEEP_ALIVE, WarmupStrategy.ORION, WarmupStrategy.DOMINO]
        if args.strategy == "all"
        else [args.strategy]
    )

    if args.fresh:
        for wf in selected_workflows.keys():
            for st in selected_strategies:
                p = f"data/exp2/exp2_{wf}_{st}.csv"
                if os.path.exists(p):
                    os.remove(p)

    run_experiment_2(count=args.count, workflows=selected_workflows, strategies=selected_strategies)
