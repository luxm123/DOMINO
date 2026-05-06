import time
import threading
import random
from .lambda_client import LambdaClient
from .markov_model import MarkovModel

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
        self.warmup_marker = {'warmup': True}

    def start_keep_alive(self, functions, interval=240):
        self.stop_keep_alive = False
        def ping_loop():
            while not self.stop_keep_alive:
                for f in functions:
                    self.client.invoke(f, payload=self.warmup_marker, async_invoke=True)
                time.sleep(interval)
        self.keep_alive_thread = threading.Thread(target=ping_loop)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

    def stop_keep_alive_service(self):
        self.stop_keep_alive = True

    def execute_dag(self, dag_config, strategy=WarmupStrategy.VANILLA, model_params=None):
        results = {}
        workflow_start = time.time()
        warmup_call_count = 0
        
        # DOMINO Step 1: Offline analysis
        warmup_table = {}
        if strategy == WarmupStrategy.DOMINO:
            model = MarkovModel(dag_config, model_params)
            warmup_table = model.compute_optimal_warmup()

        # Topological execution
        current_nodes = [dag_config['start_node']]
        executed_nodes = set()
        
        while current_nodes:
            next_level = []
            level_threads = []
            level_results = []
            
            # Counter for this level's warmups
            level_warmup_lock = threading.Lock()
            nonlocal_warmup_count = [0] 

            def run_node(node_id):
                # Pre-warmup Logic
                if strategy == WarmupStrategy.ORION:
                    successors = dag_config['nodes'].get(node_id, {}).get('next', [])
                    for succ in successors:
                        self.client.invoke(succ, payload=self.warmup_marker, async_invoke=True)
                        with level_warmup_lock: nonlocal_warmup_count[0] += 1
                
                elif strategy == WarmupStrategy.DOMINO:
                    warmup_info = warmup_table.get(node_id)
                    if warmup_info and warmup_info["timing"] == "on_start":
                        delay = warmup_info.get("delay_ms", 0)
                        
                        def delayed_warmup(funcs, d):
                            if d > 0:
                                time.sleep(d / 1000.0)
                            for succ in funcs:
                                self.client.invoke(succ, payload=self.warmup_marker, async_invoke=True)
                        
                        if delay > 0:
                            threading.Thread(target=delayed_warmup, args=(warmup_info["successors_to_warm"], delay)).start()
                            with level_warmup_lock: nonlocal_warmup_count[0] += len(warmup_info["successors_to_warm"])
                        else:
                            for succ in warmup_info["successors_to_warm"]:
                                self.client.invoke(succ, payload=self.warmup_marker, async_invoke=True)
                                with level_warmup_lock: nonlocal_warmup_count[0] += 1

                # Execute
                step_start = time.time()
                res = self.client.invoke(node_id)
                step_end = time.time()
                res['node'] = node_id
                res['latency_ms'] = (step_end - step_start) * 1000
                level_results.append(res)
                
                # Post-execution warmup
                node_config = dag_config['nodes'].get(node_id, {})
                successors = node_config.get('next', [])
                
                if successors:
                    probs = node_config.get('prob')
                    if probs: # Branch
                        chosen = random.choices(successors, weights=probs, k=1)[0]
                        next_level.append(chosen)
                        if strategy == WarmupStrategy.DOMINO:
                            warmup_info = warmup_table.get(node_id)
                            if warmup_info and warmup_info["timing"] == "on_output":
                                self.client.invoke(chosen, payload=self.warmup_marker, async_invoke=True)
                                with level_warmup_lock: nonlocal_warmup_count[0] += 1
                    else: # Chain or Fanout
                        next_level.extend(successors)

            for node in current_nodes:
                if node in executed_nodes: continue
                t = threading.Thread(target=run_node, args=(node,))
                t.start()
                level_threads.append(t)
                executed_nodes.add(node)
            
            for t in level_threads:
                t.join()
            
            warmup_call_count += nonlocal_warmup_count[0]
            for r in level_results:
                results[r['node']] = r
            current_nodes = list(set(next_level))

        workflow_end = time.time()
        
        return {
            'total_latency_ms': (workflow_end - workflow_start) * 1000,
            'steps': list(results.values()),
            'strategy': strategy,
            'warmup_call_count': warmup_call_count
        }
