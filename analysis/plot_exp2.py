import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.stats_utils import calculate_stats, load_exp2_data

def plot_performance_bars(data_dir='data/exp2', output_dir='analysis/output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    workflows = ['chain', 'fanout', 'branch']
    strategies = ['vanilla', 'keep_alive', 'orion', 'domino']
    colors = ['#cccccc', '#888888', '#444444', '#000000']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, wf in enumerate(workflows):
        ax = axes[idx]
        x = np.arange(len(strategies))
        width = 0.25
        
        p50s, p95s, p99s = [], [], []
        
        for strategy in strategies:
            latencies = load_exp2_data(data_dir, wf, strategy)
            stats = calculate_stats(latencies)
            p50s.append(stats['p50'] / 1000.0) # Convert to seconds
            p95s.append(stats['p95'] / 1000.0)
            p99s.append(stats['p99'] / 1000.0)
        
        ax.bar(x - width, p50s, width, label='P50', color='#A6CEE3')
        ax.bar(x, p95s, width, label='P95', color='#1F78B4')
        ax.bar(x + width, p99s, width, label='P99', color='#B2DF8A')
        
        ax.set_title(f'Workflow: {wf.capitalize()}', fontsize=14)
        ax.set_ylabel('End-to-End Latency (s)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([s.upper() for s in strategies], rotation=15)
        if idx == 0:
            ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/exp2_performance_comparison.png', dpi=300)
    plt.savefig(f'{output_dir}/exp2_performance_comparison.pdf')
    print(f"Plot saved to {output_dir}/exp2_performance_comparison.png")

if __name__ == "__main__":
    plot_performance_bars()
