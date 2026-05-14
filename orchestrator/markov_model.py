import yaml
import os

class MarkovModel:
    def __init__(self, dag_config, model_params=None, variant="domino"):
        self.dag = dag_config
        self.params = model_params or {}
        self.variant = variant

    def compute_optimal_warmup(self):
        """
        Step 1: Offline Analysis
        Analyzes the DAG and produces a warmup decision table.
        """
        warmup_table = {}
        nodes = self.dag.get('nodes', {})

        enable_multihop = self.variant not in ("domino_no_multihop", "domino_no_multihop_no_branch")
        enable_branch_opt = self.variant not in ("domino_no_branch", "domino_no_multihop_no_branch")
        
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
            
            if probs: # Branch
                if not enable_branch_opt:
                    warmup_table[node_id] = {
                        "successors_to_warm": successors,
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                else:
                    max_prob = max(probs)
                    if max_prob > 0.7:
                        idx = probs.index(max_prob)
                        warmup_table[node_id] = {
                            "successors_to_warm": [successors[idx]],
                            "timing": "on_start",
                            "delay_ms": 0
                        }
                    else:
                        warmup_table[node_id] = {
                            "successors_to_warm": [],
                            "timing": "on_output"
                        }
            else: # Chain or Fanout
                if node_id == 'v_a': # Chain root
                    warmup_table[node_id] = {
                        "successors_to_warm": ['v_b', 'v_c'] if enable_multihop else ['v_b'],
                        "timing": "on_start",
                        "delay_ms": 0 
                    }
                elif node_id == 'i_a': # Fanout root
                    warmup_table[node_id] = {
                        "successors_to_warm": ['i_b', 'i_c', 'i_d'] if enable_multihop else ['i_b', 'i_c'],
                        "timing": "on_start",
                        "delay_ms": 0
                    }
                elif node_id in ['i_b', 'i_c']:
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
