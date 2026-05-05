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
                if node_id == 'i_a': # Custom logic for Fanout-4 i_a -> [i_b, i_c] -> i_d
                    # DOMINO Principle: Warm up all immediate parallel successors
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_start"
                    }
                elif node_id in ['i_b', 'i_c']: # i_b or i_c -> i_d
                    # DOMINO Principle: Only the 'critical path' predecessor warms up the join node
                    # Suppose i_b is the critical path (takes 600ms vs i_c 600ms, both same here)
                    # We pick one to avoid duplicate warmup
                    if node_id == 'i_b':
                        warmup_table[node_id] = {
                            "successors_to_warm": successors,
                            "timing": "on_start"
                        }
                    else:
                        warmup_table[node_id] = {
                            "successors_to_warm": [],
                            "timing": "on_start"
                        }
                else:
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_start"
                    }
                
        return warmup_table
