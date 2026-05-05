import os
import sys
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.stats_utils import calculate_stats, load_exp2_data

def summarize_exp2(data_dir='data/exp2'):
    workflows = ['chain', 'fanout', 'branch']
    strategies = ['vanilla', 'keep_alive', 'orion', 'domino']
    
    print(f"{'Workflow':<10} | {'Strategy':<12} | {'P99 (s)':<8} | {'Avg Warmups':<12}")
    print("-" * 60)
    
    for wf in workflows:
        for strategy in strategies:
            data = load_exp2_data(data_dir, wf, strategy)
            latencies = data['latencies']
            warmups = data['warmup_calls']
            
            if not latencies:
                continue
            stats = calculate_stats(latencies)
            avg_warmups = sum(warmups) / len(warmups)
            print(f"{wf:<10} | {strategy:<12} | {stats['p99']/1000.0:>8.2f} | {avg_warmups:>12.1f}")
        print("-" * 60)

if __name__ == "__main__":
    summarize_exp2()
