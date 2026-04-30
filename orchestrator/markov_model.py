import yaml
import os

class MarkovModel:
    def __init__(self, dag_config, model_params=None):
        self.dag = dag_config
        self.params = model_params or {}

    def compute_optimal_warmup(self):
        """
        Step 1: Offline Analysis
        Analyzes the DAG and produces a warmup decision table.
        """
        warmup_table = {}
        nodes = self.dag.get('nodes', {})
        
        for node_id, config in nodes.items():
            successors = config.get('next', [])
            probs = config.get('prob')
            
            if not successors:
                continue
            
            # Simplified Decision Logic for DOMINO:
            # 1. Chain: Always warm up successor on start.
            # 2. Fanout: Warm up all successors on start (or prioritize critical path).
            # 3. Branch: Warm up high-probability successor on start, 
            #    OR wait for output signal if probabilities are close.
            
            if probs: # Conditional Branch
                # If one branch is significantly more likely (> 0.7), warm it up on start
                # Otherwise, mark as 'on_output' to wait for the actual branch decision
                max_prob = max(probs)
                if max_prob > 0.7:
                    idx = probs.index(max_prob)
                    warmup_table[node_id] = {
                        "successors_to_warm": [successors[idx]],
                        "timing": "on_start"
                    }
                else:
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_output"
                    }
            else: # Chain or Fanout
                # For fanout, we might only warm up the critical path (longest duration)
                # Here we simplify: if it's a chain or small fanout, warm up all.
                # In a real model, we'd use mu_i and delta_i to calculate the critical path.
                warmup_table[node_id] = {
                    "successors_to_warm": successors,
                    "timing": "on_start"
                }
                
        return warmup_table
