import sys
import os
import time
import argparse
import pandas as pd
import threading
import csv
import statistics
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from orchestrator.dag_executor import DAGExecutor, WarmupStrategy
from orchestrator.event_logger import EventLogger
from orchestrator.markov_model import MarkovModel

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
    from orchestrator.lambda_client import LambdaClient
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

class FakeLambdaClient:
    def invoke(self, function_name, payload=None, async_invoke=False):
        if payload is None:
            payload = {}
        is_warmup = bool(payload.get('warmup', False))
        return {
            'status': 'success',
            'function_name': function_name,
            'lambda_duration_ms': 0,
            'is_warmup': is_warmup,
            'was_cold': False,
            'request_id': 'fake'
        }

def _generate_chain_dag(num_nodes):
    nodes = {}
    for i in range(num_nodes):
        node_id = f"n{i}"
        nodes[node_id] = {'next': [f"n{i+1}"]} if i < num_nodes - 1 else {'next': []}
    return {'start_node': 'n0', 'nodes': nodes}

def _generate_fanout_dag(num_nodes):
    if num_nodes < 4:
        return _generate_chain_dag(num_nodes)
    root = "n0"
    join = f"n{num_nodes-1}"
    mids = [f"n{i}" for i in range(1, num_nodes - 1)]
    nodes = {root: {'next': mids}}
    for m in mids:
        nodes[m] = {'next': [join]}
    nodes[join] = {'next': []}
    return {'start_node': root, 'nodes': nodes}

def _generate_branch_dag(num_nodes):
    if num_nodes < 4:
        return {
            'start_node': 'n0',
            'nodes': {
                'n0': {'next': ['n1', 'n2'], 'prob': [0.5, 0.5]},
                'n1': {'next': []},
                'n2': {'next': []}
            }
        }
    root = "n0"
    left = "n1"
    right = "n2"
    join = f"n{num_nodes-1}"
    nodes = {root: {'next': [left, right], 'prob': [0.5, 0.5]}}
    if num_nodes == 4:
        nodes[left] = {'next': [join]}
        nodes[right] = {'next': [join]}
        nodes[join] = {'next': []}
        return {'start_node': root, 'nodes': nodes}

    nodes[left] = {'next': [f"n3"]}
    nodes[right] = {'next': [f"n3"]}
    for i in range(3, num_nodes - 1):
        nodes[f"n{i}"] = {'next': [f"n{i+1}"]}
    nodes[join] = {'next': []}
    return {'start_node': root, 'nodes': nodes}

def _percentile(values, p):
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return float(values_sorted[f])
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return float(d0 + d1)

def _summarize(values):
    return {
        'p50': _percentile(values, 50),
        'p95': _percentile(values, 95),
        'p99': _percentile(values, 99),
        'mean': statistics.mean(values) if values else 0.0
    }

def run_orchestrator_overhead_microbenchmark(iters=5000, output_csv='data/exp3/overhead_microbenchmark.csv'):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    fake_client = FakeLambdaClient()
    executor = DAGExecutor(fake_client)

    workflow_generators = {
        'chain': _generate_chain_dag,
        'fanout': _generate_fanout_dag,
        'branch': _generate_branch_dag
    }

    sizes = [3, 5, 8, 10]
    rows = []

    exp2_e2e_p99_ms = {}
    for wf in ['chain', 'fanout', 'branch']:
        for st in [WarmupStrategy.ORION, WarmupStrategy.DOMINO]:
            p = f"data/exp2/exp2_{wf}_{st}.csv"
            if not os.path.exists(p):
                continue
            try:
                df = pd.read_csv(p)
                if 'total_latency_ms' in df.columns and len(df) > 0:
                    exp2_e2e_p99_ms[(wf, st)] = float(df['total_latency_ms'].quantile(0.99))
            except Exception:
                continue

    for wf_name, gen in workflow_generators.items():
        for n in sizes:
            dag = gen(n)

            t0 = time.time()
            warmup_table = MarkovModel(dag).compute_optimal_warmup()
            offline_ms = (time.time() - t0) * 1000.0

            for strategy in [WarmupStrategy.ORION, WarmupStrategy.DOMINO]:
                first_warmup_offsets = []
                online_total_ms = []

                for _ in range(iters):
                    if strategy == WarmupStrategy.DOMINO:
                        res = executor.execute_dag(dag, strategy=strategy, warmup_table=warmup_table)
                    else:
                        res = executor.execute_dag(dag, strategy=strategy)

                    m = res.get('metrics', {})
                    first_warmup_offsets.append(m.get('first_warmup_offset_ms') or 0.0)
                    online_total_ms.append(res.get('total_latency_ms') or 0.0)

                fw = _summarize(first_warmup_offsets)
                online = _summarize(online_total_ms)
                e2e_p99_ms = exp2_e2e_p99_ms.get((wf_name, strategy), 0.0)
                overhead_pct = (online['p99'] / e2e_p99_ms * 100.0) if e2e_p99_ms else 0.0

                rows.append({
                    'workflow': wf_name,
                    'dag_nodes': n,
                    'strategy': strategy,
                    'offline_analysis_ms': offline_ms if strategy == WarmupStrategy.DOMINO else 0.0,
                    'first_warmup_p50_ms': fw['p50'],
                    'first_warmup_p95_ms': fw['p95'],
                    'first_warmup_p99_ms': fw['p99'],
                    'online_overhead_p50_ms': online['p50'],
                    'online_overhead_p95_ms': online['p95'],
                    'online_overhead_p99_ms': online['p99'],
                    'exp2_e2e_p99_ms': e2e_p99_ms,
                    'overhead_pct_of_exp2_p99': overhead_pct
                })

    with open(output_csv, 'w', newline='') as f:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="exp2", choices=["exp2", "overhead"])
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--workflow", type=str, default="all", choices=["all"] + list(WORKFLOWS.keys()))
    parser.add_argument("--strategy", type=str, default="all", choices=["all", "vanilla", "keep_alive", "orion", "domino"])
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--iters", type=int, default=5000)
    args = parser.parse_args()

    if args.mode == "overhead":
        run_orchestrator_overhead_microbenchmark(iters=args.iters)
        raise SystemExit(0)

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
