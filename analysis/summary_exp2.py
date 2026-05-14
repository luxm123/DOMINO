import os
import sys
import pandas as pd
import numpy as np
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.stats_utils import calculate_stats, load_exp2_data

def summarize_exp2(data_dir='data/exp2', prefix='exp2', include_ablation=False):
    workflows = ['chain', 'fanout', 'branch']
    strategies = ['vanilla', 'keep_alive', 'orion', 'domino']
    if include_ablation:
        strategies.extend(['domino_no_multihop', 'domino_no_branch', 'domino_no_multihop_no_branch'])
    
    print(f"{'Workflow':<10} | {'Strategy':<12} | {'P50 (s)':<8} | {'P95 (s)':<8} | {'P99 (s)':<8} | {'Avg Warmups':<12}")
    print("-" * 92)
    
    for wf in workflows:
        for strategy in strategies:
            data = load_exp2_data(data_dir, wf, strategy, prefix=prefix)
            latencies = data['latencies']
            warmups = data['warmup_calls']
            
            if not latencies:
                continue
            stats = calculate_stats(latencies)
            avg_warmups = sum(warmups) / len(warmups)
            print(
                f"{wf:<10} | {strategy:<12} | "
                f"{stats['p50']/1000.0:>8.2f} | {stats['p95']/1000.0:>8.2f} | {stats['p99']/1000.0:>8.2f} | "
                f"{avg_warmups:>12.1f}"
            )
        print("-" * 92)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data/exp2")
    parser.add_argument("--prefix", type=str, default="exp2")
    parser.add_argument("--include_ablation", action="store_true")
    args = parser.parse_args()

    summarize_exp2(data_dir=args.data_dir, prefix=args.prefix, include_ablation=args.include_ablation)
