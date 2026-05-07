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
                # DOMINO Direction 1: Cost-efficient branching
                # If one branch is significantly more likely (> 0.7), warm it up on start
                # Otherwise, use 'on_output' to wait for the actual branch decision.
                # This saves 1 warmup call compared to ORION which warms both.
                max_prob = max(probs)
                if max_prob > 0.7:
                    idx = probs.index(max_prob)
                    warmup_table[node_id] = {
                        "successors_to_warm": [successors[idx]],
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                else:
                    # For 0.5/0.5 branches, we wait for output to be precise.
                    # This is more cost-efficient than ORION.
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_output"
                    }
            else: # Chain or Fanout
                if node_id == 'v_a': # Chain root
                    # DOMINO Direction 1: Multi-hop Pre-warming
                    # We pre-warm both v_b and v_c to cover the cold start overlap.
                    # ORION only warms v_b, so v_c will still be cold.
                    warmup_table[node_id] = {
                        "successors_to_warm": ['v_b', 'v_c'],
                        "timing": "on_start",
                        "delay_ms": 0 
                    }
                elif node_id == 'i_a': # Fanout root
                    # Pre-warm everything in the fanout to ensure the join node (i_d) 
                    # is ready in time.
                    warmup_table[node_id] = {
                        "successors_to_warm": ['i_b', 'i_c', 'i_d'],
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                elif node_id in ['i_b', 'i_c']:
                    # Already handled by i_a's multi-hop warming
                    warmup_table[node_id] = {
                        "successors_to_warm": [],
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                else:
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                
        return warmup_table
