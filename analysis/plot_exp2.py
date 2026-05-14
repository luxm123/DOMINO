import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.stats_utils import calculate_stats, load_exp2_data

def plot_performance_bars(data_dir='data/exp2', output_dir='analysis/output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    workflows = ['chain', 'fanout', 'branch']
    strategies = ['vanilla', 'keep_alive', 'orion', 'domino']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, wf in enumerate(workflows):
        ax = axes[idx]
        ax2 = ax.twinx() # Create a twin axis for warmup counts
        
        x = np.arange(len(strategies))
        width = 0.65
        
        p99s = []
        avg_warmups = []
        
        for strategy in strategies:
            data = load_exp2_data(data_dir, wf, strategy)
            latencies = data['latencies']
            warmups = data['warmup_calls']
            
            stats = calculate_stats(latencies)
            p99s.append(stats['p99'] / 1000.0)
            avg_warmups.append(sum(warmups) / len(warmups) if warmups else 0)
        
        # Plot Latencies (Left Axis)
        bar_colors = ['#BDBDBD', '#66BD63', '#2C7FB8', '#F28E2B']
        ax.bar(x, p99s, width, label='P99 (Latency)', color=bar_colors, alpha=0.9)
        for xi, val in zip(x, p99s):
            ax.text(xi, val + 0.35, f"{val:.2f}", ha='center', va='bottom', fontsize=9)
        
        # Plot Warmups (Right Axis)
        ax2.plot(x, avg_warmups, color='red', marker='D', linestyle='-', linewidth=2, label='Avg Warmups', markersize=8)
        ax2.set_ylabel('Avg Warmup Calls', color='red', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Ensure red line is visible by setting y-axis limits slightly above max
        max_warmup = max(avg_warmups) if avg_warmups else 5
        ax2.set_ylim(0, max_warmup + 1) 
        
        ax.set_title(f'Workflow: {wf.capitalize()}', fontsize=14, fontweight='bold')
        ax.set_ylabel('End-to-End Latency (s)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([s.upper() for s in strategies], rotation=15)
        
        if idx == 0:
            # Combine legends
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines + lines2, labels + labels2, loc='upper right', fontsize=10)
        
        ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/exp2_p99_comparison.png', dpi=300)
    plt.savefig(f'{output_dir}/exp2_p99_comparison.pdf')
    print(f"Plot saved to {output_dir}/exp2_p99_comparison.png")

def plot_orchestrator_overhead(data_csv='data/exp3/overhead_microbenchmark.csv', output_dir='analysis/output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(data_csv):
        raise FileNotFoundError(data_csv)

    df = pd.read_csv(data_csv)
    workflows = ['chain', 'fanout', 'branch']
    strategies = ['orion', 'domino']
    sizes = sorted(df['dag_nodes'].unique().tolist())

    fig, axes = plt.subplots(2, 3, figsize=(18, 8), sharex='col')

    for j, wf in enumerate(workflows):
        ax_top = axes[0][j]
        ax_bot = axes[1][j]

        for st in strategies:
            sub = df[(df['workflow'] == wf) & (df['strategy'] == st)].sort_values('dag_nodes')
            ax_top.plot(sub['dag_nodes'], sub['first_warmup_p99_ms'], marker='o', linewidth=2, label=st.upper())

        sub_domino = df[(df['workflow'] == wf) & (df['strategy'] == 'domino')].sort_values('dag_nodes')
        ax_bot.plot(sub_domino['dag_nodes'], sub_domino['offline_analysis_ms'], marker='o', linewidth=2, color='#F28E2B')

        ax_top.set_title(f'{wf.capitalize()}: First Warmup P99', fontsize=12, fontweight='bold')
        ax_top.set_ylabel('ms')
        ax_top.grid(axis='y', linestyle='--', alpha=0.4)

        ax_bot.set_title(f'{wf.capitalize()}: Offline Analysis', fontsize=12, fontweight='bold')
        ax_bot.set_ylabel('ms')
        ax_bot.set_xlabel('DAG Nodes')
        ax_bot.set_xticks(sizes)
        ax_bot.grid(axis='y', linestyle='--', alpha=0.4)

    axes[0][0].legend(loc='upper left', fontsize=10)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/orchestrator_overhead_microbenchmark.png', dpi=300)
    plt.savefig(f'{output_dir}/orchestrator_overhead_microbenchmark.pdf')
    print(f"Plot saved to {output_dir}/orchestrator_overhead_microbenchmark.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--overhead", action="store_true")
    args = parser.parse_args()

    if args.overhead:
        plot_orchestrator_overhead()
    else:
        plot_performance_bars()
