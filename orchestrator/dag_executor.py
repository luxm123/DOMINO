import time
import threading
import random
from .lambda_client import LambdaClient

class WarmupStrategy:
    VANILLA = "vanilla"
    KEEP_ALIVE = "keep_alive"
    ORION = "orion"
    DOMINO = "domino"

class DAGExecutor:
    def __init__(self, lambda_client):
        self.client = lambda_client
        self.keep_alive_thread = None
        self.stop_keep_alive = False

    def start_keep_alive(self, functions, interval=240):
        """
        Background thread for Keep-Alive baseline.
        """
        self.stop_keep_alive = False
        def ping_loop():
            while not self.stop_keep_alive:
                for f in functions:
                    self.client.invoke(f, payload={'warmup': True}, async_invoke=True)
                time.sleep(interval)
        
        self.keep_alive_thread = threading.Thread(target=ping_loop)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

    def stop_keep_alive_service(self):
        self.stop_keep_alive = True

    def execute_dag(self, dag_config, strategy=WarmupStrategy.VANILLA):
        """
        Execute a DAG based on the specified strategy.
        dag_config: {
            'start_node': 'a',
            'nodes': {
                'a': {'next': ['b', 'c'], 'prob': [0.5, 0.5]},
                'b': {'next': ['d']},
                ...
            }
        }
        """
        results = []
        workflow_start = time.time()
        
        # Start with the initial node
        current_nodes = [dag_config['start_node']]
        executed_nodes = set()
        
        while current_nodes:
            next_level = []
            threads = []
            
            for node in current_nodes:
                if node in executed_nodes: continue
                
                # Warmup logic based on strategy
                if strategy == WarmupStrategy.ORION:
                    # Warm up ALL successors immediately
                    successors = dag_config['nodes'].get(node, {}).get('next', [])
                    for succ in successors:
                        self.client.invoke(succ, payload={'warmup': True}, async_invoke=True)
                
                elif strategy == WarmupStrategy.DOMINO:
                    # Warm up successors based on some probability or look-ahead
                    # Simplified: warm up if prob > threshold or just follow the DAG
                    successors = dag_config['nodes'].get(node, {}).get('next', [])
                    for succ in successors:
                        # In a real DOMINO implementation, this would involve Markov chain logic
                        self.client.invoke(succ, payload={'warmup': True}, async_invoke=True)

                # Execute current node
                step_start = time.time()
                res = self.client.invoke(node)
                step_end = time.time()
                
                res['node'] = node
                res['latency_ms'] = (step_end - step_start) * 1000
                results.append(res)
                executed_nodes.add(node)
                
                # Determine next nodes (handling conditional branches)
                node_config = dag_config['nodes'].get(node, {})
                next_nodes = node_config.get('next', [])
                probs = node_config.get('prob')
                
                if next_nodes:
                    if probs: # Conditional branch
                        chosen = random.choices(next_nodes, weights=probs, k=1)[0]
                        next_level.append(chosen)
                    else: # Parallel fan-out
                        next_level.extend(next_nodes)
            
            current_nodes = list(set(next_level)) # Deduplicate for fan-in

        workflow_end = time.time()
        return {
            'total_latency_ms': (workflow_end - workflow_start) * 1000,
            'steps': results,
            'strategy': strategy
        }
